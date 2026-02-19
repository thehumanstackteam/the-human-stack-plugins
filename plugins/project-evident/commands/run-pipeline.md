---
description: Run the full Project Evident pipeline end-to-end for a client (autonomous, no stopping)
argument-hint: [client-name or "all"]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task, TaskOutput
---

Run the full pipeline for **$ARGUMENTS** autonomously. No prompting,
no approval gates, no stopping between stages. Tim has veto power after the fact.

**Architecture:** Main conversation orchestrates and runs all Bash. Background
agents handle AI-heavy analysis with fresh context windows. Each agent reads
skill files and reference files from disk -- nothing is embedded in prompts.

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

## Constants

```
REPO = ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident
ARTIFACT_ROOT = ~/Dev/claude-cowork/Clients/Project Evident Updates
```

## Sequence

### Step 0: Setup

1. Read reference files from the repo (use absolute paths):
   - `{REPO}/skills/coaching-call-analyzer/references/org-mapping.md`
   - `{REPO}/skills/coaching-call-analyzer/references/endpoint-map.md`
   - `{REPO}/skills/coaching-call-analyzer/references/simon-criteria.md`

2. Resolve client from org-mapping. HALT if IDs are missing.
   Extract: `client_page_id`, `essentials_page_id`, `folder_name`, `short_name`.

3. Set working directory: `{ARTIFACT_ROOT}/{folder_name}/`

4. Export Notion token ONCE (all subsequent Bash calls inherit it):
   ```bash
   export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
   ```

5. Check current state: read pipeline.log and filesystem to determine where to
   pick up (skip completed stages).

### Stage 1A: Pull Transcripts

Skip if `1-transcripts/manifest.json` already exists with calls.

1. Update status:
   ```bash
   python3 {REPO}/scripts/update-status.py '{short_name}' 'Pulling Transcripts'
   ```

2. Run directly in main conversation:
   ```bash
   python3 {REPO}/scripts/pull-transcripts.py '{short_name}'
   ```

3. Verify: manifest.json exists and lists `calls_to_analyze`.

### Stage 1B: Analyze Each Transcript

Skip if `2-evaluations/` already has files matching manifest count.

1. Update status:
   ```bash
   python3 {REPO}/scripts/update-status.py '{short_name}' 'Analyzing Calls'
   ```

2. Read `manifest.json` to get the list of calls and their transcript file paths.

3. Launch N parallel background agents -- one per call -- ALL in a SINGLE message.
   Each agent gets a short prompt that tells it to read everything from disk:

   ```
   Task(
     subagent_type: "general-purpose",
     description: "Analyze call {N}: {client}",
     run_in_background: true,
     prompt: "You are a coaching call analyzer for Project Evident.

       Read your instructions:
         ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/SKILL.md
       Follow ONLY the 'PHASE B: Parallel Analysis' section onward.

       Read these reference files:
         ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/references/endpoint-map.md
         ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/references/simon-criteria.md

       Analyze this transcript:
         {working_dir}/1-transcripts/call-{N}-transcript.md

       Write your evaluation to:
         {working_dir}/2-evaluations/call-{N}-evaluation.md

       Client: {short_name}
       Session number: {N}
       Client page ID: {client_page_id}
       Essentials page ID: {essentials_page_id}

       Follow the SKILL.md instructions EXACTLY. Read the files from disk,
       do not ask for any input. Write the evaluation file and finish."
   )
   ```

4. **Poll for completion:**
   - Every 30 seconds, count files in `2-evaluations/` matching `call-*-evaluation.md`
   - When count matches manifest `calls_to_analyze` count -> done
   - If stuck 5+ minutes with no new files, log PARTIAL and continue with what exists

5. Log completion to pipeline.log.

### Stage 2 + 2.5: Populate Essentials and Quality Gate

Skip if `3-essentials/essentials-review.md` already exists.

1. Update status:
   ```bash
   python3 {REPO}/scripts/update-status.py '{short_name}' 'Populating Fields'
   ```

2. Launch ONE background agent:

   ```
   Task(
     subagent_type: "general-purpose",
     description: "Populate essentials: {client}",
     run_in_background: true,
     prompt: "You are the essentials populator for Project Evident.

       Read your instructions:
         ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/essentials-populator/SKILL.md

       Read these reference files:
         ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/references/endpoint-map.md
         ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/references/simon-criteria.md

       Read ALL evaluation files in:
         {working_dir}/2-evaluations/

       Client: {short_name}
       Client page ID: {client_page_id}
       Essentials page ID: {essentials_page_id}
       Working directory: {working_dir}

       Produce TWO output files:
       1. {working_dir}/3-essentials/essentials-review.md
          (human-readable review per SKILL.md format)
       2. {working_dir}/3-essentials/essentials-payload.json
          (machine-readable for push script -- see SKILL.md for format)

       Run the quality gate (7 Essential Elements from simon-criteria).
       If <7/7 pass, identify gaps and retry up to 2 times.
       If still <7/7 after retries, proceed but note gaps in the review file.

       Follow the SKILL.md instructions EXACTLY. Read all files from disk,
       do not ask for any input. Write both output files and finish."
   )
   ```

3. Poll: check for existence of `3-essentials/essentials-review.md` every 30 seconds.

4. When complete, update status:
   ```bash
   python3 {REPO}/scripts/update-status.py '{short_name}' 'Quality Gate'
   ```

### Stage 3: Push to Notion

1. Update status:
   ```bash
   python3 {REPO}/scripts/update-status.py '{short_name}' 'Pushing to Notion'
   ```

2. Run directly in main conversation:
   ```bash
   python3 {REPO}/scripts/push-essentials.py '{short_name}'
   ```

3. Verify push succeeded (check exit code).

4. Update status:
   ```bash
   python3 {REPO}/scripts/update-status.py '{short_name}' 'Pushed To Document'
   ```

5. Log to pipeline.log:
   ```
   [{timestamp}] [v2.2.0] [pipeline:essentials-complete] [{client}]
     Status: PUSHED_TO_DOCUMENT
     Quality gate: {N}/7
     Fields pushed: {count}
     Essentials page: {essentials_page_id}
   ```

### Stage 4: Simon Summary

Skip if `4-summary/simon-summary.md` already exists.

1. Update status:
   ```bash
   python3 {REPO}/scripts/update-status.py '{short_name}' 'Writing Summary'
   ```

2. Launch ONE background agent:

   ```
   Task(
     subagent_type: "general-purpose",
     description: "Simon summary: {client}",
     run_in_background: true,
     prompt: "You are the Simon Summary writer for Project Evident.

       Read your instructions:
         ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/simon-summary/SKILL.md

       Read the essentials review:
         {working_dir}/3-essentials/essentials-review.md

       Read reference:
         ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/coaching-call-analyzer/references/simon-criteria.md

       Client: {short_name}
       Client page ID: {client_page_id}
       Working directory: {working_dir}

       Write to: {working_dir}/4-summary/simon-summary.md

       After writing the summary, push it to Notion:
       - Target: Client page {client_page_id} (NOT essentials page)
       - Property: 'Simon Summary' (rich_text)
       - NOTION_API_KEY is already in the environment -- use curl directly
       - If summary exceeds 2000 chars, split into multiple rich_text elements
         at sentence boundaries

       Follow the SKILL.md instructions EXACTLY. Read all files from disk,
       do not ask for any input. Write the file, push to Notion, and finish."
   )
   ```

3. Poll: check for existence of `4-summary/simon-summary.md` every 30 seconds.

4. Log to pipeline.log:
   ```
   [{timestamp}] [v2.2.0] [stage-4:simon-summary] [{client}]
     Status: SUCCESS
     Output: 4-summary/simon-summary.md
     Target: Client page {client_page_id} -> 'Simon Summary' property
   ```

### Completion

Tell the user:
"Pipeline complete for {client}.
- Essentials pushed to Notion
- Simon Summary written to Client page
- Check pipeline.log for details

To request changes: add comments on the Essentials page in Notion, then
`/evaluate-session revise {client}` -- the agent reads your comments and fixes."

## If $ARGUMENTS is "all"

Run the full sequence above for EACH client sequentially (not parallel --
each client pipeline uses significant context). Report progress per client.

## Error Handling

- If any Bash script fails, log the error and HALT. Do not continue to the next stage.
- If a background agent produces no output after 10 minutes, log TIMEOUT and continue
  with whatever partial results exist.
- If the quality gate fails after retries, proceed but flag it clearly in the log.

**This command never asks questions. It never stops. It runs to completion
or halts on error. Tim vetoes after the fact if needed.**
