---
description: Populate Essentials endpoint fields for a Project Evident coaching client (runs in background)
argument-hint: [client-name]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Populate the AI Implementation Essentials endpoint fields for **$ARGUMENTS** in the background.

**This runs autonomously in the background.** Launch the populator as a background subagent,
then return immediately so the conversation stays free.

## Launch Sequence

1. Read ALL three reference files now (background agents cannot access plugin files):
   - `${CLAUDE_PLUGIN_ROOT}/skills/essentials-populator/references/org-mapping.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/essentials-populator/references/endpoint-map.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/essentials-populator/references/simon-criteria.md`

2. Resolve the client's page IDs and folder name from org-mapping.
3. **HALT if `client_page_id` or `essentials_page_id` is missing from org-mapping.md.**
4. Check that evaluation files exist in `2-evaluations/`. If none -> HALT with "Run Stage 1 first."

5. **Launch the populator as a background subagent, embedding ALL reference
   file content directly in the prompt:**

```
Task(
  subagent_type: "general-purpose",
  description: "Stage 2: Populate essentials for {client}",
  run_in_background: true,
  prompt: "You are the Stage 2 essentials populator for Project Evident.
    Populate essentials for {Client Name}.
    Client page ID: {client_page_id}.
    Essentials page ID: {essentials_page_id}.
    Folder: ~/Dev/claude-cowork/Clients/Project Evident Updates/{folder_name}/

    Run the full workflow:
    - Glob 2-evaluations/call-*-evaluation.md to find all evaluation files
    - Validate essentials_page_id is present and consistent across all files
    - Map evaluation content to all 50 fields using the endpoint map below
    - Calculate values using $65/hr staff, $100/hr ED, $200/hr consultant rates
    - Write 3-essentials/essentials-review.md with YAML frontmatter
    - Run Essential Elements quality gate using the simon criteria below
    - Append SUCCESS or FAILED entry to pipeline.log

    ## Reference: Endpoint Map
    {paste full endpoint-map.md content here}

    ## Reference: Simon Criteria
    {paste full simon-criteria.md content here}

    Return: quality gate results, file path, any gaps."
)
```

6. **Tell the user Stage 2 is running in the background:**
   - Report which client was launched
   - Instruct: "Check progress with `/evaluate-session status {client}` or read `pipeline.log` directly."
   - Do NOT block waiting for results

**Important:** This skill does NOT push to Notion. It writes `essentials-review.md` for Tim's review. Stage 3 (evaluator) handles the push after Tim approves.
