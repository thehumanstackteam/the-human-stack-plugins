---
name: coaching-evaluator
description: >
  Status checker and revision handler for Project Evident coaching work.
  Use for "status on [client]", "revise [client]", or "push [client]".
  For full pipeline runs, use /run-pipeline instead -- this skill does NOT
  run the pipeline.
---

# Coaching Evaluator (Status & Revise)

Lightweight utility for checking pipeline state and handling revisions.

**For full pipeline runs: use `/run-pipeline {client}` or `/run-pipeline all`.**
This skill does NOT run the pipeline. It checks status and processes revisions.

**Plugin version: 2.0.0**

## Routing Logic

| Request Pattern | Route |
|----------------|-------|
| "process [client]" / "run pipeline" / "full run" / "resume [client]" | **REDIRECT:** Tell the user to run `/run-pipeline {client}` |
| "analyze call" / "run stage 1" | **REDIRECT:** Tell the user to run `/run-pipeline {client}` |
| "populate essentials" / "run stage 2" | **REDIRECT:** Tell the user to run `/run-pipeline {client}` |
| "status on [client]" / "where is [client]" / "check [client]" | **Status check**: read log + filesystem, report state |
| "revise [client]" | **Revise**: read Notion comments, apply fixes, re-push |
| "push [client]" / "push to notion" | **Manual push**: run push-essentials.py |
| "batch" / "all clients" | **REDIRECT:** Tell the user to run `/run-pipeline all` |

**When ambiguous, default to status check.**

## Prerequisites

- Read `references/org-mapping.md` for client IDs and folder names

## Constants

```
ARTIFACT_ROOT = ~/Dev/claude-cowork/Clients/Project Evident Updates
SCRIPTS = ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/
```

## Route: Status Check

1. Match client name to org-mapping.md. Extract folder_name.
2. Set working directory: `{ARTIFACT_ROOT}/{folder_name}/`
3. Read pipeline state from both log AND filesystem:

   ```
   Check: Does pipeline.log exist?
   Check: Does 1-transcripts/manifest.json exist?
   Check: How many transcript files in 1-transcripts/?
   Check: How many evaluation files in 2-evaluations/?
   Check: Does manifest call count match evaluation file count?
   Check: Does 3-essentials/essentials-review.md exist?
   Check: Does 3-essentials/essentials-payload.json exist?
   Check: Does 4-summary/simon-summary.md exist?
   Check: Any FAILED entries in pipeline.log?
   Check: Most recent log entry?
   ```

4. Determine current state:

   | State | Condition | Report |
   |-------|-----------|--------|
   | NOT_STARTED | No log, no files | "Not started. Run `/run-pipeline {client}`" |
   | EXTRACTING | Manifest missing, log shows Pulling Transcripts | "Stage 1A in progress" |
   | ANALYZING | Evaluations < manifest count | "Stage 1B: {N} of {M} calls analyzed" |
   | STAGE_1_DONE | All evaluations match manifest | "Stage 1 complete. Run `/run-pipeline {client}` to continue" |
   | POPULATING | essentials-review.md missing, log shows Populating Fields | "Stage 2 in progress" |
   | STAGE_2_DONE | essentials-review.md exists | "Stage 2 complete" |
   | PUSHED | Log shows PUSHED_TO_NOTION | "Pushed to Notion" |
   | FAILED | FAILED entry in log | Show error, suggest fix |

5. Report:
   ```
   # {Client Name} -- Pipeline Status

   State: {current state}
   Last activity: {most recent log entry timestamp}

   Stage 1A (Extract): {# calls found, # filtered}
   Stage 1B (Analyze): {# analyzed / # expected}
   Stage 2 (Synthesize): {done/not run}
   Stage 3 (Push): {pushed/not run}
   Stage 4 (Simon Summary): {done/not run}

   Files:
     Manifest: {exists/missing}
     Transcripts: {count}
     Evaluations: {count} of {expected}
     Essentials review: {exists/missing}
     Simon summary: {exists/missing}

   Next step: {what to do}
   ```

## Route: Revise (Comment-Based Veto)

When Tim says "revise [client]":

1. Resolve client -> get `essentials_page_id` from org-mapping
2. Update status to `Revise`:
   ```bash
   export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
   python3 {SCRIPTS}/update-status.py '{client}' 'Revise'
   ```
3. Read ALL comments on the Essentials page using Notion MCP `get-comments`
   with `include_all_blocks: true`
   - Page-level comments = general revision instructions
   - Block-level comments = targeted fixes on specific content sections
4. For each unresolved comment:
   - Identify which field(s) it affects
   - Update the value in `3-essentials/essentials-review.md`
5. Re-push:
   ```bash
   python3 {SCRIPTS}/push-essentials.py '{client}'
   ```
6. Reply to each comment acknowledging the change
7. Update status:
   ```bash
   python3 {SCRIPTS}/update-status.py '{client}' 'Waiting for Review'
   ```
8. Log the revision to pipeline.log

## Route: Manual Push

1. Resolve client, validate `3-essentials/essentials-review.md` exists
2. Run:
   ```bash
   export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
   python3 {SCRIPTS}/push-essentials.py '{client}'
   ```
3. Update status to `Pushed To Document`
4. Report fields pushed and any blanks

## What This Skill Does

- Status checks (reads log + filesystem)
- Comment-based revisions (reads Notion comments, applies fixes, re-pushes)
- Manual push trigger

## What This Skill Does NOT Do

- Run the pipeline (use `/run-pipeline`)
- Analyze transcripts (that's Stage 1B inside the orchestrator)
- Map content to fields (that's Stage 2 inside the orchestrator)
- Generate Simon Summary (that's Stage 4 inside the orchestrator)
- Manage HITL approval gates (removed -- veto model only)
