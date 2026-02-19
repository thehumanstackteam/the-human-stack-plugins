---
description: Analyze coaching call transcripts for a Project Evident client (runs in background)
argument-hint: [client-name]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Analyze coaching call transcripts for **$ARGUMENTS** using the coaching-call-analyzer skill.

**This runs autonomously in the background.** Launch the Phase A orchestrator as a background
subagent, then return immediately so the conversation stays free.

## Launch Sequence

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/org-mapping.md` to resolve the client's page IDs and folder name.
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/endpoint-map.md` for the 50 field names.
3. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/simon-criteria.md` for Essential Elements.
4. **HALT if `client_page_id` or `essentials_page_id` is missing from org-mapping.md.**
5. Create folder structure if needed:
   ```bash
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/1-transcripts"
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/2-evaluations"
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/3-essentials"
   ```

6. **Launch the Phase A orchestrator as a background subagent:**

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

    ## Reference Files (read these first)
    - {skill_directory}/references/org-mapping.md
    - {skill_directory}/references/endpoint-map.md
    - {skill_directory}/references/simon-criteria.md

    ## Instructions
    Follow the coaching-call-analyzer skill exactly:
    - Steps A0-A6: Retrieve, filter, write transcripts and manifest
    - Steps B0-B1: Read manifest, spawn one background Task subagent per call
      (run_in_background: true on each)
    - Step B2: Log the Phase B launch to pipeline.log and return

    Phase B agents run autonomously. Each writes its own evaluation file and
    pipeline.log entry. You do NOT wait for them to finish.

    Every file gets YAML frontmatter with client_page_id, essentials_page_id,
    transcript_page_id, and plugin_version: 1.1.0.
    If any ID can't be resolved, HALT -- don't write a file with blank IDs."
)
```

7. **Tell the user the analysis is running in the background:**
   - Report which client was launched
   - Report the working folder path
   - Explain: "Phase A (retrieval) and Phase B (analysis) are running autonomously in the background."
   - Instruct: "Check progress with `/evaluate-session status {client}` or read `pipeline.log` directly."
   - Do NOT block waiting for results
