# feat(architect): Add Session Hoardinator Module

> **Priority**: Phase 1 packaging
> **PRD**: [session-hoardinator-prd.md](https://github.com/jabberlockie/AI-Readiness-and-Digital-Health-Diagnostic/blob/main/architect/docs/session-hoardinator-prd.md)
> **Source repo**: jabberlockie/AI-Readiness-and-Digital-Health-Diagnostic

## What to build

Ingest Claude Code JSONL session transcripts into normalized Supabase tables for analytics and learning loop closure. Ships as an architect module — every architect-enabled project gets it via marketplace update.

## Skills to create

### `/log` — Log the current session
User says `/log` (or "log this session") mid-conversation. Parses the active session's JSONL, detects incremental state, uploads only new messages.

### `/ingest` — Batch sweep
- `/ingest` — all sessions for current repo
- `/ingest all` — all sessions across all repos
- `/ingest 2026-02-23` — sessions from a specific date

## Files to add

```
plugins/architect/
├── scripts/
│   ├── parse-sessions.py      # JSONL parser (from /tmp/parse-sessions.py prototype)
│   └── upload-sessions.sh     # Batched upload via Supabase Management API
├── skills/
│   ├── log.md                 # /log skill definition
│   └── ingest.md              # /ingest skill definition
└── hooks/
    ├── query-hoardinator.sh   # SessionStart: query past learnings
    └── save-learnings.sh      # PreCompact: save learnings
```

## Supabase tables (already deployed)

Project: `hdhmwaldvzxwhimoemap` (the-hoardinator)

- `sessions` — 1 row per conversation (tokens, model, branches, security flags)
- `messages` — 1 row per conversational unit (text, thinking, tool_result, system, compaction)
- `tool_calls` — 1 row per tool invocation (10 categories, agent stats, security)
- `session_embeddings` — classified learnings with pgvector

## Key features

- **Incremental ingestion** — delta detect via `message_index` + `last_message_at`
- **Empty session filtering** — skips 0-message sessions
- **Namespace** — repo/org/author from `git remote`, one Supabase serves all
- **Dollar-quoted SQL** — handles markdown, shell output, nested quotes
- **40-stmt batching** — stays under Supabase API payload limits

## Prototype status

Working prototype at `/tmp/parse-sessions.py` and `/tmp/upload-sessions.sh`. Tested: 18 sessions, 2857 messages, 1490 tool calls ingested successfully. Hooks prototyped in `.claude/hooks/`.

Needs: bundle into architect plugin structure, create skill files, wire hooks, publish.
