#!/usr/bin/env python3
"""
push-evaluations.py - Push evaluation content to Notion coaching call records.

Reads evaluation files from 2-evaluations/, pushes the content to the
"Call Evaluation" rich_text property on each coaching call page in Notion.

Usage:
    python3 push-evaluations.py ALAS
    python3 push-evaluations.py all
    python3 push-evaluations.py ALAS --dry-run    # show what would be pushed

Requires: NOTION_API_KEY env var
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

PLUGIN_VERSION = "1.1.0"
ARTIFACT_ROOT = Path.home() / "Dev" / "claude-cowork" / "Clients" / "Project Evident Updates"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
EVAL_PROPERTY_NAME = "Call Evaluation"

# Same client mapping as pull-transcripts.py
CLIENTS = {
    "ALAS": {"folder": "ALAS Working Files", "client_page_id": "2aaa2a956650803b93c4e9565fb80dcd"},
    "Building Promise": {"folder": "Building Promise Working Files", "client_page_id": "2aaa2a95665080f9b43ae92cb493c43a"},
    "CPA": {"folder": "CPA Working Files", "client_page_id": "2aaa2a956650806cb479c164b64829ce"},
    "CHDC": {"folder": "CHDC Working Files", "client_page_id": "2aaa2a9566508060a6d1d2ed3056e050"},
    "E4": {"folder": "E4 Youth Working Files", "client_page_id": "2aaa2a95665080108e87ff952a656af6"},
    "EDC": {"folder": "EDC Working Files", "client_page_id": "2aaa2a956650809ca20acc03b583ddb7"},
    "LAA": {"folder": "LAA Working Files", "client_page_id": "2aaa2a95665080059938e10f32c53166"},
    "SV@Home": {"folder": "SV@Home Working Files", "client_page_id": "2aaa2a95665080feb633f5e9e53fa702"},
    "Sumter": {"folder": "Sumter Working Files", "client_page_id": "2aaa2a95665080fb95e5c8a03cf41175"},
    "TAP": {"folder": "TAP Working Files", "client_page_id": "2aaa2a95665080e38fecc2f37c05d4b3"},
    "TIP": {"folder": "TIP Working Files", "client_page_id": "2aaa2a95665080efb5bcdfb78b3df0d2"},
}


def get_token():
    token = os.environ.get("NOTION_API_KEY")
    if not token:
        print("ERROR: NOTION_API_KEY env var not set.", file=sys.stderr)
        sys.exit(1)
    return token


def notion_patch(token, path, body):
    url = f"{NOTION_API}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode()
    req = Request(url, data=data, headers=headers, method="PATCH")
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        error_body = e.read().decode()
        print(f"Notion API error {e.code}: {error_body}", file=sys.stderr)
        raise


def parse_frontmatter(text):
    """Extract YAML frontmatter as a dict."""
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def get_eval_body(text):
    """Get everything after the YAML frontmatter."""
    match = re.match(r"^---\n.*?\n---\n*(.*)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def truncate_for_notion(text, max_chars=2000):
    """Notion rich_text has a 2000 char limit per block. Split into chunks."""
    chunks = []
    while text:
        chunks.append(text[:max_chars])
        text = text[max_chars:]
    return chunks


def push_evaluation(token, transcript_page_id, eval_content, dry_run=False):
    """Push evaluation content to the Call Evaluation property on a coaching call page."""
    chunks = truncate_for_notion(eval_content)
    rich_text = [{"type": "text", "text": {"content": chunk}} for chunk in chunks]

    body = {
        "properties": {
            EVAL_PROPERTY_NAME: {
                "rich_text": rich_text
            }
        }
    }

    if dry_run:
        print(f"    DRY RUN: Would push {len(eval_content)} chars to page {transcript_page_id}")
        return True

    try:
        notion_patch(token, f"/pages/{transcript_page_id}", body)
        return True
    except HTTPError:
        return False


def process_client(token, short_name, client_info, dry_run=False):
    now = datetime.now(timezone.utc).isoformat()
    folder_path = ARTIFACT_ROOT / client_info["folder"]
    eval_dir = folder_path / "2-evaluations"

    print(f"\n{'='*60}")
    print(f"Pushing evaluations: {short_name}")
    print(f"{'='*60}")

    # Find evaluation files
    eval_files = sorted(eval_dir.glob("call-*-evaluation.md"))
    if not eval_files:
        print(f"  No evaluation files found in {eval_dir}")
        return 0

    print(f"  Found {len(eval_files)} evaluation files")

    success_count = 0
    for eval_file in eval_files:
        text = eval_file.read_text()
        fm = parse_frontmatter(text)
        body = get_eval_body(text)

        transcript_page_id = fm.get("transcript_page_id", "")
        session = fm.get("session", "?")

        if not transcript_page_id:
            print(f"  SKIP: {eval_file.name} -- no transcript_page_id in frontmatter")
            continue

        print(f"  Pushing call {session} -> page {transcript_page_id} ({len(body)} chars)...")
        if push_evaluation(token, transcript_page_id, body, dry_run=dry_run):
            success_count += 1
            print(f"    OK")
        else:
            print(f"    FAILED")

    # Log
    if not dry_run:
        log_file = folder_path / "pipeline.log"
        log_entry = (
            f"[{now}] [v{PLUGIN_VERSION}] [push-evaluations] [{short_name}]\n"
            f"  Status: SUCCESS\n"
            f"  Evaluations pushed: {success_count} of {len(eval_files)}\n"
            f"  Target property: {EVAL_PROPERTY_NAME}\n\n"
        )
        with open(log_file, "a") as f:
            f.write(log_entry)

    return success_count


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 push-evaluations.py <client|all> [--dry-run]")
        sys.exit(1)

    arg = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("*** DRY RUN MODE -- no changes will be made ***\n")

    token = get_token()

    if arg.lower() == "all":
        clients_to_process = list(CLIENTS.items())
    else:
        match = None
        for short, info in CLIENTS.items():
            if arg.lower() == short.lower():
                match = (short, info)
                break
        if not match:
            print(f"ERROR: Unknown client '{arg}'.", file=sys.stderr)
            sys.exit(1)
        clients_to_process = [match]

    total = 0
    for short_name, client_info in clients_to_process:
        count = process_client(token, short_name, client_info, dry_run=dry_run)
        total += count

    print(f"\nTotal evaluations pushed: {total}")


if __name__ == "__main__":
    main()
