# Project Evident Plugin v3.0.0

End-to-end pipeline for Project Evident coaching: analyze call transcripts, populate 50 Essentials fields, push to Notion, and generate Simon Summary. Fire-and-forget architecture with pipeline continuation chaining -- every command dispatches background agents that auto-chain to the next stage. No HITL, no approval gates. Comment-based veto.

## Usage

- `/run-pipeline Building Promise` -> full autonomous pipeline: dispatches Stage 1 which auto-chains through all stages
- `/run-pipeline all` -> sequential: one client at a time, each auto-chains
- `/evaluate-session status CHDC` -> check pipeline state from log + filesystem
- `/evaluate-session revise ALAS` -> read Notion comments, apply fixes, re-push
- `/evaluate-session push TAP` -> manual re-push to Notion
- `/analyze-call TAP` -> Stage 1 in background, auto-chains to Stage 2+
- `/populate-essentials TAP` -> Stage 2 in background, auto-chains to Stage 3+4
- `/simon-summary TAP` -> Stage 4 in background

## Architecture (v3.0.0)

**Thin dispatcher + pipeline continuation.** Every command reads reference files, dispatches a background agent, and returns immediately. Each background agent runs autonomously with Bash permission (python scripts, curl, status updates) and auto-chains to the next pipeline stage on completion.

- No context flows through the orchestrator after dispatch
- No HITL prompts -- all tools (including Bash) run without approval
- Pipeline state tracked via pipeline.log + filesystem
- Tim vetoes after the fact via Notion comments

## Commands

- `/run-pipeline [client|all]` -- dispatches full pipeline as background agent
- `/evaluate-session [status|revise|push|process] [client]` -- routes to appropriate action
- `/analyze-call [client]` -- Stage 1 in background, auto-chains to Stage 2+3+4
- `/populate-essentials [client]` -- Stage 2 in background, auto-chains to Stage 3+4
- `/simon-summary [client]` -- Stage 4 in background

## Pipeline Stages

**Stage 1A: Extract** -- `pull-transcripts.py` fetches coaching calls from Notion, filters cancellations and empties, writes raw transcripts + manifest to disk.

**Stage 1B: Analyze** -- one background agent per transcript, all parallel. Topic clustering, speaker attribution, component evaluation, Essential Elements scoring. Last agent to finish triggers Stage 2.

**Stage 2: Synthesize** -- maps evaluations to 50 Notion fields using endpoint-map. Builds L/M/H value proxy tables where projected data exists. Auto-chains to Stage 3.

**Stage 2.5: Quality Gate** -- checks 7/7 Essential Elements. Auto-retry (max 2) if gaps exist.

**Stage 3: Push** -- `push-essentials.py` clears + pushes all 50 fields and page body to Notion. Auto-chains to Stage 4.

**Stage 4: Simon Summary** -- generates a funder-ready paragraph written to the Client page "Simon Summary" property. Final stage.

## Pipeline Continuation

Each stage checks prerequisites for the next stage and auto-dispatches it:
- Stage 1B (last eval written) -> Stage 2
- Stage 2 (essentials written) -> Stage 3 (push) -> Stage 4 (simon summary)
- Stage 4 -> pipeline complete

This means `/analyze-call ClientX` runs the full pipeline if all prerequisites are met along the way.

## Status Tracking

The Essentials DB "Status" property updates at every stage transition:
Pulling Transcripts -> Analyzing Calls -> Populating Fields -> Quality Gate -> Pushing to Notion -> Pushed To Document -> Writing Summary

Veto flow: Revise -> Waiting for Review -> Pushed To Document

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

- **Fire-and-forget dispatch** -- commands launch background agents and return immediately
- **Pipeline continuation** -- each stage auto-chains to the next on completion
- **No HITL** -- all tools including Bash run without approval prompts
- **Filesystem as artifact store** -- all intermediate outputs are files on disk
- **Background agents with manifest coordination** -- file count = completion detection
- **Embed references, don't reference paths** -- background agents can't access plugin files
- **Credentials exported once** -- one Touch ID per pipeline run
- **Status is a sidecar** -- reports state but doesn't affect pipeline logic
- **Veto, not approval** -- pipeline assumes approval, user vetoes after

## Setup

Connect Notion when prompted. Authorize with access to the Project Evident Coaching workspace.
