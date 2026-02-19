---
description: Run the full Project Evident pipeline end-to-end for a client (autonomous, no prompting)
argument-hint: [client-name or "all"]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Run the full pipeline for **$ARGUMENTS** autonomously in the background. No prompting,
no asking permission, no stopping between stages. The only stop is the HITL gate
after Stage 2.

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
    Run the FULL pipeline for {Client Name} without stopping or asking questions.
    Do NOT ask the user anything. Do NOT prompt for confirmation between stages.
    Run each stage, verify output, advance to the next.

    Client: {Client Name}
    Client Page ID: {client_page_id}
    Essentials Page ID: {essentials_page_id}
    Folder: ~/Dev/claude-cowork/Clients/Project Evident Updates/{folder_name}/
    Current state: {state from step 3}

    ## STAGE 1A: Pull Transcripts
    Skip if 1-transcripts/manifest.json already exists with calls.

    Run this command:
    export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
    python3 /tmp/ths-plugins/plugins/project-evident/scripts/pull-transcripts.py '{client_short_name}'

    Verify: manifest.json exists and lists calls_to_analyze.

    ## STAGE 1B: Analyze Each Transcript
    Skip if 2-evaluations/ already has files matching manifest count.

    For EACH call in manifest.json, spawn a background subagent:
    - Launch ALL subagents in a SINGLE message (parallel execution)
    - Each uses run_in_background: true
    - Each analyzes ONE transcript and writes ONE evaluation file
    - Embed the endpoint-map and simon-criteria content in each prompt

    Then POLL for completion:
    - Every 30 seconds, count files in 2-evaluations/ matching call-*-evaluation.md
    - When count matches manifest calls_to_analyze count -> Stage 1B complete
    - If stuck for 5+ minutes with no new files, log PARTIAL and continue with what exists
    - Log completion to pipeline.log

    ## STAGE 2: Populate Essentials
    Skip if 3-essentials/essentials-review.md already exists.

    Do NOT spawn another subagent for this. Run it directly in this context:
    - Read all evaluation files from 2-evaluations/
    - Map content to 50 fields using the endpoint map
    - Build L/M/H value proxy tables where projected data exists
    - Run the Essential Elements quality gate
    - Write 3-essentials/essentials-review.md
    - Log to pipeline.log

    ## STOP: HITL Gate
    After writing essentials-review.md, STOP. Do NOT push to Notion.
    Log:
    [{timestamp}] [v1.1.0] [pipeline:orchestrator] [{client}]
      Status: WAITING_FOR_HITL
      Review file: 3-essentials/essentials-review.md
      Quality gate: {N}/7
      Next: Tim reviews, then /evaluate-session push {client}

    Return a summary: stages completed, quality gate results, file path.

    ## Reference: Org Mapping
    {org_mapping content}

    ## Reference: Endpoint Map
    {endpoint_map content}

    ## Reference: Simon Criteria
    {simon_criteria content}"
)
```

5. **Tell the user immediately:**
   "Pipeline launched for {client} in background. It will run Stage 1A -> 1B -> 2
   autonomously and stop at the HITL gate.

   Check progress: read `{folder}/pipeline.log`
   When ready: `/evaluate-session push {client}`"

6. **If $ARGUMENTS is "all":**
   Launch one orchestrator per client, ALL in a single message (parallel).
   Each runs independently. Report: "{N} pipeline agents launched."

**This command never asks questions. It never stops between stages. It runs until
the HITL gate or until an error forces a halt.**
