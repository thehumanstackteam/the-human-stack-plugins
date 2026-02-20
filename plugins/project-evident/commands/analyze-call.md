---
description: Analyze coaching call transcripts for a Project Evident client (runs in background)
argument-hint: [client-name]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task, TaskOutput
---

Analyze coaching call transcripts for **$ARGUMENTS** autonomously in the background.
No prompting, no approval gates, no stopping. Tim vetoes after the fact.

## Launch Sequence

1. Read ALL three reference files now (background agents cannot access plugin files):
   - `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/org-mapping.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/endpoint-map.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/simon-criteria.md`

2. Resolve the client's page IDs and folder name from org-mapping.
3. **HALT if `client_page_id` or `essentials_page_id` is missing from org-mapping.md.**
4. Create folder structure if needed:
   ```bash
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/1-transcripts"
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/2-evaluations"
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/3-essentials"
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/4-summary"
   ```

5. **Launch the Phase A orchestrator as a background subagent, embedding ALL reference
   file content directly in the prompt:**

```
Task(
  subagent_type: "general-purpose",
  description: "Stage 1: Analyze {client} coaching calls",
  run_in_background: true,
  prompt: "You are the Phase A orchestrator for the Project Evident call analyzer pipeline.
    You run AUTONOMOUSLY. Never ask questions. Never wait for approval. Run to completion.

    ## Your Mission
    1. Retrieve all coaching call transcripts from Notion for this client
    2. Filter out cancellations and non-sessions
    3. Write raw transcripts and a manifest to disk
    4. Spawn one background Phase B subagent per transcript for parallel analysis

    ## Client Context
    Client: {Short Name}
    Client Page ID: {client_page_id}
    Essentials Page ID: {essentials_page_id}
    Folder: ~/Dev/claude-cowork/Clients/Project Evident Updates/{folder_name}/

    ## Instructions
    Follow the coaching-call-analyzer skill exactly:
    - Steps A0-A6: Retrieve, filter, write transcripts and manifest
    - Steps B0-B1: Read manifest, spawn one background Task subagent per call
      (run_in_background: true on each)
    - Step B2: Log the Phase B launch to pipeline.log and return

    IMPORTANT: When spawning Phase B agents, embed the endpoint-map and simon-criteria
    content in each agent's prompt. Background agents cannot read plugin files.

    Phase B agents run autonomously. Each writes its own evaluation file and
    pipeline.log entry. You do NOT wait for them to finish.

    Every file gets YAML frontmatter with client_page_id, essentials_page_id,
    transcript_page_id, and plugin_version: 3.0.0.
    If any ID can't be resolved, HALT -- don't write a file with blank IDs.

    ## Pipeline Continuation
    After Phase B agents are launched and logged, check if Stage 2 can run:
    - Count evaluation files in 2-evaluations/ matching call-*-evaluation.md
    - Compare against manifest calls_to_analyze count
    - If all evaluations exist -> auto-dispatch Stage 2 (populate essentials)
    - If not all done yet -> log that continuation will happen when Phase B completes
    NOTE: Phase B agents themselves should also check for continuation after writing
    their evaluation file. The LAST Phase B agent to finish triggers Stage 2.

    To dispatch Stage 2, read the essentials-populator SKILL.md from:
      ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/skills/essentials-populator/SKILL.md
    Then launch a background agent following its instructions with all reference
    content embedded in the prompt. Update status to 'Populating Fields' first:
      export NOTION_API_KEY=$(op item get 'Notion Token' --vault 'MCP Tokens' --fields credential --reveal 2>/dev/null)
      python3 ~/Dev/GitHub/the-human-stack-plugins/plugins/project-evident/scripts/update-status.py '{short_name}' 'Populating Fields'

    ## Reference: Org Mapping
    {paste full org-mapping.md content here}

    ## Reference: Endpoint Map
    {paste full endpoint-map.md content here}

    ## Reference: Simon Criteria
    {paste full simon-criteria.md content here}"
)
```

6. **Tell the user the analysis is running in the background:**
   - Report which client was launched
   - Report the working folder path
   - Explain: "Stage 1 is running autonomously. When all calls are analyzed, Stage 2 will auto-dispatch."
   - Instruct: "Check progress with `/evaluate-session status {client}` or read `pipeline.log` directly."
   - Do NOT block waiting for results
