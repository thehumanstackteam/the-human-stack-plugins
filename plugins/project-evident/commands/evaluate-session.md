---
description: Pipeline controller for Project Evident -- routes to analyze, populate, push, status, or revise
argument-hint: [client-name or "batch" or "status [client]" or "push [client]"]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task, TaskOutput
---

Process Project Evident coaching work for **$ARGUMENTS** using the coaching-evaluator skill.
All stages run AUTONOMOUSLY in the background. No prompting, no approval gates.
Tim vetoes after the fact.

This is the single entry point. The evaluator reads pipeline state and routes to the right workflow:

- **"process [client]"** -> full pipeline. Dispatches Stage 1 as background agent; pipeline auto-chains through all stages.
- **"status [client]"** -> read pipeline.log + filesystem, report what's done/pending/running
- **"push [client]"** -> validate essentials-review.md exists -> run push-essentials.py
- **"analyze call for [client]"** -> dispatch Stage 1 call analyzer (background, auto-chains to Stage 2+)
- **"populate essentials for [client]"** -> dispatch Stage 2 populator (background, auto-chains to Stage 3+4)
- **"simon summary for [client]"** -> dispatch Stage 4 simon summary (background)
- **"revise [client]"** -> read Notion comments on the Essentials page, apply changes, re-push
- **"batch"** -> full pipeline for all 11 clients sequentially (each auto-chains)

Follow the coaching-evaluator skill workflow:

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-evaluator/references/org-mapping.md` for all client IDs and folder names
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-evaluator/references/endpoint-map.md` for field names
3. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-evaluator/references/simon-criteria.md` for quality gate
4. **Always read pipeline state first:** check `pipeline.log` AND verify files exist on disk
5. **Cross-validate log vs. filesystem** -- don't trust the log alone, don't trust files alone
6. **Generate `essentials-payload.json` before pushing** -- this is the single source of truth for what gets written to Notion

**All stages run as autonomous background subagents with pipeline continuation.**
Each stage auto-dispatches the next stage on completion. The main conversation stays free.

When dispatching any stage:
- Use `run_in_background: true`
- Embed all reference file content in the subagent prompt
- Include pipeline continuation instructions so the agent chains to the next stage
- Include Notion token export: `export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)`
- Tell the agent to run autonomously: "Never ask questions. Never wait for approval."

## Revise Flow (Comment-Based Veto)

When Tim says **"revise [client]"**, the veto is driven by Notion comments:

1. Resolve client -> get `essentials_page_id` from org-mapping
2. Update status: `Revise`
3. Read ALL comments on the Essentials page using Notion MCP `get-comments` with `include_all_blocks: true`
   - Page-level comments = general revision instructions
   - Block-level comments = targeted fixes on specific content sections
4. For each unresolved comment:
   - Identify which field(s) it affects
   - Update the value in `essentials-review.md`
   - Update `essentials-payload.json`
5. Re-push updated fields to the Essentials page
6. Resolve each comment after the fix is applied (reply acknowledging the change)
7. Update status: `Waiting for Review`
8. Log the revision to pipeline.log

Tim reviews. If more comments appear, run revise again. When satisfied, Tim
resolves remaining comments and the status stays at `Pushed To Document`.
