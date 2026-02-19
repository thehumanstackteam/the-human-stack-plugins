---
description: Generate the Simon Summary paragraph for a Project Evident coaching client
argument-hint: [client-name]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Generate the Simon Summary for **$ARGUMENTS**.

## Sequence

1. Read reference files:
   - `${CLAUDE_PLUGIN_ROOT}/skills/simon-summary/references/org-mapping.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/simon-summary/references/simon-criteria.md`

2. Resolve the client from org-mapping. HALT if client_page_id is missing.

3. Read `~/Dev/claude-cowork/Clients/Project Evident Updates/{folder_name}/3-essentials/essentials-review.md`.
   HALT if it doesn't exist -- Stage 2 must complete first.

4. Check the Essential Elements Quality Gate in the review file. All 7 must be
   specific (or Tim must have approved despite gaps).

5. Generate the summary paragraph following the simon-summary SKILL.md instructions.
   All 7 elements must appear with specific content. One paragraph, funder-readable.

6. Present the summary to Tim for review before pushing to Notion.

7. On approval:
   - Write to `4-summary/simon-summary.md`
   - Push to the "Simon Summary" property on the Client page via Notion MCP
   - Append to pipeline.log

**This skill writes to the Client page in Notion after Tim approves.**
