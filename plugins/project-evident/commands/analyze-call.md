---
description: Analyze coaching call transcripts for a Project Evident client
argument-hint: [client-name]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

Analyze coaching call transcripts for **$ARGUMENTS** using the coaching-call-analyzer skill.

Follow the coaching-call-analyzer skill workflow exactly — it has a two-phase architecture:

**Phase A (Retrieval):**
1. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/org-mapping.md` to get the client's page IDs and folder name
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/endpoint-map.md` for the 50 field names
3. Read `${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/simon-criteria.md` for Essential Elements
4. **HALT if `client_page_id` or `essentials_page_id` is missing from org-mapping.md**
5. Create folder structure: `~/Dev/claude-cowork/Clients/Project Evident Updates/{Folder Name}/1-transcripts/` and `2-evaluations/`
6. Fetch the client org page via Notion MCP `fetch` tool using the page ID
7. From the org page, get the Coaching Calls relation IDs
8. For each coaching call page: fetch → filter by Page Type, transcript content, and not-a-call check → save passing transcripts to `1-transcripts/`
9. Write `1-transcripts/manifest.json` with all calls to analyze and skip reasons

**Phase B (Parallel Analysis):**
10. For each call in the manifest, spawn a parallel Task subagent to analyze that single transcript
11. Each subagent reads one transcript + reference files → writes one evaluation to `2-evaluations/`
12. Collect results, verify all evaluation files exist
13. Every file gets YAML frontmatter with `client_page_id`, `essentials_page_id`, `transcript_page_id`, and `plugin_version: 1.0.0`
14. Append SUCCESS or FAILED entry to `pipeline.log` for each call processed
15. Present per-call Essential Elements scorecards and recommend running Stage 2

**Important:** Every file must have Notion IDs in frontmatter. If any ID can't be resolved, HALT — don't write a file with blank IDs.
