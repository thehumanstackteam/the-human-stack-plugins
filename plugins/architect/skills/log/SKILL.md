---
name: log
description: Log the current Claude Code session into the Session Hoardinator database (sessions, messages, tool_calls tables in Supabase)
triggers:
  - /log
  - log this session
  - hoardinator log
---

# Log Session

Ingest the current Claude Code session into the Session Hoardinator database.
Parses the active JSONL transcript and uploads messages, tool calls, and
session-level statistics to Supabase.

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
/log
```

Say `/log` or "log this session" at any point during a conversation.

## What It Does

1. Locates the current session's JSONL file in `~/.claude/projects/`
2. Parses it with `${CLAUDE_PLUGIN_ROOT}/scripts/parse-sessions.py`:
   - Ordered via linked-list traversal (`parentUuid`)
   - Extracts: user messages, assistant text, thinking blocks, tool results, tool calls
   - Classifies tool calls into 10 categories (file, bash, agent, plugin, web, interaction, todo, tool_search, skill, other)
   - Detects security flags (destructive commands, sensitive files, secret exposure)
   - Generates dollar-quoted SQL INSERT statements in 40-statement batches
3. Uploads SQL batches to Supabase via `${CLAUDE_PLUGIN_ROOT}/scripts/upload-sessions.sh`
4. Uses `ON CONFLICT ... DO NOTHING` for messages and tool calls — safe to run multiple
   times during a session; only new content is added each time

## Implementation Steps

1. Check that `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set:
   ```bash
   if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
     echo "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
     echo "See plugins/architect/skills/log/SKILL.md for setup instructions."
     exit 1
   fi
   ```

2. Create a temp output directory:
   ```bash
   OUTDIR=$(mktemp -d /tmp/hoardinator-XXXXXX)
   ```

3. Run the parser (automatically finds the current repo's active session):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/parse-sessions.py" \
     --output "$OUTDIR"
   ```

4. Upload to Supabase:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/upload-sessions.sh" "$OUTDIR"
   ```

5. Clean up and report results:
   ```bash
   rm -rf "$OUTDIR"
   ```
   Report: "Logged: N messages, M tool calls, K thinking blocks"

## Example Output

```
Session Hoardinator — /log

  Processing abc123-def456.jsonl ... 47 messages, 32 tool calls

Session Hoardinator parse complete:
  Sessions processed : 1
  Sessions skipped   : 0 (empty)
  Total messages     : 47
  Total tool calls   : 32
  SQL files written  : 3
  Output directory   : /tmp/hoardinator-abc123

Session Hoardinator upload:
  Project ref  : hdhmwaldvzxwhimoemap
  SQL files    : 3

  ✓ abc123-def456_001.sql
  ✓ abc123-def456_002.sql
  ✓ abc123-def456_003.sql

Upload complete:
  ✓ Succeeded : 3
  ✗ Failed    : 0

Session logged ✓
  Messages    : 47
  Tool calls  : 32
  Thinking    : 5 blocks
  Session ID  : abc123-def456
```
