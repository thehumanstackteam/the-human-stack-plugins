#!/bin/bash
# plugins/architect/hooks/save-learnings.sh
# PreCompact hook — save learnings before context compression
#
# Prerequisites:
#   - Supabase plugin installed in Claude Code
#   - Architect plugin initialized (docs/architect/ exists in project)
#
# This hook outputs instructions for Claude to classify and insert learnings
# into session_embeddings via the Supabase MCP tool before context is compacted.
# No API keys are read here — authentication is handled by the MCP connection.
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

ORG=$(echo "$REPO" | cut -d'/' -f1)

# Output additionalContext instructing Claude to save learnings via Supabase MCP
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreCompact",
    "additionalContext": "Session Hoardinator: Save learnings before compaction for $REPO.\n\nBefore this context is compressed, identify 3-5 key learnings from this session and save them using the Supabase MCP tool.\n\nFor each learning, insert a row:\n\n  INSERT INTO session_embeddings (repo, org, layer, sublayer, content)\n  VALUES ('$REPO', '$ORG', '<layer>', '<sublayer>', '<learning text>');\n\nLayer guide:\n  user    -> patterns, preferences, mistakes, learnings (how you work)\n  product -> architecture, design, domain (stable system knowledge)\n  project -> decisions, state (current feature context)\n  plan    -> strategy, steps (implementation approaches)\n  task    -> implementation, debugging (how specific work was executed)\n\nOnly insert if there are meaningful, reusable learnings. If the Supabase MCP is unavailable or returns an error, skip silently and allow compaction to proceed."
  }
}
EOF

exit 0
