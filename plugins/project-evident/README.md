# Project Evident Plugin v1.1.0

3-stage pipeline for managing Project Evident coaching workflows. Stage 1 runs autonomously in the background. Artifacts persist in visible client folders. Pipeline state tracked in a log. HITL review before any Notion push.

## Usage

Just tell it what you need:

- "Process E4 Youth" -> launches Stage 1 in background, checks back for Stage 2 when ready
- "Status on CHDC" -> reads pipeline log, reports what's done and what's running
- "Push ALAS" -> validates review file exists, generates JSON, pushes to Notion
- "Analyze the latest call for TAP" -> Stage 1 in background (returns immediately)
- "Populate essentials for LAA" -> Stage 2 field mapping only
- "Batch" -> full pipeline for all 11 clients in order

## Commands

- `/evaluate-session [request]` -- the main entry point, routes everything
- `/analyze-call [client-name]` -- direct access to Stage 1 (runs in background)
- `/populate-essentials [client-name]` -- direct access to Stage 2 field mapping

## Pipeline Stages

**Stage 1: Call Analyzer (background)** -- Phase A orchestrator fetches transcripts from Notion, filters, writes manifest. Phase B spawns one background agent per transcript for parallel analysis. Both phases run autonomously -- the conversation stays free.

**Stage 2: Essentials Populator (background)** -- reads evaluation files, maps to 50 Notion fields, validates against Simon's 7 Essential Elements, writes `essentials-review.md` for Tim's review. Runs autonomously in background.

**Stage 3: Evaluator/Router** -- reads pipeline log, validates state, manages HITL review, generates `essentials-payload.json`, pushes to Notion on approval.

## Background Execution Model

Stage 1 uses `run_in_background: true` for both Phase A and Phase B:

```
/analyze-call ALAS
  |
  +-> Phase A orchestrator (background)
       |  - Fetches from Notion
       |  - Filters and writes transcripts
       |  - Writes manifest.json
       |
       +-> Phase B agent: call-1 (background)
       +-> Phase B agent: call-2 (background)
       +-> Phase B agent: call-3 (background)
       ...each writes its own evaluation + pipeline.log entry
```

Check progress with `/evaluate-session status [client]` or read `pipeline.log` directly.

## Artifact Location

All files persist in:
```
~/Dev/claude-cowork/Clients/Project Evident Updates/{Org Name} Working Files/
+-- pipeline.log
+-- 1-transcripts/
+-- 2-evaluations/
+-- 3-essentials/
```

## Key Design Principles

- **Every file has Notion IDs in frontmatter** -- `client_page_id`, `essentials_page_id`, `transcript_page_id`
- **Pipeline log tracks state** -- the evaluator reads it before advancing any stage
- **Background agents write their own log entries** -- pipeline.log is the coordination mechanism
- **HALT on missing IDs** -- never write a file with blank Notion IDs, never push without `essentials_page_id`
- **HITL before Notion push** -- Tim reviews and edits `essentials-review.md` before anything hits the database
- **Version stamped** -- every file and log entry includes `plugin_version`

## Setup

Connect Notion when prompted. Authorize with a Notion account that has access to the Project Evident Coaching workspace. No API tokens needed.
