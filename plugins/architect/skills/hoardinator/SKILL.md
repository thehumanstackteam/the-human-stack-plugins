---
name: hoardinator
description: Session Hoardinator - ingest Claude Code JSONL session transcripts into Supabase for analytics. Use when user says /hoardinator, "log this session", "ingest sessions", or asks about session analytics.
---

# Session Hoardinator

Ingest Claude Code JSONL session transcripts into normalized Supabase tables (sessions, messages, tool_calls) for analytics and learning loop closure. Works standalone -- does not require architect to be initialized.

## Prerequisites

- `SUPABASE_URL` environment variable set (e.g. `https://hdhmwaldvzxwhimoemap.supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY` environment variable set (Supabase secret key)
- Tables `sessions`, `messages`, `tool_calls` must exist in Supabase

If env vars are missing, commands will exit with a clear error message.

## Commands

### /hoardinator log

Log the current session into the Hoardinator database.

**What it does:**
1. Finds the current session JSONL file
2. Parses it (linked-list traversal, tool classification, security detection)
3. Uploads to Supabase via REST API with delta detection (skips already-ingested messages)

**Implementation steps:**

1. Find the current session JSONL:
```bash
# Find the most recent .jsonl in the Claude projects dir matching current cwd
PROJECTS_DIR="$HOME/.claude/projects"
CWD=$(pwd)
# Look for project directories, find .jsonl files, pick most recent
JSONL_FILE=$(find "$PROJECTS_DIR" -name "*.jsonl" -newer "$PROJECTS_DIR" 2>/dev/null | while read f; do
  head -1 "$f" 2>/dev/null | python3 -c "import json,sys; r=json.load(sys.stdin); cwd=r.get('cwd',''); print(f'$f') if cwd and '$CWD'.startswith(cwd) else None" 2>/dev/null
done | head -1)
```
Or use the session transcript path if available from hook context.

2. Parse and upload:
```bash
SESSION_ID=$(basename "$JSONL_FILE" .jsonl)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/parse-sessions.py" "$JSONL_FILE" --session-id "$SESSION_ID" > /tmp/hoard-parsed.json 2>/tmp/hoard-err.txt
bash "${CLAUDE_PLUGIN_ROOT}/scripts/upload-sessions.sh" /tmp/hoard-parsed.json --check-delta --strict
rm -f /tmp/hoard-parsed.json
```

3. Report the results shown by upload-sessions.sh.

### /hoardinator ingest [scope]

Batch-ingest Claude Code session transcripts.

**Scope options:**
- `(no argument)` -- all sessions for the current repo/project
- `all` -- all sessions across all repos on this machine
- `YYYY-MM-DD` -- sessions modified on a specific date

**Implementation steps:**

1. Find JSONL files based on scope:
```bash
PROJECTS_DIR="$HOME/.claude/projects"

# Current repo: find project dir matching cwd, list its .jsonl files
# All: find "$PROJECTS_DIR" -name "*.jsonl"
# Date: find "$PROJECTS_DIR" -name "*.jsonl" and filter by modification date
```

2. For each JSONL file found:
```bash
SESSION_ID=$(basename "$JSONL_FILE" .jsonl)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/parse-sessions.py" "$JSONL_FILE" --session-id "$SESSION_ID" > /tmp/hoard-parsed.json 2>/tmp/hoard-err.txt
bash "${CLAUDE_PLUGIN_ROOT}/scripts/upload-sessions.sh" /tmp/hoard-parsed.json --check-delta --strict
rm -f /tmp/hoard-parsed.json
```

3. Report aggregate results: total sessions processed, skipped (already up to date), messages ingested.

### /hoardinator status

Show ingestion status and recent sessions.

**Implementation steps:**

1. Query recent sessions:
```bash
curl -s "${SUPABASE_URL}/rest/v1/sessions?select=session_id,repo,app_name,total_messages,total_tool_calls,session_date,ingested_at&order=ingested_at.desc&limit=10" \
  -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}"
```

2. Query totals:
```bash
curl -s -D - -o /dev/null "${SUPABASE_URL}/rest/v1/sessions?select=session_id" \
  -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Prefer: count=exact" \
  -H "Range: 0-0"
# Extract total from Content-Range header
```

3. Format as a table:
```
Hoardinator Status:
  Total sessions: 19
  Total messages: 3,931
  Total tool calls: 2,034

Recent sessions:
  Session                              App           Messages  Tools   Date
  proof-test-xscore-triangle           xscore-sand.  1074      544     2026-02-21
  ...
```

## Hooks

The Hoardinator includes two automatic hooks:

- **SessionStart** (`query-hoardinator.sh`): Shows a status line if this project has ingested sessions
- **PreCompact** (`save-learnings.sh`): Auto-ingests the current session before context compaction

Both hooks degrade silently if Supabase credentials are not configured.

## Schema

### sessions
One row per conversation. Tracks message/tool counts, token usage, models used, git branches, security flags, and ingestion timestamps.

### messages
One row per conversational unit. Types: text, thinking, tool_result, system, compaction_summary. Unique on (session_id, message_index).

### tool_calls
One row per tool invocation. Classified into 10 categories: file, bash, agent, web, interaction, skill, todo, tool_search, plugin, other. Tracks security flags, agent metadata, and execution details. Unique on (session_id, call_index).
