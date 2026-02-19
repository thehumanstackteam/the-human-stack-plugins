---
description: Analyze coaching call transcripts for a Project Evident client (runs in background)
argument-hint: [client-name]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Analyze coaching call transcripts for **$ARGUMENTS** using the coaching-call-analyzer skill.

**This runs autonomously in the background.** Launch the Phase A orchestrator as a background
subagent, then return immediately so the conversation stays free.

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
   ```

5. **Launch the Phase A orchestrator as a background subagent, embedding ALL reference
   file content directly in the prompt:**

```
Task(
  subagent_type: "general-purpose",
  description: "Stage 1: Analyze {client} coaching calls",
  run_in_background: true,
  prompt: "You are the Phase A orchestrator for the Project Evident call analyzer pipeline.

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
    transcript_page_id, and plugin_version: 1.1.0.
    If any ID can't be resolved, HALT -- don't write a file with blank IDs.

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
   - Explain: "Phase A (retrieval) and Phase B (analysis) are running autonomously in the background."
   - Instruct: "Check progress with `/evaluate-session status {client}` or read `pipeline.log` directly."
   - Do NOT block waiting for results
