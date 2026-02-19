# Project Evident Plugin v1.2.0

End-to-end pipeline for Project Evident coaching: analyze call transcripts, populate 50 Essentials fields, push to Notion, and generate Simon Summary. Autonomous orchestrator with live Notion status updates and comment-based veto.

## Usage

- `/run-pipeline Building Promise` -> full autonomous pipeline: extract -> analyze -> synthesize -> evaluate -> push -> simon summary
- `/run-pipeline all` -> parallel: one orchestrator per client
- `/evaluate-session status CHDC` -> check pipeline state from log + filesystem
- `/evaluate-session revise ALAS` -> read Notion comments, apply fixes, re-push
- `/evaluate-session push TAP` -> manual re-push to Notion

## Commands

- `/run-pipeline [client|all]` -- autonomous end-to-end orchestrator (no stopping)
- `/evaluate-session [status|revise|push] [client]` -- status checks and revisions
- `/analyze-call [client]` -- direct access to Stage 1 (runs in background)
- `/populate-essentials [client]` -- direct access to Stage 2 field mapping
- `/simon-summary [client]` -- Stage 4: funder-ready summary paragraph

## Pipeline Stages

**Stage 1A: Extract** -- `pull-transcripts.py` fetches coaching calls from Notion, filters cancellations and empties, writes raw transcripts + manifest to disk.

**Stage 1B: Analyze** -- one background agent per transcript, all parallel. Topic clustering, speaker attribution, component evaluation, Essential Elements scoring.

**Stage 2: Synthesize** -- maps evaluations to 50 Notion fields using endpoint-map. Builds L/M/H value proxy tables where projected data exists.

**Stage 2.5: Evaluate** -- quality gate checks 7/7 Essential Elements. Auto-retry (max 2) if gaps exist.

**Stage 3: Deliver** -- `push-essentials.py` clears + pushes all 50 fields and page body to Notion.

**Stage 4: Simon Summary** -- generates a funder-ready paragraph written to the Client page "Simon Summary" property.

## Status Tracking

The Essentials DB "Status" property updates at every stage transition:
Pulling Transcripts -> Analyzing Calls -> Populating Fields -> Quality Gate -> Pushing to Notion -> Pushed To Document -> Writing Summary

Veto flow: Revise -> Waiting for Review -> Pushed To Document

Status is also synced to `pipeline-manifest.md` locally.

## Veto Model

No approval gates. Pipeline runs to completion. Tim reviews the pushed output in Notion and leaves comments if changes are needed. `/evaluate-session revise {client}` reads those comments and applies fixes.

## Artifact Location

```
~/Dev/claude-cowork/Clients/Project Evident Updates/{Org Name} Working Files/
+-- pipeline.log
+-- 1-transcripts/    (raw transcripts + manifest.json)
+-- 2-evaluations/    (per-call analysis files)
+-- 3-essentials/     (essentials-review.md + payload.json)
+-- 4-summary/        (simon-summary.md)
```

## Scripts

All in `scripts/`, all require `NOTION_API_KEY` env var:

- `pull-transcripts.py` -- Stage 1A extraction from Notion
- `push-essentials.py` -- Stage 3 push to Notion (clear + write)
- `update-status.py` -- updates Notion status + pipeline-manifest.md
- `push-evaluations.py` -- push eval content to Coaching Call pages

## Key Design Principles

- **Filesystem as artifact store** -- all intermediate outputs are files on disk
- **Background agents with manifest coordination** -- file count = completion detection
- **Embed references, don't reference paths** -- background agents can't access plugin files
- **Credentials exported once** -- one Touch ID per pipeline run
- **Status is a sidecar** -- reports state but doesn't affect pipeline logic
- **Veto, not approval** -- pipeline assumes approval, user vetoes after

## Setup

Connect Notion when prompted. Authorize with access to the Project Evident Coaching workspace.
