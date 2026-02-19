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
| Pushed To Document | 3-done | Essentials pushed. Moving to Simon Summary |
| Writing Summary | 4 | Generating funder-ready summary for Client page |
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
    Scripts: ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/
    Skills: ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/
    Current state: {state from step 3}

    CRITICAL -- NOTION TOKEN: Export ONCE at the very start of the pipeline.
    All subsequent script calls inherit this env var. Do NOT call op again.
    export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)

    CRITICAL -- STATUS UPDATES: Before EVERY stage, update the Notion status:
    python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/update-status.py '{client_short_name}' '<STATUS>'

    CRITICAL -- SKILL FILES: Before EVERY stage, Read the skill's SKILL.md file
    from disk and follow its instructions EXACTLY. The skill files contain all
    the rules, framing guidance, examples, and quality constraints for that stage.
    Do NOT paraphrase or summarize skill instructions from memory. Read the file,
    then execute. The skill file is the authority.

    Skill file locations:
    - Stage 1: ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/SKILL.md
    - Stage 2: ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/essentials-populator/SKILL.md
    - Stage 4: ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/simon-summary/SKILL.md

    Reference file locations (read these at pipeline start, re-read before any
    stage if your context has grown large):
    - ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/references/org-mapping.md
    - ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/references/endpoint-map.md
    - ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/references/simon-criteria.md

    ## STAGE 1A: Pull Transcripts
    Skip if 1-transcripts/manifest.json already exists with calls.

    1. Update status: 'Pulling Transcripts'
    2. Run:
       python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/pull-transcripts.py '{client_short_name}'
    3. Verify: manifest.json exists and lists calls_to_analyze.

    ## STAGE 1B: Analyze Each Transcript
    Skip if 2-evaluations/ already has files matching manifest count.

    1. Update status: 'Analyzing Calls'
    2. Read the coaching-call-analyzer SKILL.md from disk NOW.
    3. Re-read endpoint-map and simon-criteria reference files from disk NOW
       (context compression may have dropped them since pipeline start).
    4. For EACH call in manifest.json, spawn a background subagent:
       - Launch ALL subagents in a SINGLE message (parallel execution)
       - Each uses run_in_background: true
       - Each analyzes ONE transcript and writes ONE evaluation file
       - EMBED the FULL SKILL.md content (everything from 'PHASE B: Parallel
         Analysis' onward) in each subagent's prompt. Also embed the endpoint-map
         and simon-criteria reference file content. Subagents cannot read plugin
         files -- they need the content in their prompt.
    4. POLL for completion:
       - Every 30 seconds, count files in 2-evaluations/ matching call-*-evaluation.md
       - When count matches manifest calls_to_analyze count -> done
       - If stuck 5+ minutes with no new files, log PARTIAL and continue with what exists
    5. Log completion to pipeline.log

    ## STAGE 2: Populate Essentials
    Skip if 3-essentials/essentials-review.md already exists.

    1. Update status: 'Populating Fields'
    2. Read the essentials-populator SKILL.md from disk NOW.
    3. Read the endpoint-map reference file from disk NOW (re-read even if you
       read it earlier -- context compression may have dropped it).
    4. Follow the SKILL.md instructions EXACTLY to:
       - Read all evaluation files from 2-evaluations/
       - Map content to 50 fields using the endpoint map
       - Apply ALL framing rules from the skill (staff transitions, tool-constraint
         fit, no editorializing, blank fields stay blank, right-sizing context)
       - Build L/M/H value proxy tables where projected data exists
       - Write 3-essentials/essentials-review.md in the format shown in the skill
    5. Log to pipeline.log

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
       python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/push-essentials.py '{client_short_name}'
    3. Verify push succeeded (check exit code)
    4. Log to pipeline.log

    ## STAGE FINAL: Mark Essentials Complete
    1. Update status: 'Pushed To Document'
    2. Log to pipeline.log:
       [{timestamp}] [v2.1.0] [pipeline:essentials-complete] [{client}]
         Status: PUSHED_TO_DOCUMENT
         Quality gate: {N}/7
         Fields pushed: {count}
         Essentials page: {essentials_page_id}

    ## STAGE 4: Simon Summary
    Write the funder-ready summary sentence to the Client page.
    Skip if 4-summary/simon-summary.md already exists.

    1. Update status: 'Writing Summary'
    2. Read the simon-summary SKILL.md from disk NOW.
    3. Follow the SKILL.md instructions EXACTLY -- especially:
       - No dollar amounts
       - Count workflows, not attendees
       - Titles, not names
       - Step count reduction + time reduction + volume pattern
       - Lead with people, then tools, then workflow change, then impact
       - Test: could Simon paste this into a funder report with zero edits?
    4. Read 3-essentials/essentials-review.md
    5. Write to {ARTIFACT_ROOT}/{folder_name}/4-summary/simon-summary.md
    6. Push the summary to the 'Simon Summary' rich_text property on the Client page
       (client_page_id, NOT essentials_page_id).
       NOTION_API_KEY is already exported from pipeline start -- do NOT call op again.
       Use Notion API PATCH to /pages/{client_page_id} with:
       {'properties': {'Simon Summary': {'rich_text': [{'text': {'content': '{summary}'}}]}}}
       If summary exceeds 2000 chars, split into multiple rich_text array elements
       at sentence boundaries.
    7. Log to pipeline.log:
       [{timestamp}] [v2.1.0] [stage-4:simon-summary] [{client}]
         Status: SUCCESS
         Output: 4-summary/simon-summary.md
         Target: Client page {client_page_id} -> 'Simon Summary' property
         Characteristics: {N}/6 present
         Length: {char count}

    Return: summary of all stages, quality gate results, simon summary preview.

    ## Reference: Org Mapping
    {org_mapping content}

    ## Reference: Endpoint Map
    {endpoint_map content}

    ## Reference: Simon Criteria
    {simon_criteria content}"
)
```

5. **Tell the user immediately:**
   "Pipeline launched for {client} in background. It will run 1A -> 1B -> 2 -> push -> simon summary
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
