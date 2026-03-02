#!/bin/bash
# save-learnings.sh - PreCompact hook
# Auto-ingests the current session into Supabase before context compaction.
# Exits silently (exit 0) if prerequisites not met or on any failure.

input=$(cat)
project_dir=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null)
transcript_path=$(echo "$input" | jq -r '.transcript_path // empty' 2>/dev/null)

if [ -z "$project_dir" ]; then exit 0; fi
if [ -z "$transcript_path" ]; then exit 0; fi
if [ ! -f "$transcript_path" ]; then exit 0; fi
if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then exit 0; fi

session_id=$(basename "$transcript_path" .jsonl)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

tmpfile=$(mktemp /tmp/hoard-XXXXXX.json)
if python3 "$PLUGIN_ROOT/scripts/parse-sessions.py" "$transcript_path" --session-id "$session_id" > "$tmpfile" 2>/tmp/hoardinator-debug.log; then
  if bash "$PLUGIN_ROOT/scripts/upload-sessions.sh" "$tmpfile" --check-delta 2>>/tmp/hoardinator-debug.log; then
    msg_count=$(jq '.messages | length' "$tmpfile" 2>/dev/null)
    echo "Hoardinator: ingested ${msg_count:-0} messages from this session."
  fi
fi
rm -f "$tmpfile"
exit 0
