---
description: Run the full Project Evident pipeline end-to-end for a client (autonomous, no stopping)
argument-hint: [client-name or "all"]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Run the full pipeline for **$ARGUMENTS** autonomously in the background. No prompting,
no approval gates, no stopping between stages. Runs start to finish. Tim has veto
power after the fact.

**Every stage updates the Status field on the Essentials page in Notion.**

## Status Progression

| Status | Stage | Meaning |
|--------|-------|---------|
| Pulling Transcripts | 1A | Fetching from Notion API |
| Analyzing Calls | 1B | Per-call subagents running |
| Populating Fields | 2 | Mapping evaluations to 50 fields |
| Quality Gate | 2.5 | Checking 7/7 elements. Auto-retry if fail |
| Pushing to Notion | 3 | Writing fields + page body to Essentials page |
| Pushed To Document | Final | Complete. Tim reviews in Notion |
| Revise | Veto | Tim left comments on the Essentials page. Agent reads and fixes |
| Waiting for Review | Post-veto | Revision done, awaiting Tim's check |

## Sequence

1. Read ALL reference files now (background agents cannot access plugin files):
   - `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/org-mapping.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/endpoint-map.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/simon-criteria.md`

2. Resolve client from org-mapping. HALT if IDs are missing.

3. Check current state: read pipeline.log and filesystem to determine where to
   pick up (skip completed stages).

4. **Launch a SINGLE background orchestrator agent that runs everything:**

```
Task(
  subagent_type: "general-purpose",
  description: "Full pipeline: {client}",
  run_in_background: true,
  prompt: "You are the autonomous pipeline orchestrator for Project Evident.
    Run the FULL pipeline for {Client Name} from start to finish.
    Do NOT ask the user anything. Do NOT prompt for confirmation.
    Do NOT stop between stages. Run everything, push to Notion, done.

    Client: {Client Name}
    Client Page ID: {client_page_id}
    Essentials Page ID: {essentials_page_id}
    Folder: ~/Dev/claude-cowork/Clients/Project Evident Updates/{folder_name}/
    Scripts: /tmp/ths-plugins/plugins/project-evident/scripts/
    Current state: {state from step 3}

    CRITICAL: Before EVERY stage, update the Notion status:
    export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
    python3 /tmp/ths-plugins/plugins/project-evident/scripts/update-status.py '{client_short_name}' '<STATUS>'

    ## STAGE 1A: Pull Transcripts
    Skip if 1-transcripts/manifest.json already exists with calls.

    1. Update status: 'Pulling Transcripts'
    2. Run:
       export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
       python3 /tmp/ths-plugins/plugins/project-evident/scripts/pull-transcripts.py '{client_short_name}'
    3. Verify: manifest.json exists and lists calls_to_analyze.

    ## STAGE 1B: Analyze Each Transcript
    Skip if 2-evaluations/ already has files matching manifest count.

    1. Update status: 'Analyzing Calls'
    2. For EACH call in manifest.json, spawn a background subagent:
       - Launch ALL subagents in a SINGLE message (parallel execution)
       - Each uses run_in_background: true
       - Each analyzes ONE transcript and writes ONE evaluation file
       - Embed the endpoint-map and simon-criteria content in each prompt
    3. POLL for completion:
       - Every 30 seconds, count files in 2-evaluations/ matching call-*-evaluation.md
       - When count matches manifest calls_to_analyze count -> done
       - If stuck 5+ minutes with no new files, log PARTIAL and continue with what exists
    4. Log completion to pipeline.log

    ## STAGE 2: Populate Essentials
    Skip if 3-essentials/essentials-review.md already exists.

    1. Update status: 'Populating Fields'
    2. Run directly in this context (no subagent):
       - Read all evaluation files from 2-evaluations/
       - Map content to 50 fields using the endpoint map
       - Build L/M/H value proxy tables where projected data exists
       - Write 3-essentials/essentials-review.md
    3. Log to pipeline.log

    ## STAGE 2.5: Quality Gate
    1. Update status: 'Quality Gate'
    2. Run the Essential Elements quality gate (7 elements from simon-criteria)
    3. If 7/7 pass -> proceed to Stage 3
    4. If <7/7 -> identify which elements failed and which evaluation files
       might fill the gaps. Re-read those evaluations, update the fields,
       rewrite essentials-review.md, and re-run the gate. Max 2 retries.
    5. If still <7/7 after retries -> proceed anyway but flag gaps in pipeline.log.
       Tim can address via veto later.

    ## STAGE 3: Push to Notion
    1. Update status: 'Pushing to Notion'
    2. Push all 50 endpoint fields to the Essentials page:
       export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
       python3 /tmp/ths-plugins/plugins/project-evident/scripts/push-essentials.py '{client_short_name}'
    3. Verify push succeeded (check exit code)
    4. Log to pipeline.log

    ## STAGE FINAL: Mark Complete
    1. Update status: 'Pushed To Document'
    2. Log final entry to pipeline.log:
       [{timestamp}] [v1.1.0] [pipeline:complete] [{client}]
         Status: PUSHED_TO_DOCUMENT
         Quality gate: {N}/7
         Fields pushed: {count}
         Essentials page: {essentials_page_id}

    Return: summary of all stages, quality gate results, any gaps flagged.

    ## Reference: Org Mapping
    {org_mapping content}

    ## Reference: Endpoint Map
    {endpoint_map content}

    ## Reference: Simon Criteria
    {simon_criteria content}"
)
```

5. **Tell the user immediately:**
   "Pipeline launched for {client} in background. It will run 1A -> 1B -> 2 -> push
   autonomously. Watch the Status field on the Essentials page in Notion for live progress.

   Check pipeline.log for details.
   To request changes: add comments on the Essentials page in Notion, then
   `/evaluate-session revise {client}` -- the agent reads your comments and fixes."

6. **If $ARGUMENTS is "all":**
   Launch one orchestrator per client, ALL in a single message (parallel).
   Each runs independently. Report: "{N} pipeline agents launched.
   Watch the Status column in the Essentials database for live progress."

**This command never asks questions. It never stops. It runs to Pushed To Document
or halts on error. Tim vetoes after the fact if needed.**
