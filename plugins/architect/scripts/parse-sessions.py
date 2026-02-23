#!/usr/bin/env python3
"""
parse-sessions.py — Claude Code JSONL session parser for Session Hoardinator

Parses Claude Code session JSONL files and generates batched PostgreSQL
INSERT statements for upload to Supabase via upload-sessions.sh.

Prerequisites:
  - Architect plugin initialized (docs/architect/ exists in project)
  - Supabase plugin installed in Claude Code
  - SUPABASE_URL environment variable set
  - SUPABASE_SERVICE_ROLE_KEY environment variable set

Usage:
  # Dry run — prints counts, skips credential check, writes no files
  python3 parse-sessions.py --dry-run

  # Current repo's sessions
  python3 parse-sessions.py --output /tmp/hoardinator-sql/

  # Specific session by UUID
  python3 parse-sessions.py --session <uuid> --output /tmp/hoardinator-sql/

  # All sessions across all repos
  python3 parse-sessions.py --all --output /tmp/hoardinator-sql/

  # Sessions from a specific date
  python3 parse-sessions.py --date 2026-02-23 --output /tmp/hoardinator-sql/
"""

import os
import sys
import json
import argparse
import subprocess
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Constants ────────────────────────────────────────────────────────────────

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
BATCH_SIZE = 40  # INSERT statements per SQL file

# ── Tool Classification ───────────────────────────────────────────────────────

FILE_TOOLS = {
    "Read", "Write", "Edit", "MultiEdit", "Glob", "LS",
    "NotebookRead", "NotebookEdit", "View", "Create",
}
BASH_TOOLS = {"Bash"}
AGENT_TOOLS = {"Task", "TaskOutput", "TaskUpdate", "TaskGet", "TaskList"}
WEB_TOOLS = {"WebFetch", "WebSearch", "web_fetch", "web_search"}
INTERACTION_TOOLS = {"AskUserQuestion", "AskFollowupQuestion"}
TODO_TOOLS = {"TodoAdd", "TodoRead", "TodoUpdate", "TodoRemove"}
TOOL_SEARCH_TOOLS = {"ToolSearch"}

# ── Security Patterns ─────────────────────────────────────────────────────────

DESTRUCTIVE_PATTERNS = [
    re.compile(r"\brm\s+-[rf]{1,2}\b"),
    re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\b", re.IGNORECASE),
    re.compile(r"--force\b"),
    re.compile(r"\bgit\s+reset\s+--hard\b"),
    re.compile(r"\bgit\s+push\s+--force\b"),
    re.compile(r"\bDELETE\s+FROM\b.{0,80}\bWHERE\s+1\s*=\s*1\b", re.IGNORECASE),
]
SENSITIVE_FILE_PATTERNS = [
    re.compile(r"\.env\b"),
    re.compile(r"\.pem\b"),
    re.compile(r"\bid_rsa\b"),
    re.compile(r"\.key\b"),
    re.compile(r"\bcredentials\b", re.IGNORECASE),
    re.compile(r"\bsecrets?\b", re.IGNORECASE),
    re.compile(r"\.token\b"),
    re.compile(r"\.p12\b"),
    re.compile(r"\.pfx\b"),
]
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|apikey)\s*[=:\"']+\s*[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(?i)(secret[_-]?key)\s*[=:\"']+\s*[A-Za-z0-9_\-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{40,}"),
    re.compile(r"eyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}"),
]

# ── Prerequisite Check ────────────────────────────────────────────────────────


def check_prerequisites(dry_run=False):
    """Verify required environment and tools are available. Exit with help if not."""
    errors = []

    if not dry_run:
        if not os.environ.get("SUPABASE_URL"):
            errors.append("SUPABASE_URL is not set")
        if not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
            errors.append("SUPABASE_SERVICE_ROLE_KEY is not set")

    if not CLAUDE_PROJECTS_DIR.exists():
        errors.append(
            f"Claude projects directory not found: {CLAUDE_PROJECTS_DIR}\n"
            "  Claude Code must be installed and at least one session must exist."
        )

    if errors:
        print("Session Hoardinator: Prerequisites not met:\n", file=sys.stderr)
        for err in errors:
            print(f"  \u2717 {err}", file=sys.stderr)
        print(
            "\nSetup required:\n"
            "  1. Install the Supabase plugin in Claude Code\n"
            "  2. Set SUPABASE_URL=https://<project-ref>.supabase.co\n"
            "  3. Set SUPABASE_SERVICE_ROLE_KEY=<service-role-key>\n"
            "     (found in Supabase dashboard: Settings \u2192 API \u2192 service_role)\n"
            "  4. Run /architect init if not already done\n"
            "  Use --dry-run to preview session counts without uploading.",
            file=sys.stderr,
        )
        sys.exit(1)


# ── PostgreSQL Helpers ────────────────────────────────────────────────────────


def dollar_quote(s, label="HOARD"):
    """Wrap a string in PostgreSQL dollar-quoting. Finds a safe delimiter."""
    if s is None:
        return "NULL"
    s = str(s)
    for n in range(100):
        delim = "${}{}$".format(label, n if n else "")
        if delim not in s:
            return "{}{}{}".format(delim, s, delim)
    # Last-resort: strip all dollar signs (extremely rare)
    return "$HOARD${}$HOARD$".format(s.replace("$", ""))


def pg_bool(v):
    if v is None:
        return "NULL"
    return "TRUE" if v else "FALSE"


def pg_int(v):
    if v is None:
        return "NULL"
    try:
        return str(int(v))
    except (TypeError, ValueError):
        return "NULL"


def pg_text(v):
    if v is None:
        return "NULL"
    return dollar_quote(str(v))


def pg_array(lst):
    """Convert a Python list to a PostgreSQL text array literal."""
    if not lst:
        return "'{}'::text[]"
    return "ARRAY[{}]::text[]".format(", ".join(dollar_quote(str(x)) for x in lst))


def truncate(s, max_len=2000):
    if not s:
        return s
    return s[:max_len] if len(s) > max_len else s


# ── Git / Namespace ───────────────────────────────────────────────────────────


def get_git_info():
    """Return (repo, org, author) from git config and remote."""
    repo, org, author = None, None, "unknown"
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], stderr=subprocess.DEVNULL
        ).decode().strip()
        repo = re.sub(r".*github\.com[:/]", "", url)
        repo = re.sub(r"\.git$", "", repo)
        org = repo.split("/")[0] if "/" in repo else repo
    except Exception:
        pass
    try:
        author = subprocess.check_output(
            ["git", "config", "user.name"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        pass
    return repo, org, author


def get_environment():
    """Detect the runtime environment."""
    if os.environ.get("CODESPACE_NAME"):
        return "codespace"
    if os.environ.get("REPL_ID"):
        return "replit"
    return "local"


# ── JSONL File Discovery ──────────────────────────────────────────────────────


def find_project_jsonl_dir():
    """Find the ~/.claude/projects/<hash> dir for the current working directory."""
    cwd = str(Path.cwd())
    if not CLAUDE_PROJECTS_DIR.exists():
        return None
    # Sort by most-recently modified so we find the right project quickly
    dirs = sorted(
        (d for d in CLAUDE_PROJECTS_DIR.iterdir() if d.is_dir()),
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for proj_dir in dirs:
        for jsonl_file in proj_dir.glob("*.jsonl"):
            try:
                with open(jsonl_file, encoding="utf-8", errors="replace") as fh:
                    line = fh.readline()
                if line:
                    record = json.loads(line)
                    file_cwd = record.get("cwd", "")
                    if file_cwd and (
                        file_cwd == cwd or file_cwd.startswith(cwd + "/")
                    ):
                        return proj_dir
            except Exception:
                pass
    return None


def find_jsonl_files(args):
    """Find JSONL files to process based on CLI arguments."""
    files = []

    if args.session:
        for proj_dir in CLAUDE_PROJECTS_DIR.iterdir():
            if not proj_dir.is_dir():
                continue
            candidate = proj_dir / "{}.jsonl".format(args.session)
            if candidate.exists():
                files.append(candidate)
                break
        if not files:
            print("Session not found: {}".format(args.session), file=sys.stderr)

    elif getattr(args, "all_repos", False):
        for proj_dir in sorted(CLAUDE_PROJECTS_DIR.iterdir()):
            if proj_dir.is_dir():
                files.extend(sorted(proj_dir.glob("*.jsonl")))

    elif args.date:
        target = args.date
        for proj_dir in CLAUDE_PROJECTS_DIR.iterdir():
            if not proj_dir.is_dir():
                continue
            for f in proj_dir.glob("*.jsonl"):
                mod_date = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
                if mod_date == target:
                    files.append(f)

    else:
        proj_dir = find_project_jsonl_dir()
        if proj_dir:
            files.extend(sorted(proj_dir.glob("*.jsonl")))
        else:
            print(
                "No Claude sessions found for current directory.\n"
                "Use --all to ingest sessions across all repos.",
                file=sys.stderr,
            )

    return files


# ── JSONL Parsing ─────────────────────────────────────────────────────────────


def order_records(records):
    """Order records via parentUuid linked-list traversal."""
    valid = [r for r in records if r.get("uuid")]
    if not valid:
        return records

    by_uuid = {r["uuid"]: r for r in valid}
    children = defaultdict(list)
    roots = []

    for r in valid:
        parent = r.get("parentUuid")
        if parent and parent in by_uuid:
            children[parent].append(r)
        else:
            roots.append(r)

    roots.sort(key=lambda x: x.get("timestamp", ""))
    for k in children:
        children[k].sort(key=lambda x: x.get("timestamp", ""))

    ordered = []

    def walk(r):
        ordered.append(r)
        for child in children.get(r["uuid"], []):
            walk(child)

    for root in roots:
        walk(root)

    return ordered


def classify_tool(tool_name):
    """Classify a tool name into one of 10 categories."""
    if tool_name in FILE_TOOLS:
        return "file"
    if tool_name in BASH_TOOLS:
        return "bash"
    if tool_name in AGENT_TOOLS:
        return "agent"
    if tool_name in WEB_TOOLS:
        return "web"
    if tool_name in INTERACTION_TOOLS:
        return "interaction"
    if tool_name in TODO_TOOLS:
        return "todo"
    if tool_name in TOOL_SEARCH_TOOLS:
        return "tool_search"
    if tool_name.startswith("mcp__"):
        return "plugin"
    if tool_name.startswith("skill__") or ":" in tool_name:
        return "skill"
    return "other"


def extract_plugin_name(tool_name):
    """Extract the plugin name from an mcp__* tool name."""
    if not tool_name.startswith("mcp__"):
        return None
    parts = tool_name[5:].split("__")
    if not parts:
        return None
    p = parts[0]
    if p.startswith("plugin_"):
        p = p[7:]
    segments = p.split("_")
    return segments[-1] if segments else p


def detect_security(text):
    """Return (flags, is_destructive, is_sensitive_file, has_secret_exposure)."""
    flags = []
    if not text:
        return flags, False, False, False

    is_destructive = any(pat.search(text) for pat in DESTRUCTIVE_PATTERNS)
    is_sensitive = any(pat.search(text) for pat in SENSITIVE_FILE_PATTERNS)
    has_secret = any(pat.search(text) for pat in SECRET_PATTERNS)

    if is_destructive:
        flags.append("destructive_command")
    if is_sensitive:
        flags.append("sensitive_file")
    if has_secret:
        flags.append("secret_exposure")

    return flags, is_destructive, is_sensitive, has_secret


def parse_tool_use_result(record):
    """Extract success/failure metadata from a user record's toolUseResult field."""
    result = record.get("toolUseResult")
    defaults = dict(
        success=None,
        was_rejected=False,
        exit_code=None,
        error_type=None,
        error_message=None,
        was_interrupted=False,
        was_truncated=False,
        duration_ms=None,
        agent_id=None,
        agent_tokens=None,
        agent_tool_count=None,
        agent_duration_ms=None,
        background_task_id=None,
    )
    if result is None:
        return defaults

    out = dict(defaults)

    if isinstance(result, str):
        if "rejected" in result.lower():
            out.update(was_rejected=True, success=False, error_type="rejected", error_message=result)
        else:
            out["success"] = True

    elif isinstance(result, dict):
        if "success" in result:
            out["success"] = bool(result["success"])
        out["was_interrupted"] = bool(result.get("interrupted", False))
        out["was_truncated"] = bool(result.get("truncated", False))
        out["duration_ms"] = result.get("durationMs")
        for key in ("returnCode", "exitCode"):
            if key in result:
                try:
                    out["exit_code"] = int(result[key])
                    if out["success"] is None:
                        out["success"] = out["exit_code"] == 0
                except (TypeError, ValueError):
                    pass
        out["agent_id"] = result.get("agentId")
        out["agent_tokens"] = result.get("totalTokens")
        out["agent_tool_count"] = result.get("totalToolUseCount")
        out["agent_duration_ms"] = result.get("totalDurationMs")
        out["background_task_id"] = result.get("backgroundTaskId")
        if out["success"] is None:
            out["success"] = True

    elif isinstance(result, list):
        out["success"] = True

    return out


# ── Core Parser ───────────────────────────────────────────────────────────────


def parse_jsonl_file(path, repo, org, author, environment):
    """
    Parse a single JSONL session file.
    Returns (session_dict, messages_list, tool_calls_list) or None if empty.
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw_records = [json.loads(line) for line in fh if line.strip()]
    except (json.JSONDecodeError, OSError) as exc:
        print("  \u2717 Failed to read {}: {}".format(path, exc), file=sys.stderr)
        return None

    if not raw_records:
        return None

    records = order_records(raw_records)
    session_id = path.stem

    # Session-level aggregators
    session_date = None
    first_ts = None
    last_ts = None
    claude_version = None
    model = None
    models_used = set()
    git_branches = set()
    permission_modes = set()
    agents_used = set()
    plugins_used = set()
    skills_used = set()
    security_flags = set()
    has_continuation = False
    compaction_count = 0
    session_cwd = None

    # Counts
    total_user = 0
    total_assistant = 0
    total_thinking = 0
    total_tool_results = 0
    total_system = 0
    total_tool_calls = 0
    total_failures = 0
    total_rejections = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_read = 0
    total_cache_creation = 0
    total_thinking_chars = 0
    app_tool_calls = 0
    infra_tool_calls = 0
    sensitive_files_touched = 0
    destructive_commands = 0

    messages = []
    tool_calls = []
    message_index = 0
    call_index = 0

    # tool_use_id -> tool_call dict (pending result)
    pending_tool_uses = {}

    def _new_msg(role, msg_type, content, **kwargs):
        nonlocal message_index
        base = dict(
            session_id=session_id,
            message_index=message_index,
            role=role,
            message_type=msg_type,
            content=truncate(content),
            thinking_length=None,
            model=None,
            input_tokens=None,
            output_tokens=None,
            cache_read_tokens=None,
            cache_creation_tokens=None,
            permission_mode=None,
            git_branch=None,
            is_compaction_summary=False,
            tool_use_id=None,
            is_error=False,
            tool_call_count=0,
            tool_failure_count=0,
            created_at=None,
        )
        base.update(kwargs)
        messages.append(base)
        message_index += 1

    for record in records:
        rtype = record.get("type", "")
        ts = record.get("timestamp")
        version = record.get("version")
        branch = record.get("gitBranch")
        perm_mode = record.get("permissionMode")

        if ts:
            if first_ts is None:
                first_ts = ts
            last_ts = ts
            if session_date is None:
                session_date = ts[:10]

        if version and not claude_version:
            claude_version = version
        if branch:
            git_branches.add(branch)
        if perm_mode:
            permission_modes.add(perm_mode)
        if session_cwd is None:
            cwd_val = record.get("cwd")
            if cwd_val:
                session_cwd = cwd_val

        if rtype not in ("user", "assistant", "system"):
            continue

        common = dict(permission_mode=perm_mode, git_branch=branch, created_at=ts)

        # ── System ────────────────────────────────────────────────────────────
        if rtype == "system":
            subtype = record.get("subtype", "")
            content_text = record.get("content", "")
            msg_type = "system"
            if record.get("compactMetadata") or "compact" in subtype.lower():
                msg_type = "compaction_summary"
                compaction_count += 1
                has_continuation = True
            total_system += 1
            _new_msg("system", msg_type, content_text, is_compaction_summary=(msg_type == "compaction_summary"), **common)
            continue

        # ── User ──────────────────────────────────────────────────────────────
        if rtype == "user":
            if record.get("isCompactSummary"):
                has_continuation = True

            msg_content = record.get("message", {}).get("content", "")

            if isinstance(msg_content, str) and msg_content.strip():
                total_user += 1
                _new_msg("user", "text", msg_content, **common)

            elif isinstance(msg_content, list):
                for block in msg_content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_result":
                        tool_use_id = block.get("tool_use_id")
                        is_error = bool(block.get("is_error", False))
                        rc = block.get("content", "")
                        result_text = (
                            " ".join(c.get("text", "") for c in rc if isinstance(c, dict))
                            if isinstance(rc, list)
                            else str(rc) if rc else ""
                        )
                        total_tool_results += 1
                        _new_msg("user", "tool_result", result_text,
                                 tool_use_id=tool_use_id, is_error=is_error, **common)

                        if tool_use_id and tool_use_id in pending_tool_uses:
                            tc = pending_tool_uses.pop(tool_use_id)
                            if is_error:
                                tc["success"] = False
                                tc["error_type"] = "exit_code"
                                tc["error_message"] = truncate(result_text, 500)
                                total_failures += 1
                            else:
                                tc["success"] = True

            # Also check top-level toolUseResult for result metadata
            src_id = record.get("sourceToolUseID")
            if src_id and src_id in pending_tool_uses:
                meta = parse_tool_use_result(record)
                tc = pending_tool_uses.pop(src_id)
                tc.update({k: v for k, v in meta.items() if v is not None or tc.get(k) is None})
                if meta["was_rejected"]:
                    total_rejections += 1
            continue

        # ── Assistant ─────────────────────────────────────────────────────────
        if rtype == "assistant":
            msg = record.get("message", {})
            msg_model = msg.get("model", "")
            usage = msg.get("usage", {})
            input_toks = usage.get("input_tokens", 0) or 0
            output_toks = usage.get("output_tokens", 0) or 0
            cache_read = usage.get("cache_read_input_tokens", 0) or 0
            cache_create = usage.get("cache_creation_input_tokens", 0) or 0

            if msg_model:
                if not model:
                    model = msg_model
                models_used.add(msg_model)

            total_input_tokens += input_toks
            total_output_tokens += output_toks
            total_cache_read += cache_read
            total_cache_creation += cache_create

            content_blocks = msg.get("content", [])
            if not isinstance(content_blocks, list):
                content_blocks = []

            for block in content_blocks:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type", "")

                if btype == "text":
                    total_assistant += 1
                    _new_msg("assistant", "text", block.get("text", ""),
                             model=msg_model,
                             input_tokens=input_toks, output_tokens=output_toks,
                             cache_read_tokens=cache_read, cache_creation_tokens=cache_create,
                             **common)

                elif btype == "thinking":
                    thinking_text = block.get("thinking", "")
                    total_thinking += 1
                    total_thinking_chars += len(thinking_text)
                    _new_msg("assistant", "thinking", thinking_text,
                             thinking_length=len(thinking_text),
                             model=msg_model, **common)

                elif btype == "tool_use":
                    tool_name = block.get("name", "")
                    tool_id = block.get("id", "")
                    tool_input = block.get("input", {})
                    caller = block.get("caller", {})
                    caller_type = caller.get("type", "direct")
                    agent_type_val = caller.get("agentType") or caller.get("name")

                    tool_category = classify_tool(tool_name)
                    plugin_name = (
                        extract_plugin_name(tool_name) if tool_category == "plugin" else None
                    )
                    is_agent = tool_category == "agent"

                    if isinstance(tool_input, dict):
                        input_summary = truncate(
                            tool_input.get("command")
                            or tool_input.get("description")
                            or tool_input.get("file_path")
                            or tool_input.get("query")
                            or str(tool_input)[:500],
                            500,
                        )
                        target_file = tool_input.get("file_path") or tool_input.get("path")
                        raw_url = tool_input.get("url", "")
                        m = re.search(r"https?://([^/]+)", raw_url) if raw_url else None
                        target_domain = m.group(1) if m else (raw_url[:100] if raw_url else None)
                        is_background = bool(tool_input.get("run_in_background", False))
                    else:
                        input_summary = truncate(str(tool_input), 500)
                        target_file = None
                        target_domain = None
                        is_background = False

                    sec_flags, is_dest, is_sens, has_sec = detect_security(input_summary or "")
                    if target_file:
                        _, _, tf_sens, _ = detect_security(str(target_file))
                        if tf_sens:
                            is_sens = True
                            if "sensitive_file" not in sec_flags:
                                sec_flags.append("sensitive_file")

                    if is_dest:
                        destructive_commands += 1
                        security_flags.add("destructive_command")
                    if is_sens:
                        sensitive_files_touched += 1
                    if has_sec:
                        security_flags.add("secret_exposure")

                    infra_cats = {"bash", "file"}
                    if tool_category in infra_cats or plugin_name in {"git", "npm", "docker"}:
                        infra_tool_calls += 1
                    else:
                        app_tool_calls += 1

                    if is_agent and agent_type_val:
                        agents_used.add(str(agent_type_val))
                    if plugin_name:
                        plugins_used.add(plugin_name)

                    total_tool_calls += 1

                    tc = dict(
                        session_id=session_id,
                        call_index=call_index,
                        tool_name=tool_name,
                        tool_category=tool_category,
                        input_summary=input_summary,
                        output_summary=None,
                        success=None,
                        was_rejected=False,
                        was_revision=False,
                        error_type=None,
                        error_message=None,
                        exit_code=None,
                        target_file=str(target_file) if target_file else None,
                        target_domain=target_domain,
                        is_background=is_background,
                        is_agent=is_agent,
                        agent_type=agent_type_val,
                        plugin_name=plugin_name,
                        is_sensitive_file=is_sens,
                        has_secret_exposure=has_sec,
                        is_destructive=is_dest,
                        was_blocked_by_hook=False,
                        security_flags=sec_flags,
                        caller_type=caller_type,
                        was_interrupted=False,
                        was_truncated=False,
                        agent_id=None,
                        agent_tokens=None,
                        agent_tool_count=None,
                        agent_duration_ms=None,
                        background_task_id=None,
                        result_duration_ms=None,
                        duration_ms=None,
                        repo=repo,
                        org=org,
                        session_date=session_date,
                        created_at=ts,
                    )
                    tool_calls.append(tc)
                    if tool_id:
                        pending_tool_uses[tool_id] = tc
                    call_index += 1

    # ── Empty session filter ──────────────────────────────────────────────────
    if len(messages) == 0 and total_tool_calls == 0:
        return None

    # ── Build session row ─────────────────────────────────────────────────────
    app_name = session_cwd.split("/")[-1] if session_cwd else None

    session_row = dict(
        session_id=session_id,
        repo=repo,
        org=org,
        author=author,
        app_name=app_name,
        environment=environment,
        claude_version=claude_version,
        model=model,
        session_date=session_date,
        first_message_at=first_ts,
        last_message_at=last_ts,
        total_messages=len(messages),
        total_user_messages=total_user,
        total_assistant_messages=total_assistant,
        total_thinking_blocks=total_thinking,
        total_tool_results=total_tool_results,
        total_system_events=total_system,
        total_tool_calls=total_tool_calls,
        total_failures=total_failures,
        total_rejections=total_rejections,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        total_cache_read_tokens=total_cache_read,
        total_cache_creation_tokens=total_cache_creation,
        total_thinking_chars=total_thinking_chars,
        app_tool_calls=app_tool_calls,
        infra_tool_calls=infra_tool_calls,
        compaction_count=compaction_count,
        has_continuation=has_continuation,
        agents_used=sorted(agents_used),
        plugins_used=sorted(plugins_used),
        skills_used=sorted(skills_used),
        git_branches=sorted(git_branches),
        permission_modes=sorted(permission_modes),
        models_used=sorted(models_used),
        security_flags=sorted(security_flags),
        sensitive_files_touched=sensitive_files_touched,
        destructive_commands=destructive_commands,
    )

    return session_row, messages, tool_calls


# ── SQL Generation ────────────────────────────────────────────────────────────


def generate_session_sql(s):
    return (
        "INSERT INTO sessions (\n"
        "  session_id, repo, org, author, app_name, environment,\n"
        "  claude_version, model, session_date, first_message_at, last_message_at,\n"
        "  total_messages, total_user_messages, total_assistant_messages,\n"
        "  total_thinking_blocks, total_tool_results, total_system_events,\n"
        "  total_tool_calls, total_failures, total_rejections,\n"
        "  total_input_tokens, total_output_tokens,\n"
        "  total_cache_read_tokens, total_cache_creation_tokens,\n"
        "  total_thinking_chars, app_tool_calls, infra_tool_calls, compaction_count,\n"
        "  has_continuation, agents_used, plugins_used, skills_used,\n"
        "  git_branches, permission_modes, models_used, security_flags,\n"
        "  sensitive_files_touched, destructive_commands, ingested, ingested_at\n"
        ") VALUES (\n"
        "  {session_id}, {repo}, {org}, {author},\n"
        "  {app_name}, {environment},\n"
        "  {claude_version}, {model},\n"
        "  {session_date}, {first_message_at}, {last_message_at},\n"
        "  {total_messages}, {total_user_messages}, {total_assistant_messages},\n"
        "  {total_thinking_blocks}, {total_tool_results}, {total_system_events},\n"
        "  {total_tool_calls}, {total_failures}, {total_rejections},\n"
        "  {total_input_tokens}, {total_output_tokens},\n"
        "  {total_cache_read_tokens}, {total_cache_creation_tokens},\n"
        "  {total_thinking_chars}, {app_tool_calls}, {infra_tool_calls}, {compaction_count},\n"
        "  {has_continuation},\n"
        "  {agents_used}, {plugins_used}, {skills_used},\n"
        "  {git_branches}, {permission_modes}, {models_used}, {security_flags},\n"
        "  {sensitive_files_touched}, {destructive_commands},\n"
        "  TRUE, NOW()\n"
        ")\n"
        "ON CONFLICT (session_id) DO UPDATE SET\n"
        "  last_message_at = EXCLUDED.last_message_at,\n"
        "  total_messages = EXCLUDED.total_messages,\n"
        "  total_user_messages = EXCLUDED.total_user_messages,\n"
        "  total_assistant_messages = EXCLUDED.total_assistant_messages,\n"
        "  total_thinking_blocks = EXCLUDED.total_thinking_blocks,\n"
        "  total_tool_results = EXCLUDED.total_tool_results,\n"
        "  total_system_events = EXCLUDED.total_system_events,\n"
        "  total_tool_calls = EXCLUDED.total_tool_calls,\n"
        "  total_failures = EXCLUDED.total_failures,\n"
        "  total_rejections = EXCLUDED.total_rejections,\n"
        "  total_input_tokens = EXCLUDED.total_input_tokens,\n"
        "  total_output_tokens = EXCLUDED.total_output_tokens,\n"
        "  total_cache_read_tokens = EXCLUDED.total_cache_read_tokens,\n"
        "  total_cache_creation_tokens = EXCLUDED.total_cache_creation_tokens,\n"
        "  total_thinking_chars = EXCLUDED.total_thinking_chars,\n"
        "  app_tool_calls = EXCLUDED.app_tool_calls,\n"
        "  infra_tool_calls = EXCLUDED.infra_tool_calls,\n"
        "  compaction_count = EXCLUDED.compaction_count,\n"
        "  has_continuation = EXCLUDED.has_continuation,\n"
        "  agents_used = EXCLUDED.agents_used,\n"
        "  plugins_used = EXCLUDED.plugins_used,\n"
        "  git_branches = EXCLUDED.git_branches,\n"
        "  permission_modes = EXCLUDED.permission_modes,\n"
        "  models_used = EXCLUDED.models_used,\n"
        "  security_flags = EXCLUDED.security_flags,\n"
        "  sensitive_files_touched = EXCLUDED.sensitive_files_touched,\n"
        "  destructive_commands = EXCLUDED.destructive_commands,\n"
        "  ingested = TRUE,\n"
        "  ingested_at = NOW();"
    ).format(
        session_id=pg_text(s["session_id"]),
        repo=pg_text(s["repo"]),
        org=pg_text(s["org"]),
        author=pg_text(s["author"]),
        app_name=pg_text(s["app_name"]),
        environment=pg_text(s["environment"]),
        claude_version=pg_text(s["claude_version"]),
        model=pg_text(s["model"]),
        session_date=pg_text(s["session_date"]),
        first_message_at=pg_text(s["first_message_at"]),
        last_message_at=pg_text(s["last_message_at"]),
        total_messages=pg_int(s["total_messages"]),
        total_user_messages=pg_int(s["total_user_messages"]),
        total_assistant_messages=pg_int(s["total_assistant_messages"]),
        total_thinking_blocks=pg_int(s["total_thinking_blocks"]),
        total_tool_results=pg_int(s["total_tool_results"]),
        total_system_events=pg_int(s["total_system_events"]),
        total_tool_calls=pg_int(s["total_tool_calls"]),
        total_failures=pg_int(s["total_failures"]),
        total_rejections=pg_int(s["total_rejections"]),
        total_input_tokens=pg_int(s["total_input_tokens"]),
        total_output_tokens=pg_int(s["total_output_tokens"]),
        total_cache_read_tokens=pg_int(s["total_cache_read_tokens"]),
        total_cache_creation_tokens=pg_int(s["total_cache_creation_tokens"]),
        total_thinking_chars=pg_int(s["total_thinking_chars"]),
        app_tool_calls=pg_int(s["app_tool_calls"]),
        infra_tool_calls=pg_int(s["infra_tool_calls"]),
        compaction_count=pg_int(s["compaction_count"]),
        has_continuation=pg_bool(s["has_continuation"]),
        agents_used=pg_array(s["agents_used"]),
        plugins_used=pg_array(s["plugins_used"]),
        skills_used=pg_array(s["skills_used"]),
        git_branches=pg_array(s["git_branches"]),
        permission_modes=pg_array(s["permission_modes"]),
        models_used=pg_array(s["models_used"]),
        security_flags=pg_array(s["security_flags"]),
        sensitive_files_touched=pg_int(s["sensitive_files_touched"]),
        destructive_commands=pg_int(s["destructive_commands"]),
    )


def generate_message_sql(m):
    tl = m.get("thinking_length")
    return (
        "INSERT INTO messages (\n"
        "  session_id, message_index, role, message_type, content,\n"
        "  thinking_length, model,\n"
        "  input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens,\n"
        "  permission_mode, git_branch, is_compaction_summary,\n"
        "  tool_use_id, is_error, tool_call_count, tool_failure_count, created_at\n"
        ") VALUES (\n"
        "  {session_id}, {message_index}, {role}, {message_type}, {content},\n"
        "  {thinking_length}, {model},\n"
        "  {input_tokens}, {output_tokens}, {cache_read_tokens}, {cache_creation_tokens},\n"
        "  {permission_mode}, {git_branch}, {is_compaction_summary},\n"
        "  {tool_use_id}, {is_error}, {tool_call_count}, {tool_failure_count}, {created_at}\n"
        ")\n"
        "ON CONFLICT (session_id, message_index) DO NOTHING;"
    ).format(
        session_id=pg_text(m["session_id"]),
        message_index=pg_int(m["message_index"]),
        role=pg_text(m["role"]),
        message_type=pg_text(m["message_type"]),
        content=pg_text(m["content"]),
        thinking_length=pg_int(tl) if tl is not None else "NULL",
        model=pg_text(m["model"]),
        input_tokens=pg_int(m["input_tokens"]),
        output_tokens=pg_int(m["output_tokens"]),
        cache_read_tokens=pg_int(m["cache_read_tokens"]),
        cache_creation_tokens=pg_int(m["cache_creation_tokens"]),
        permission_mode=pg_text(m["permission_mode"]),
        git_branch=pg_text(m["git_branch"]),
        is_compaction_summary=pg_bool(m["is_compaction_summary"]),
        tool_use_id=pg_text(m["tool_use_id"]),
        is_error=pg_bool(m["is_error"]),
        tool_call_count=pg_int(m["tool_call_count"]),
        tool_failure_count=pg_int(m["tool_failure_count"]),
        created_at=pg_text(m["created_at"]),
    )


def generate_tool_call_sql(tc):
    return (
        "INSERT INTO tool_calls (\n"
        "  session_id, call_index, tool_name, tool_category,\n"
        "  input_summary, output_summary,\n"
        "  success, was_rejected, was_revision,\n"
        "  error_type, error_message, exit_code,\n"
        "  target_file, target_domain,\n"
        "  is_background, is_agent, agent_type, plugin_name,\n"
        "  is_sensitive_file, has_secret_exposure, is_destructive, was_blocked_by_hook,\n"
        "  security_flags, caller_type, was_interrupted, was_truncated,\n"
        "  agent_id, agent_tokens, agent_tool_count, agent_duration_ms,\n"
        "  background_task_id, result_duration_ms, duration_ms,\n"
        "  repo, org, session_date, created_at\n"
        ") VALUES (\n"
        "  {session_id}, {call_index}, {tool_name}, {tool_category},\n"
        "  {input_summary}, {output_summary},\n"
        "  {success}, {was_rejected}, {was_revision},\n"
        "  {error_type}, {error_message}, {exit_code},\n"
        "  {target_file}, {target_domain},\n"
        "  {is_background}, {is_agent}, {agent_type}, {plugin_name},\n"
        "  {is_sensitive_file}, {has_secret_exposure}, {is_destructive}, {was_blocked_by_hook},\n"
        "  {security_flags}, {caller_type}, {was_interrupted}, {was_truncated},\n"
        "  {agent_id}, {agent_tokens}, {agent_tool_count}, {agent_duration_ms},\n"
        "  {background_task_id}, {result_duration_ms}, {duration_ms},\n"
        "  {repo}, {org}, {session_date}, {created_at}\n"
        ")\n"
        "ON CONFLICT (session_id, call_index) DO NOTHING;"
    ).format(
        session_id=pg_text(tc["session_id"]),
        call_index=pg_int(tc["call_index"]),
        tool_name=pg_text(tc["tool_name"]),
        tool_category=pg_text(tc["tool_category"]),
        input_summary=pg_text(tc["input_summary"]),
        output_summary=pg_text(tc["output_summary"]),
        success=pg_bool(tc["success"]),
        was_rejected=pg_bool(tc["was_rejected"]),
        was_revision=pg_bool(tc["was_revision"]),
        error_type=pg_text(tc["error_type"]),
        error_message=pg_text(tc["error_message"]),
        exit_code=pg_int(tc["exit_code"]),
        target_file=pg_text(tc["target_file"]),
        target_domain=pg_text(tc["target_domain"]),
        is_background=pg_bool(tc["is_background"]),
        is_agent=pg_bool(tc["is_agent"]),
        agent_type=pg_text(tc["agent_type"]),
        plugin_name=pg_text(tc["plugin_name"]),
        is_sensitive_file=pg_bool(tc["is_sensitive_file"]),
        has_secret_exposure=pg_bool(tc["has_secret_exposure"]),
        is_destructive=pg_bool(tc["is_destructive"]),
        was_blocked_by_hook=pg_bool(tc["was_blocked_by_hook"]),
        security_flags=pg_array(tc["security_flags"]),
        caller_type=pg_text(tc["caller_type"]),
        was_interrupted=pg_bool(tc["was_interrupted"]),
        was_truncated=pg_bool(tc["was_truncated"]),
        agent_id=pg_text(tc["agent_id"]),
        agent_tokens=pg_int(tc["agent_tokens"]),
        agent_tool_count=pg_int(tc["agent_tool_count"]),
        agent_duration_ms=pg_int(tc["agent_duration_ms"]),
        background_task_id=pg_text(tc["background_task_id"]),
        result_duration_ms=pg_int(tc["result_duration_ms"]),
        duration_ms=pg_int(tc["duration_ms"]),
        repo=pg_text(tc["repo"]),
        org=pg_text(tc["org"]),
        session_date=pg_text(tc["session_date"]),
        created_at=pg_text(tc["created_at"]),
    )


def write_batches(statements, output_dir, session_id):
    """Write INSERT statements in BATCH_SIZE chunks to output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files_written = []
    total_batches = (len(statements) + BATCH_SIZE - 1) // BATCH_SIZE
    for i, start in enumerate(range(0, len(statements), BATCH_SIZE)):
        chunk = statements[start : start + BATCH_SIZE]
        fname = output_dir / "{}_{:03d}.sql".format(session_id, i + 1)
        with open(fname, "w", encoding="utf-8") as fh:
            fh.write("-- Session Hoardinator: batch {} of {} for {}\n".format(
                i + 1, total_batches, session_id))
            fh.write("BEGIN;\n\n")
            fh.write("\n\n".join(chunk))
            fh.write("\n\nCOMMIT;\n")
        files_written.append(fname)
    return files_written


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Parse Claude Code JSONL sessions and generate SQL for Supabase.",
        epilog=(
            "Prerequisites: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set,\n"
            "and the Supabase plugin must be installed in Claude Code.\n"
            "Use --dry-run to preview counts without writing files or checking credentials."
        ),
    )
    parser.add_argument("--session", metavar="UUID",
                        help="Process a specific session by its UUID")
    parser.add_argument("--output", metavar="DIR",
                        help="Directory for SQL output files (required unless --dry-run)")
    parser.add_argument("--date", metavar="YYYY-MM-DD",
                        help="Process only sessions modified on this date")
    parser.add_argument("--all", dest="all_repos", action="store_true",
                        help="Process all sessions across all repos on this machine")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print counts only; no SQL files written, no credential check")
    parser.add_argument("--repo", metavar="OWNER/REPO",
                        help="Override repo namespace (default: from git remote)")
    parser.add_argument("--org", metavar="OWNER",
                        help="Override org namespace (default: derived from --repo)")
    args = parser.parse_args()

    if not args.dry_run and not args.output:
        parser.error("--output <dir> is required unless --dry-run is specified")

    check_prerequisites(dry_run=args.dry_run)

    repo, org, author = get_git_info()
    if args.repo:
        repo = args.repo
        org = args.org or (repo.split("/")[0] if "/" in repo else repo)
    environment = get_environment()

    if not repo:
        print(
            "Warning: Could not determine repo from git remote.\n"
            "Use --repo owner/name to set it explicitly.",
            file=sys.stderr,
        )
        repo = "unknown/unknown"
        org = "unknown"

    jsonl_files = find_jsonl_files(args)
    if not jsonl_files:
        print("No JSONL session files found.")
        return

    total_sessions = 0
    total_skipped = 0
    total_msgs = 0
    total_tcs = 0
    all_files = []

    for jsonl_path in jsonl_files:
        print("  Processing {} ...".format(jsonl_path.name), end=" ", flush=True)
        result = parse_jsonl_file(jsonl_path, repo, org, author, environment)
        if result is None:
            total_skipped += 1
            print("skipped (empty)")
            continue

        session_row, msgs, tcs = result
        total_sessions += 1
        total_msgs += len(msgs)
        total_tcs += len(tcs)
        print("{} messages, {} tool calls".format(len(msgs), len(tcs)))

        if not args.dry_run:
            stmts = (
                [generate_session_sql(session_row)]
                + [generate_message_sql(m) for m in msgs]
                + [generate_tool_call_sql(tc) for tc in tcs]
            )
            all_files.extend(write_batches(stmts, args.output, session_row["session_id"]))

    print("\nSession Hoardinator parse complete:")
    print("  Sessions processed : {}".format(total_sessions))
    print("  Sessions skipped   : {} (empty)".format(total_skipped))
    print("  Total messages     : {}".format(total_msgs))
    print("  Total tool calls   : {}".format(total_tcs))
    if not args.dry_run:
        print("  SQL files written  : {}".format(len(all_files)))
        print("  Output directory   : {}".format(args.output))
        print("\nNext: run upload-sessions.sh {}".format(args.output))


if __name__ == "__main__":
    main()
