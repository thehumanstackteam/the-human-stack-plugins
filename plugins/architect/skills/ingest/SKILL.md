---
name: ingest
description: Batch-ingest Claude Code JSONL session transcripts into the Session Hoardinator database (Supabase sessions, messages, tool_calls tables)
triggers:
  - /ingest
  - hoardinator ingest
---

# Ingest Sessions

Batch-sweep and ingest Claude Code session transcripts into the Session
Hoardinator database. Processes all JSONL files from `~/.claude/projects/`,
scoped by repo, date, or all machines.

## Prerequisites

This skill requires:

1. **Supabase plugin installed** — the Supabase MCP server must be configured
   in Claude Code (check `.mcp.json` or `~/.claude/mcp.json` for a `supabase` entry)

2. **Architect plugin initialized** — `docs/architect/` must exist in the project
   (run `/architect init` if not already done)

3. **Environment variables set**:
   - `SUPABASE_URL` — your Supabase project URL, e.g. `https://hdhmwaldvzxwhimoemap.supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY` — service role key from Supabase → Settings → API

If either env var is missing, the script will exit with a clear error message
explaining what to set and where to find the values.

## Usage

```
/ingest                    # All sessions for the current repo
/ingest all                # All sessions across all repos on this machine
/ingest 2026-02-23         # Sessions from a specific date (YYYY-MM-DD)
```

## What It Does

1. Scans `~/.claude/projects/` for `.jsonl` session files (scoped by usage)
2. For each file, parses via `parse-sessions.py`:
   - Linked-list traversal to establish message ordering
   - Extracts messages (text, thinking, tool_result, system, compaction)
   - Classifies tool calls (10 categories) and detects security flags
   - Filters empty sessions (0 messages and 0 tool calls)
3. Generates batched dollar-quoted SQL INSERT statements (40 per file)
4. Uploads to Supabase via `upload-sessions.sh`
5. `ON CONFLICT` clauses make every run idempotent — re-running produces no duplicates

## Implementation Steps

1. Check that `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set:
   ```bash
   if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
     echo "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
     echo "See plugins/architect/skills/ingest/SKILL.md for setup instructions."
     exit 1
   fi
   ```

2. Parse the user's intent from the trigger phrase:
   - `/ingest` → current repo (no extra flags)
   - `/ingest all` → pass `--all` to the parser
   - `/ingest 2026-02-23` → pass `--date 2026-02-23` to the parser

3. Create a temp output directory:
   ```bash
   OUTDIR=$(mktemp -d /tmp/hoardinator-XXXXXX)
   ```

4. Run the parser with the appropriate scope flag:
   ```bash
   # Current repo
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/parse-sessions.py" \
     --output "$OUTDIR"

   # All repos
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/parse-sessions.py" \
     --all --output "$OUTDIR"

   # Specific date
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/parse-sessions.py" \
     --date 2026-02-23 --output "$OUTDIR"
   ```

5. Upload to Supabase:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/upload-sessions.sh" "$OUTDIR"
   ```

6. Clean up and report:
   ```bash
   rm -rf "$OUTDIR"
   ```

## Example Output

```
Session Hoardinator — /ingest

  Processing 2026-02-23-abc123.jsonl ... 89 messages, 67 tool calls
  Processing 2026-02-23-def456.jsonl ... 12 messages, 8 tool calls
  Processing 2026-02-22-ghi789.jsonl ... skipped (empty)

Session Hoardinator parse complete:
  Sessions processed : 2
  Sessions skipped   : 1 (empty)
  Total messages     : 101
  Total tool calls   : 75
  SQL files written  : 6

Session Hoardinator upload:
  Project ref  : hdhmwaldvzxwhimoemap
  SQL files    : 6

  ✓ 2026-02-23-abc123_001.sql
  ✓ 2026-02-23-abc123_002.sql
  ...

Upload complete:
  ✓ Succeeded : 6
  ✗ Failed    : 0

Ingestion complete ✓
  Sessions ingested  : 2
  Sessions skipped   : 1 (empty)
  Total messages     : 101
  Total tool calls   : 75
```
