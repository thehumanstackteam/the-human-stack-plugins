---
description: Run the full Project Evident pipeline end-to-end for a client (autonomous, no stopping)
argument-hint: [client-name or "all"]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task, TaskOutput
---

Run the full pipeline for **$ARGUMENTS** autonomously. No prompting,
no approval gates, no stopping between stages. Tim has veto power after the fact.

**Architecture (v3.0.0):** Thin dispatcher. The main conversation reads reference files,
dispatches Stage 1 as a background agent, and returns immediately. Each stage auto-chains
to the next via pipeline continuation -- the orchestrator does NOT hold context for
the full run. Background agents run Bash (python scripts, curl) autonomously.

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

2. Also read skill files (needed for embedding in background agent prompts):
   - `{REPO}/skills/coaching-call-analyzer/SKILL.md`
   - `{REPO}/skills/essentials-populator/SKILL.md`
   - `{REPO}/skills/simon-summary/SKILL.md`

3. Resolve client from org-mapping. HALT if IDs are missing.
   Extract: `client_page_id`, `essentials_page_id`, `folder_name`, `short_name`.

4. Set working directory: `{ARTIFACT_ROOT}/{folder_name}/`

5. Create folder structure:
   ```bash
   mkdir -p "{ARTIFACT_ROOT}/{folder_name}/1-transcripts"
   mkdir -p "{ARTIFACT_ROOT}/{folder_name}/2-evaluations"
   mkdir -p "{ARTIFACT_ROOT}/{folder_name}/3-essentials"
   mkdir -p "{ARTIFACT_ROOT}/{folder_name}/4-summary"
   ```

6. Export Notion token:
   ```bash
   export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
   ```

7. Check current state: read pipeline.log and filesystem to determine where to
   pick up (skip completed stages). If a stage is already complete, dispatch
   from the next incomplete stage instead.

### Dispatch: Launch from the right stage

Based on pipeline state, dispatch the appropriate stage as a background agent.
Each stage includes pipeline continuation instructions that auto-chain to the next.

**If starting from Stage 1 (no manifest or evaluations):**

1. Update status:
   ```bash
   python3 {REPO}/scripts/update-status.py '{short_name}' 'Pulling Transcripts'
   ```

2. Launch ONE background agent that handles the full Stage 1 -> 2 -> 3 -> 4 chain:

```
Task(
  subagent_type: "general-purpose",
  description: "Pipeline: {client} (Stage 1 -> 4)",
  run_in_background: true,
  prompt: "You are the autonomous pipeline runner for Project Evident.
    You run the FULL pipeline from Stage 1 through Stage 4 without stopping.
    Never ask questions. Never wait for approval. Run to completion or halt on error.

    ## Client Context
    Client: {short_name}
    Client Page ID: {client_page_id}
    Essentials Page ID: {essentials_page_id}
    Folder: {ARTIFACT_ROOT}/{folder_name}/

    ## Notion API Access
    Export before any API/script calls:
      export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)

    ## Stage 1A: Pull Transcripts
    Follow the coaching-call-analyzer SKILL.md Phase A steps (A0-A6):
    - Retrieve coaching calls from Notion for this client
    - Filter out cancellations and non-sessions
    - Write raw transcripts and manifest to disk

    ## Stage 1B: Analyze Each Transcript
    - Update status: python3 {REPO}/scripts/update-status.py '{short_name}' 'Analyzing Calls'
    - Launch N parallel background agents -- one per call -- ALL in a SINGLE message
    - Each agent gets run_in_background: true
    - Embed endpoint-map and simon-criteria in each agent's prompt
    - Poll for completion: count evaluation files every 30 seconds
    - When all evaluations exist (or 10 min timeout), proceed

    ## Stage 2: Populate Essentials
    - Update status: python3 {REPO}/scripts/update-status.py '{short_name}' 'Populating Fields'
    - Follow the essentials-populator SKILL.md
    - Write essentials-review.md and essentials-payload.json
    - Run quality gate. Retry up to 2 times if <7/7.
    - Update status: python3 {REPO}/scripts/update-status.py '{short_name}' 'Quality Gate'

    ## Stage 3: Push to Notion
    - Update status: python3 {REPO}/scripts/update-status.py '{short_name}' 'Pushing to Notion'
    - Run: python3 {REPO}/scripts/push-essentials.py '{short_name}'
    - Verify exit code
    - Update status: python3 {REPO}/scripts/update-status.py '{short_name}' 'Pushed To Document'
    - Log to pipeline.log

    ## Stage 4: Simon Summary
    - Update status: python3 {REPO}/scripts/update-status.py '{short_name}' 'Writing Summary'
    - Follow the simon-summary SKILL.md
    - Write 4-summary/simon-summary.md
    - Push to 'Simon Summary' property on Client page via Notion API
    - Log to pipeline.log

    ## Error Handling
    - If any Bash script fails, log the error to pipeline.log and HALT
    - If Phase B agents produce no output after 10 minutes, log TIMEOUT and continue
    - If quality gate fails after retries, proceed but flag in log

    ## Coaching Call Analyzer SKILL.md
    {paste full coaching-call-analyzer SKILL.md content here}

    ## Essentials Populator SKILL.md
    {paste full essentials-populator SKILL.md content here}

    ## Simon Summary SKILL.md
    {paste full simon-summary SKILL.md content here}

    ## Reference: Org Mapping
    {paste full org-mapping.md content here}

    ## Reference: Endpoint Map
    {paste full endpoint-map.md content here}

    ## Reference: Simon Criteria
    {paste full simon-criteria.md content here}"
)
```

**If resuming from Stage 2 (evaluations exist, no essentials-review.md):**
Dispatch from Stage 2 onward using the same pattern but skip Stage 1.

**If resuming from Stage 3 (essentials-review.md exists, not pushed):**
Run push-essentials.py directly, then dispatch Stage 4.

**If resuming from Stage 4 (pushed, no simon-summary.md):**
Dispatch Stage 4 only.

3. **Tell the user the pipeline is running:**
   - Report which client and which starting stage
   - Explain: "Pipeline is running autonomously in the background. All stages will auto-chain."
   - Instruct: "Check progress with `/evaluate-session status {client}` or read `pipeline.log`."
   - Do NOT block waiting for results

## If $ARGUMENTS is "all"

Run the full sequence above for EACH client sequentially (not parallel --
each client pipeline uses significant context). Report progress per client.

For each client:
1. Check pipeline state
2. Dispatch from the appropriate stage
3. Wait for the background agent to complete (poll pipeline.log for the
   stage-4:simon-summary SUCCESS entry, or timeout after 30 minutes)
4. Move to the next client

## Error Handling

- If any Bash script fails, log the error and HALT. Do not continue to the next stage.
- If a background agent produces no output after 10 minutes, log TIMEOUT and continue
  with whatever partial results exist.
- If the quality gate fails after retries, proceed but flag it clearly in the log.

**This command never asks questions. It never stops. It runs to completion
or halts on error. Tim vetoes after the fact if needed.**
