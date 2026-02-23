#!/bin/bash
# plugins/architect/hooks/query-hoardinator.sh
# SessionStart hook — query past learnings from Session Hoardinator
#
# Prerequisites:
#   - Supabase plugin installed in Claude Code
#   - Architect plugin initialized (docs/architect/ exists in project)
#
# This hook outputs instructions for Claude to query session_embeddings
# via the Supabase MCP tool. No API keys are read here — authentication
# is handled by the already-configured Supabase MCP connection.
#
# Silently exits (exit 0) if:
#   - No project directory detected
#   - Architect is not initialized (docs/architect/ missing)
#   - Supabase MCP is not configured in .mcp.json or ~/.claude/mcp.json
#   - Repo namespace cannot be derived from git remote

input=$(cat)
project_dir=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null)

# Silently exit if not in a project
if [ -z "$project_dir" ]; then
    exit 0
fi

# Silently exit if Architect is not initialized
if [ ! -d "$project_dir/docs/architect" ]; then
    exit 0
fi

# Check if Supabase MCP is configured (project-level or user-level)
SUPABASE_CONFIGURED=false

check_supabase_mcp() {
    local cfg="$1"
    if [ -f "$cfg" ] && grep -q '"supabase"' "$cfg" 2>/dev/null; then
        SUPABASE_CONFIGURED=true
    fi
}

check_supabase_mcp "$project_dir/.mcp.json"
check_supabase_mcp "$HOME/.claude/mcp.json"

if [ "$SUPABASE_CONFIGURED" = false ]; then
    # Supabase plugin not configured — skip silently
    exit 0
fi

# Derive repo namespace from git remote
REPO=$(git -C "$project_dir" remote get-url origin 2>/dev/null \
    | sed 's|.*github\.com[:/]||;s|\.git$||')

# Silently exit if we cannot determine the repo namespace
if [ -z "$REPO" ]; then
    exit 0
fi

# Output additionalContext instructing Claude to query via Supabase MCP
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Session Hoardinator: Retrieve recent learnings for $REPO.\n\nUsing the Supabase MCP tool, run this query:\n\nSELECT layer, sublayer, content, created_at\nFROM session_embeddings\nWHERE repo = '$REPO'\n  AND layer IN ('user', 'project', 'task')\nORDER BY created_at DESC\nLIMIT 10;\n\nIf results exist, briefly surface the most relevant learnings as context for this session. If the Supabase MCP returns an error or is unavailable, skip silently and continue without interrupting the session."
  }
}
EOF

exit 0
