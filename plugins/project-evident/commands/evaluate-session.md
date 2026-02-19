---
description: Pipeline controller for Project Evident — routes to analyze, populate, push, or status check
argument-hint: [client-name or "batch" or "status [client]" or "push [client]"]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Process Project Evident coaching work for **$ARGUMENTS** using the coaching-evaluator skill.

This is the single entry point. The evaluator reads pipeline state and routes to the right workflow:

- **"process [client]"** → full pipeline (analyze → populate → HITL review → push)
- **"status [client]"** → read pipeline.log + filesystem, report what's done/pending
- **"push [client]"** → validate essentials-review.md exists → generate JSON → push to Notion
- **"analyze call for [client]"** → dispatch Stage 1 call analyzer only
- **"populate essentials for [client]"** → dispatch Stage 2 populator only
- **"batch"** → full pipeline for all 11 clients in order

Follow the coaching-evaluator skill workflow:

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-evaluator/references/org-mapping.md` for all client IDs and folder names
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-evaluator/references/endpoint-map.md` for field names
3. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-evaluator/references/simon-criteria.md` for quality gate
4. **Always read pipeline state first:** check `pipeline.log` AND verify files exist on disk
5. **Cross-validate log vs. filesystem** — don't trust the log alone, don't trust files alone
6. **Never push to Notion without Tim's explicit approval**
7. **Generate `essentials-payload.json` before pushing** — this is the single source of truth for what gets written to Notion

When dispatching subagents (Stage 1 or Stage 2), use the Task tool with subagent_type "general-purpose" and instruct them to invoke the appropriate skill. After subagent return, **verify the expected output files exist** before proceeding.
