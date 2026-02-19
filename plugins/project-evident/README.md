# Project Evident Plugin v0.3.0

3-stage pipeline for managing Project Evident coaching workflows. Artifacts persist in visible client folders. Pipeline state tracked in a log. HITL review before any Notion push.

## Usage

Just tell it what you need:

- "Process E4 Youth" → runs full pipeline (analyze → populate → review → push)
- "Status on CHDC" → reads pipeline log, reports what's done and what's next
- "Push ALAS" → validates review file exists, generates JSON, pushes to Notion
- "Analyze the latest call for TAP" → Stage 1 transcript analysis only
- "Populate essentials for LAA" → Stage 2 field mapping only
- "Batch" → full pipeline for all 11 clients in order

## Commands

- `/evaluate-session [request]` — the main entry point, routes everything
- `/analyze-call [client-name]` — direct access to Stage 1 transcript analysis
- `/populate-essentials [client-name]` — direct access to Stage 2 field mapping

## Pipeline Stages

**Stage 1: Call Analyzer** — fetches transcripts from Notion → semantic topic clustering → speaker attribution log → component evaluation → Essential Elements scorecard → writes files to `1-transcripts/` and `2-evaluations/`

**Stage 2: Essentials Populator** — reads evaluation files → maps to 50 Notion fields → validates against Simon's 7 Essential Elements → writes `essentials-review.md` for Tim's review

**Stage 3: Evaluator/Router** — reads pipeline log → validates state → manages HITL review → generates `essentials-payload.json` → pushes to Notion on approval

## Artifact Location

All files persist in:
```
~/Dev/claude-cowork/Clients/Project Evident Updates/{Org Name} Working Files/
├── pipeline.log
├── 1-transcripts/
├── 2-evaluations/
└── 3-essentials/
```

## Key Design Principles

- **Every file has Notion IDs in frontmatter** — `client_page_id`, `essentials_page_id`, `transcript_page_id`
- **Pipeline log tracks state** — the evaluator reads it before advancing any stage
- **HALT on missing IDs** — never write a file with blank Notion IDs, never push without `essentials_page_id`
- **HITL before Notion push** — Tim reviews and edits `essentials-review.md` before anything hits the database
- **Version stamped** — every file and log entry includes `plugin_version: 0.3.0`

## Setup

Connect Notion when prompted. Authorize with a Notion account that has access to the Project Evident Coaching workspace. No API tokens needed.
