#!/bin/bash
# query-hoardinator.sh - SessionStart hook
# Injects a light status line if Hoardinator has data for this project.
# Exits silently (exit 0) if prerequisites not met.

input=$(cat)
project_dir=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null)

if [ -z "$project_dir" ]; then exit 0; fi
if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then exit 0; fi

app_name=$(basename "$project_dir")
response=$(curl -s "${SUPABASE_URL}/rest/v1/sessions?app_name=eq.${app_name}&select=session_id,total_messages,ingested_at&order=ingested_at.desc&limit=1" \
  -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" 2>/dev/null)

count=$(echo "$response" | jq 'length' 2>/dev/null)
if [ "${count:-0}" = "0" ] || [ -z "$count" ]; then exit 0; fi

last_date=$(echo "$response" | jq -r '.[0].ingested_at // empty' 2>/dev/null)
total_msgs=$(echo "$response" | jq -r '.[0].total_messages // 0' 2>/dev/null)

if [ -n "$last_date" ]; then
  echo "Session Hoardinator active. Last ingested: ${last_date} (${total_msgs} messages). Run /hoardinator status for details."
fi
exit 0
