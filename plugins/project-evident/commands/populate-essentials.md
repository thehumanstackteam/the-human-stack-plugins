---
description: Populate Essentials endpoint fields for a Project Evident coaching client (runs in background)
argument-hint: [client-name]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task, TaskOutput
---

Populate the AI Implementation Essentials endpoint fields for **$ARGUMENTS** autonomously
in the background. No prompting, no approval gates, no stopping. Tim vetoes after the fact.

## Launch Sequence

1. Read ALL three reference files now (background agents cannot access plugin files):
   - `${CLAUDE_PLUGIN_ROOT}/skills/essentials-populator/references/org-mapping.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/essentials-populator/references/endpoint-map.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/essentials-populator/references/simon-criteria.md`

2. Resolve the client's page IDs and folder name from org-mapping.
3. **HALT if `client_page_id` or `essentials_page_id` is missing from org-mapping.md.**
4. Check that evaluation files exist in `2-evaluations/`. If none -> HALT with "Run Stage 1 first."

5. Update status:
   ```bash
   export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
   python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/update-status.py '{short_name}' 'Populating Fields'
   ```

6. **Launch the populator as a background subagent, embedding ALL reference
   file content directly in the prompt:**

```
Task(
  subagent_type: "general-purpose",
  description: "Stage 2: Populate essentials for {client}",
  run_in_background: true,
  prompt: "You are the Stage 2 essentials populator for Project Evident.
    You run AUTONOMOUSLY. Never ask questions. Never wait for approval. Run to completion.

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
    - Write 3-essentials/essentials-payload.json
    - Run Essential Elements quality gate using the simon criteria below
    - Append SUCCESS or FAILED entry to pipeline.log

    ## Pipeline Continuation
    After writing essentials-review.md and essentials-payload.json:
    1. Update status to 'Quality Gate':
       export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
       python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/update-status.py '{short_name}' 'Quality Gate'
    2. If quality gate passes (or proceeds with flagged gaps), auto-dispatch Stage 3:
       - Update status to 'Pushing to Notion':
         python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/update-status.py '{short_name}' 'Pushing to Notion'
       - Run the push script directly:
         python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/push-essentials.py '{short_name}'
       - Update status to 'Pushed To Document':
         python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/update-status.py '{short_name}' 'Pushed To Document'
       - Log push to pipeline.log
    3. After Stage 3 push succeeds, auto-dispatch Stage 4 (Simon Summary):
       - Update status to 'Writing Summary':
         python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/update-status.py '{short_name}' 'Writing Summary'
       - Read the simon-summary SKILL.md from:
         ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/simon-summary/SKILL.md
       - Read essentials-review.md (you just wrote it)
       - Read simon-criteria reference (already embedded below)
       - Follow the SKILL.md instructions to write the Simon Summary
       - Write to 4-summary/simon-summary.md
       - Push to the 'Simon Summary' property on the Client page via Notion API (use curl with NOTION_API_KEY)
       - Log to pipeline.log

    ## Reference: Endpoint Map
    {paste full endpoint-map.md content here}

    ## Reference: Simon Criteria
    {paste full simon-criteria.md content here}

    Return: quality gate results, file path, any gaps."
)
```

7. **Tell the user Stage 2 is running in the background:**
   - Report which client was launched
   - Explain: "Stage 2 is running autonomously. On completion it will auto-push to Notion (Stage 3) and write the Simon Summary (Stage 4)."
   - Instruct: "Check progress with `/evaluate-session status {client}` or read `pipeline.log` directly."
   - Do NOT block waiting for results
