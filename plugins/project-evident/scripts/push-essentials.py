#!/usr/bin/env python3
"""
push-essentials.py - Push essentials data to Notion.

Reads essentials-review.md (or essentials-payload.json if it exists),
clears existing endpoint fields on the Essentials page, then pushes
each endpoint value. Also pushes a summary to the page content.

Usage:
    python3 push-essentials.py ALAS
    python3 push-essentials.py all
    python3 push-essentials.py ALAS --dry-run
    python3 push-essentials.py ALAS --clean-only   # just clear fields, don't push

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

CLIENTS = {
    "ALAS": {"folder": "ALAS Working Files", "essentials_page_id": "cbafaee4b7334746988ea76d39f7e9ed", "client_page_id": "2aaa2a956650803b93c4e9565fb80dcd"},
    "Building Promise": {"folder": "Building Promise Working Files", "essentials_page_id": "20f0abcb1b914e43aab9cc267df71d1c", "client_page_id": "2aaa2a95665080f9b43ae92cb493c43a"},
    "CPA": {"folder": "CPA Working Files", "essentials_page_id": "a7eab654617c4031bef40af65822c007", "client_page_id": "2aaa2a956650806cb479c164b64829ce"},
    "CHDC": {"folder": "CHDC Working Files", "essentials_page_id": "cb71fd8d747a4ae6b37583cdf962fc6d", "client_page_id": "2aaa2a9566508060a6d1d2ed3056e050"},
    "E4": {"folder": "E4 Youth Working Files", "essentials_page_id": "a6b5553660124314b0394168503922e4", "client_page_id": "2aaa2a95665080108e87ff952a656af6"},
    "EDC": {"folder": "EDC Working Files", "essentials_page_id": "01c62bde3bb6431eb10af51987b40546", "client_page_id": "2aaa2a956650809ca20acc03b583ddb7"},
    "LAA": {"folder": "LAA Working Files", "essentials_page_id": "5e9704da19594e1dbcbd16d7b667c0f1", "client_page_id": "2aaa2a95665080059938e10f32c53166"},
    "SV@Home": {"folder": "SV@Home Working Files", "essentials_page_id": "10a3c22b981b4de4baedddb2d844c63f", "client_page_id": "2aaa2a95665080feb633f5e9e53fa702"},
    "Sumter": {"folder": "Sumter Working Files", "essentials_page_id": "bc1e39451152408e8492d94af6a68ffa", "client_page_id": "2aaa2a95665080fb95e5c8a03cf41175"},
    "TAP": {"folder": "TAP Working Files", "essentials_page_id": "5f99201e619e4c6688d2df2bd5be842b", "client_page_id": "2aaa2a95665080e38fecc2f37c05d4b3"},
    "TIP": {"folder": "TIP Working Files", "essentials_page_id": "f41fb0c3396d4a63aa13bb9b591bf9ee", "client_page_id": "2aaa2a95665080efb5bcdfb78b3df0d2"},
}

# All 50 endpoint fields from endpoint-map.md
ENDPOINT_FIELDS = {
    # Component 1: Pain Point & AI Solution
    "C1P1T1: Pain Point": "text",
    "C1P1T2: Current Impact": "text",
    "C1P2: Reviewed AI Solutions and Tools": "text",
    # Component 2: Policy
    "C2T1F1: Policy Document Link": "url",
    "C2T1F2: Policy Notes": "text",
    # Component 3 Phase 1: Foundation
    "C3P1T1F1: AI Tools Purchase Checked": "checkbox",
    "C3P1T1F2: Description of AI Tools Purchase": "text",
    "C3P1T1F3: Owner for AI Tools Purchase": "text",
    "C3P1T1F4: Progress Indicators for AI Tools Purchase": "text",
    "C3P1T2F1: Data Identified Checked": "checkbox",
    "C3P1T2F2: Description of Data Identified and Readiness": "text",
    "C3P1T2F3: Owner for Data Identification": "text",
    "C3P1T2F4: Progress Indicators for Data Readiness": "text",
    "C3P1T3F1: Technology Integration Complete Checked": "checkbox",
    "C3P1T3F2: Description of Technology Integration": "text",
    "C3P1T3F3: Owner for Technology Integration": "text",
    "C3P1T3F4: Progress Indicators for Technology Integration": "text",
    # Component 3 Phase 2: Testing
    "C3P2T1F1: Small Scale Test Run Checked": "checkbox",
    "C3P2T1F2: Description of Small Scale Test": "text",
    "C3P2T1F3: Owner for Small Scale Test": "text",
    "C3P2T1F4: Progress Indicators for Small Scale Test": "text",
    # Component 3 Phase 3: Rollout
    "C3P3T1F1: Wider Rollout Checked": "checkbox",
    "C3P3T1F2: Description of Wider Rollout": "text",
    "C3P3T1F3: Owner for Wider Rollout": "text",
    "C3P3T1F4: Progress Indicators for Wider Rollout": "text",
    # Component 4: Before/After
    "C4P1F1: Before AI": "text",
    "C4P1F2: After AI": "text",
    # Component 4: Benefits
    "C4P2T1F1: Cost Savings Checked": "checkbox",
    "C4P2T1F2: Description of Cost Savings": "text",
    "C4P2T1F3: Evidence of Cost Savings": "text",
    "C4P2T2F1: Productivity Gains Checked": "checkbox",
    "C4P2T2F2: Description of Productivity Gains": "text",
    "C4P2T2F3: Evidence of Productivity Gains": "text",
    "C4P2T3F1: Policy Changes Checked": "checkbox",
    "C4P2T3F2: Description of Policy Changes": "text",
    "C4P2T3F3: Evidence of Policy Changes": "text",
    "C4P2T4F1: Service Delivery Improvements Checked": "checkbox",
    "C4P2T4F2: Description of Service Delivery Improvements": "text",
    "C4P2T4F3: Evidence of Service Delivery Improvements": "text",
    "C4P2T5F1: Outcomes Improved Checked": "checkbox",
    "C4P2T5F2: Description of Outcomes Improved": "text",
    "C4P2T5F3: Evidence of Outcomes Improved": "text",
    "C4P2T6F1: Increased Funding Checked": "checkbox",
    "C4P2T6F2: Description of Increased Funding": "text",
    "C4P2T6F3: Evidence of Increased Funding": "text",
    "C4P2T7F1: Other Changes Checked": "checkbox",
    "C4P2T7F2: Description of Other Changes": "text",
    "C4P2T7F3: Evidence of Other Changes": "text",
    # Narrative
    "Coaching Notes": "text",
    "Aha Moments": "text",
}


def get_token():
    token = os.environ.get("NOTION_API_KEY")
    if not token:
        print("ERROR: NOTION_API_KEY env var not set.", file=sys.stderr)
        sys.exit(1)
    return token


def notion_request(token, method, path, body=None):
    url = f"{NOTION_API}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        error_body = e.read().decode()
        print(f"Notion API error {e.code}: {error_body}", file=sys.stderr)
        raise


def notion_patch(token, path, body):
    return notion_request(token, "PATCH", path, body)


def notion_get(token, path):
    return notion_request(token, "GET", path)


def notion_delete(token, path):
    return notion_request(token, "DELETE", path)


def build_clear_properties():
    """Build a properties payload that clears all 50 endpoint fields."""
    props = {}
    for field_name, field_type in ENDPOINT_FIELDS.items():
        if field_type == "checkbox":
            props[field_name] = {"checkbox": False}
        elif field_type == "url":
            props[field_name] = {"url": None}
        elif field_type == "text":
            props[field_name] = {"rich_text": []}
    return props


def build_push_properties(values):
    """Build a properties payload from a dict of field_name -> value."""
    props = {}
    for field_name, value in values.items():
        if field_name not in ENDPOINT_FIELDS:
            print(f"  WARNING: Unknown field '{field_name}', skipping")
            continue

        field_type = ENDPOINT_FIELDS[field_name]

        if not value or value.strip() == "":
            continue  # Skip blanks

        if field_type == "checkbox":
            is_checked = value.strip().upper() in ("__YES__", "YES", "TRUE", "1")
            props[field_name] = {"checkbox": is_checked}
        elif field_type == "url":
            url_val = value.strip()
            if url_val and url_val.startswith("http"):
                props[field_name] = {"url": url_val}
        elif field_type == "text":
            # Notion rich_text has 2000 char limit per text block
            text = value.strip()
            chunks = []
            while text:
                chunks.append({"type": "text", "text": {"content": text[:2000]}})
                text = text[2000:]
            props[field_name] = {"rich_text": chunks}

    return props


def clear_page_content(token, page_id):
    """Delete all block children from a page (clear the page body)."""
    blocks = []
    cursor = None
    while True:
        path = f"/blocks/{page_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        resp = notion_get(token, path)
        blocks.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    for block in blocks:
        try:
            notion_delete(token, f"/blocks/{block['id']}")
        except HTTPError:
            pass  # Some blocks may not be deletable

    return len(blocks)


def push_page_content(token, page_id, markdown_content):
    """Push markdown content as blocks to the page body."""
    blocks = []
    for line in markdown_content.split("\n"):
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]},
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]},
            })
        elif line.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]},
            })
        elif line.startswith("- "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]},
            })
        elif line.startswith("---"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        else:
            # Truncate to 2000 chars per paragraph block
            text = line[:2000]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
            })

    # Notion allows max 100 blocks per append
    for i in range(0, len(blocks), 100):
        batch = blocks[i:i + 100]
        notion_patch(token, f"/blocks/{page_id}/children", {"children": batch})

    return len(blocks)


def load_payload_json(folder_path):
    """Try to load essentials-payload.json (generated by Stage 3)."""
    payload_file = folder_path / "3-essentials" / "essentials-payload.json"
    if payload_file.exists():
        data = json.loads(payload_file.read_text())
        return data.get("properties", {})
    return None


def load_review_md(folder_path):
    """Parse essentials-review.md tables to extract field values."""
    review_file = folder_path / "3-essentials" / "essentials-review.md"
    if not review_file.exists():
        return None

    text = review_file.read_text()
    values = {}

    # Parse markdown tables: | Field Name | Value |
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        # parts[0] is empty (before first |), parts[-1] is empty (after last |)
        if len(parts) < 4:
            continue
        field = parts[1]
        value = parts[2]

        # Skip header rows
        if field in ("Field", "---", "Element") or field.startswith("-"):
            continue

        # Match against known fields
        if field in ENDPOINT_FIELDS:
            values[field] = value

    return values


def process_client(token, short_name, client_info, dry_run=False, clean_only=False):
    now = datetime.now(timezone.utc).isoformat()
    folder_path = ARTIFACT_ROOT / client_info["folder"]
    essentials_page_id = client_info["essentials_page_id"]

    print(f"\n{'='*60}")
    print(f"Push essentials: {short_name}")
    print(f"Target page: {essentials_page_id}")
    print(f"{'='*60}")

    # Step 1: Clear existing fields
    print(f"  Clearing all 50 endpoint fields...")
    clear_props = build_clear_properties()

    if not dry_run:
        try:
            notion_patch(token, f"/pages/{essentials_page_id}", {"properties": clear_props})
            print(f"    Cleared {len(clear_props)} fields")
        except HTTPError as e:
            print(f"    FAILED to clear fields: {e}")
            return False
    else:
        print(f"    DRY RUN: Would clear {len(clear_props)} fields")

    # Step 2: Clear page body content
    print(f"  Clearing page body content...")
    if not dry_run:
        deleted = clear_page_content(token, essentials_page_id)
        print(f"    Deleted {deleted} blocks")
    else:
        print(f"    DRY RUN: Would delete existing blocks")

    if clean_only:
        print(f"  Clean-only mode -- stopping here.")
        return True

    # Step 3: Load values
    # Prefer payload JSON (post-HITL), fall back to review MD
    values = load_payload_json(folder_path)
    source = "essentials-payload.json"
    if values is None:
        values = load_review_md(folder_path)
        source = "essentials-review.md"
    if values is None:
        print(f"  ERROR: No essentials-review.md or essentials-payload.json found in {folder_path / '3-essentials'}")
        return False

    print(f"  Loaded values from {source}: {len(values)} non-empty fields")

    # Step 4: Push endpoint properties
    push_props = build_push_properties(values)
    print(f"  Pushing {len(push_props)} fields to Notion properties...")

    if not dry_run:
        try:
            notion_patch(token, f"/pages/{essentials_page_id}", {"properties": push_props})
            print(f"    Pushed {len(push_props)} fields")
        except HTTPError as e:
            print(f"    FAILED: {e}")
            return False
    else:
        for fname in sorted(push_props.keys()):
            ftype = ENDPOINT_FIELDS.get(fname, "?")
            print(f"    {fname} ({ftype})")

    # Step 5: Push summary content to page body
    review_file = folder_path / "3-essentials" / "essentials-review.md"
    if review_file.exists():
        print(f"  Pushing essentials content to page body...")
        review_text = review_file.read_text()
        # Strip frontmatter
        body = re.sub(r"^---\n.*?\n---\n*", "", review_text, flags=re.DOTALL).strip()

        if not dry_run:
            block_count = push_page_content(token, essentials_page_id, body)
            print(f"    Pushed {block_count} blocks to page body")
        else:
            print(f"    DRY RUN: Would push ~{len(body.split(chr(10)))} lines to page body")

    # Step 6: Log
    if not dry_run:
        log_file = folder_path / "pipeline.log"
        log_entry = (
            f"[{now}] [v{PLUGIN_VERSION}] [push-essentials] [{short_name}]\n"
            f"  Status: PUSHED_TO_NOTION\n"
            f"  Target: essentials_page_id={essentials_page_id}\n"
            f"  Source: {source}\n"
            f"  Fields pushed: {len(push_props)} of 50\n"
            f"  Page body: updated\n\n"
        )
        with open(log_file, "a") as f:
            f.write(log_entry)

    print(f"  Done.")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 push-essentials.py <client|all> [--dry-run] [--clean-only]")
        sys.exit(1)

    arg = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    clean_only = "--clean-only" in sys.argv

    if dry_run:
        print("*** DRY RUN MODE -- no changes will be made ***\n")
    if clean_only:
        print("*** CLEAN ONLY MODE -- will clear fields but not push new values ***\n")

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

    results = {}
    for short_name, client_info in clients_to_process:
        ok = process_client(token, short_name, client_info, dry_run=dry_run, clean_only=clean_only)
        results[short_name] = ok

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for short_name, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {short_name:20s} {status}")


if __name__ == "__main__":
    main()
