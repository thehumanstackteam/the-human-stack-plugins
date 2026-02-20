---
description: Generate the Simon Summary paragraph for a Project Evident coaching client (runs in background)
argument-hint: [client-name]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task, TaskOutput
---

Generate the Simon Summary for **$ARGUMENTS** autonomously in the background.
No prompting, no approval gates, no stopping. Tim vetoes after the fact.

## Launch Sequence

1. Read reference files (background agents cannot access plugin files):
   - `${CLAUDE_PLUGIN_ROOT}/skills/simon-summary/references/org-mapping.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/simon-summary/references/simon-criteria.md`

2. Resolve the client from org-mapping. HALT if client_page_id is missing.

3. Read `~/Dev/claude-cowork/Clients/Project Evident Updates/{folder_name}/3-essentials/essentials-review.md`.
   HALT if it doesn't exist -- Stage 2 must complete first.

4. Read the simon-summary SKILL.md:
   - `${CLAUDE_PLUGIN_ROOT}/skills/simon-summary/SKILL.md`

5. Update status:
   ```bash
   export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
   python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/update-status.py '{short_name}' 'Writing Summary'
   ```

6. **Launch the summary writer as a background subagent, embedding ALL reference
   content and the SKILL.md instructions directly in the prompt:**

```
Task(
  subagent_type: "general-purpose",
  description: "Stage 4: Simon summary for {client}",
  run_in_background: true,
  prompt: "You are the Simon Summary writer for Project Evident.
    You run AUTONOMOUSLY. Never ask questions. Never wait for approval. Run to completion.

    Client: {short_name}
    Client page ID: {client_page_id}
    Working directory: ~/Dev/claude-cowork/Clients/Project Evident Updates/{folder_name}/

    Read the essentials review at:
      {working_dir}/3-essentials/essentials-review.md

    Follow the Simon Summary skill instructions below EXACTLY:
    1. Extract raw ingredients from essentials-review.md
    2. Choose the lead (constraint > blockage > time collapse > tool)
    3. Draft two sentences
    4. Run all 9 self-evaluation tests. Rewrite (don't patch) any failures.
    5. Write to {working_dir}/4-summary/simon-summary.md
    6. Push to the 'Simon Summary' rich_text property on the Client page:
       - Use curl with NOTION_API_KEY from environment
       - Target: Client page {client_page_id}
       - If summary exceeds 2000 chars, split into multiple rich_text elements
    7. Log to pipeline.log

    ## Notion API Access
    Export the token before any API calls:
      export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)

    ## Simon Summary SKILL.md Instructions
    {paste full SKILL.md content here}

    ## Reference: Simon Criteria
    {paste full simon-criteria.md content here}

    ## Pipeline Continuation
    Stage 4 is the final stage. After completion:
    - Log SUCCESS to pipeline.log
    - No further stages to dispatch
    - Pipeline is complete for this client"
)
```

7. **Tell the user the Simon Summary is running in the background:**
   - Report which client was launched
   - Explain: "Stage 4 is running autonomously. The summary will be written and pushed to Notion without approval gates."
   - Instruct: "Check progress with `/evaluate-session status {client}` or read `pipeline.log` directly."
   - Do NOT block waiting for results
