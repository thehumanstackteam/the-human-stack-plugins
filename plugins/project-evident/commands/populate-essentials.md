---
description: Populate Essentials endpoint fields for a Project Evident coaching client
argument-hint: [client-name]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Populate the AI Implementation Essentials endpoint fields for **$ARGUMENTS**.

Follow the essentials-populator skill workflow exactly:

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/essentials-populator/references/org-mapping.md` to get the client's page IDs and folder name
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/essentials-populator/references/endpoint-map.md` for exact Notion property names
3. Read `${CLAUDE_PLUGIN_ROOT}/skills/essentials-populator/references/simon-criteria.md` for the 7 Essential Elements quality gate
4. **HALT if `client_page_id` or `essentials_page_id` is missing from org-mapping.md**
5. Glob `~/Dev/claude-cowork/Clients/Project Evident Updates/{Folder Name}/2-evaluations/call-*-evaluation.md`
6. **If zero files found → HALT** with "Run Stage 1 first: /analyze-call {client}"
7. **Validate `essentials_page_id` is present and consistent** across all evaluation files
8. Map evaluation content to all 50 fields using endpoint-map.md property names
9. Calculate values using $65/hr staff, $100/hr ED, $200/hr consultant rates
10. Write `3-essentials/essentials-review.md` with YAML frontmatter carrying both Notion IDs
11. Run Essential Elements quality gate — report gaps or generate summary sentence
12. Append SUCCESS or FAILED entry to `pipeline.log`
13. Tell Tim to review the file and run the evaluator to push when ready

**Important:** This skill does NOT push to Notion. It writes `essentials-review.md` for Tim's review. Stage 3 (evaluator) handles the push after Tim approves.
