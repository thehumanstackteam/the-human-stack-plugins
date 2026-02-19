#!/usr/bin/env python3
"""
pull-transcripts.py - Replaces Phase A entirely.

Pulls coaching call transcripts from Notion, filters them, creates folder
structure, writes raw transcripts and manifest. No AI needed.

Usage:
    python3 pull-transcripts.py ALAS
    python3 pull-transcripts.py all          # batch all 11 clients
    python3 pull-transcripts.py --list       # show all clients

Requires: NOTION_API_KEY env var (internal integration token)
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

# From org-mapping.md
CLIENTS = {
    "ALAS": {
        "full_name": "Ayudando Latinos a Sonar",
        "folder": "ALAS Working Files",
        "client_page_id": "2aaa2a956650803b93c4e9565fb80dcd",
        "essentials_page_id": "cbafaee4b7334746988ea76d39f7e9ed",
    },
    "Building Promise": {
        "full_name": "Building Promise USA",
        "folder": "Building Promise Working Files",
        "client_page_id": "2aaa2a95665080f9b43ae92cb493c43a",
        "essentials_page_id": "20f0abcb1b914e43aab9cc267df71d1c",
    },
    "CPA": {
        "full_name": "Chinese Progressive Association",
        "folder": "CPA Working Files",
        "client_page_id": "2aaa2a956650806cb479c164b64829ce",
        "essentials_page_id": "a7eab654617c4031bef40af65822c007",
    },
    "CHDC": {
        "full_name": "Community Housing Dev Corp",
        "folder": "CHDC Working Files",
        "client_page_id": "2aaa2a9566508060a6d1d2ed3056e050",
        "essentials_page_id": "cb71fd8d747a4ae6b37583cdf962fc6d",
    },
    "E4": {
        "full_name": "E4 Youth",
        "folder": "E4 Youth Working Files",
        "client_page_id": "2aaa2a95665080108e87ff952a656af6",
        "essentials_page_id": "a6b5553660124314b0394168503922e4",
    },
    "EDC": {
        "full_name": "Eviction Defense Collaborative",
        "folder": "EDC Working Files",
        "client_page_id": "2aaa2a956650809ca20acc03b583ddb7",
        "essentials_page_id": "01c62bde3bb6431eb10af51987b40546",
    },
    "LAA": {
        "full_name": "Latin America Association",
        "folder": "LAA Working Files",
        "client_page_id": "2aaa2a95665080059938e10f32c53166",
        "essentials_page_id": "5e9704da19594e1dbcbd16d7b667c0f1",
    },
    "SV@Home": {
        "full_name": "Silicon Valley at Home",
        "folder": "SV@Home Working Files",
        "client_page_id": "2aaa2a95665080feb633f5e9e53fa702",
        "essentials_page_id": "10a3c22b981b4de4baedddb2d844c63f",
    },
    "Sumter": {
        "full_name": "Sumter United Ministries",
        "folder": "Sumter Working Files",
        "client_page_id": "2aaa2a95665080fb95e5c8a03cf41175",
        "essentials_page_id": "bc1e39451152408e8492d94af6a68ffa",
    },
    "TAP": {
        "full_name": "Texas Advocacy Project",
        "folder": "TAP Working Files",
        "client_page_id": "2aaa2a95665080e38fecc2f37c05d4b3",
        "essentials_page_id": "5f99201e619e4c6688d2df2bd5be842b",
    },
    "TIP": {
        "full_name": "Transgender Intersex Justice Project",
        "folder": "TIP Working Files",
        "client_page_id": "2aaa2a95665080efb5bcdfb78b3df0d2",
        "essentials_page_id": "f41fb0c3396d4a63aa13bb9b591bf9ee",
    },
}


def get_token():
    token = os.environ.get("NOTION_API_KEY")
    if not token:
        print("ERROR: NOTION_API_KEY env var not set.", file=sys.stderr)
        print("Set it: export NOTION_API_KEY='ntn_...'", file=sys.stderr)
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


def notion_get(token, path):
    return notion_request(token, "GET", path)


def get_page(token, page_id):
    return notion_get(token, f"/pages/{page_id}")


def get_page_content(token, page_id):
    """Get all block children (page body content)."""
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
    return blocks


def extract_rich_text(prop):
    """Extract plain text from a Notion rich_text property."""
    if not prop:
        return ""
    rich_text = prop.get("rich_text", [])
    if not rich_text:
        return ""
    return "".join(rt.get("plain_text", "") for rt in rich_text)


def extract_title(prop):
    """Extract plain text from a Notion title property."""
    if not prop:
        return ""
    title = prop.get("title", [])
    if not title:
        return ""
    return "".join(t.get("plain_text", "") for t in title)


def extract_relation(prop):
    """Extract list of page IDs from a relation property."""
    if not prop:
        return []
    return [r["id"] for r in prop.get("relation", [])]


def extract_select(prop):
    """Extract select value."""
    if not prop:
        return ""
    select = prop.get("select")
    if not select:
        return ""
    return select.get("name", "")


def extract_date(prop):
    """Extract date string from a date property."""
    if not prop:
        return ""
    date = prop.get("date")
    if not date:
        return ""
    return date.get("start", "")


def blocks_to_text(blocks):
    """Convert Notion blocks to plain text."""
    lines = []
    for block in blocks:
        btype = block.get("type", "")
        content = block.get(btype, {})
        rich_text = content.get("rich_text", [])
        text = "".join(rt.get("plain_text", "") for rt in rich_text)
        if btype.startswith("heading"):
            lines.append(f"\n{'#' * int(btype[-1])} {text}\n")
        elif btype == "bulleted_list_item":
            lines.append(f"- {text}")
        elif btype == "numbered_list_item":
            lines.append(f"1. {text}")
        elif btype == "divider":
            lines.append("---")
        else:
            lines.append(text)
    return "\n".join(lines)


def process_client(token, short_name, client_info):
    now = datetime.now(timezone.utc).isoformat()
    folder_path = ARTIFACT_ROOT / client_info["folder"]
    transcripts_dir = folder_path / "1-transcripts"
    evaluations_dir = folder_path / "2-evaluations"
    essentials_dir = folder_path / "3-essentials"

    # Create folders
    for d in [transcripts_dir, evaluations_dir, essentials_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Processing: {short_name} ({client_info['full_name']})")
    print(f"Folder: {folder_path}")
    print(f"{'='*60}")

    # Fetch client page
    client_page_id = client_info["client_page_id"]
    print(f"Fetching client page {client_page_id}...")
    page = get_page(token, client_page_id)
    props = page.get("properties", {})

    # Get coaching calls relation
    coaching_calls_prop = None
    for pname, pval in props.items():
        if "coaching call" in pname.lower() or "coaching calls" in pname.lower():
            coaching_calls_prop = pval
            break

    if not coaching_calls_prop:
        # Try to find any relation property
        for pname, pval in props.items():
            if pval.get("type") == "relation":
                print(f"  Found relation property: {pname}")
                coaching_calls_prop = pval
                break

    if not coaching_calls_prop:
        print(f"  ERROR: No Coaching Calls relation found on client page.", file=sys.stderr)
        return None

    call_page_ids = extract_relation(coaching_calls_prop)
    print(f"  Found {len(call_page_ids)} pages in Coaching Calls relation.")

    # Fetch and filter each coaching call
    passing_calls = []
    skipped = []

    for call_id in call_page_ids:
        print(f"  Fetching call page {call_id}...")
        try:
            call_page = get_page(token, call_id)
        except HTTPError:
            print(f"    SKIP: Could not fetch page {call_id}")
            skipped.append({"page_id": call_id, "title": "?", "reason": "Fetch error"})
            continue

        call_props = call_page.get("properties", {})
        title = ""
        for pname, pval in call_props.items():
            if pval.get("type") == "title":
                title = extract_title(pval)
                break

        # Filter 1: Page Type
        page_type = ""
        for pname, pval in call_props.items():
            if pname.lower() == "page type":
                page_type = extract_select(pval)
                break

        if page_type in ("Cancellation", "THS Cancelled"):
            print(f"    SKIP: {title} -- {page_type}")
            skipped.append({"page_id": call_id, "title": title, "reason": page_type})
            continue

        if page_type == "Client Page":
            print(f"    SKIP: {title} -- Client Page (not a call)")
            skipped.append({"page_id": call_id, "title": title, "reason": "Client Page"})
            continue

        # Filter 2: Transcript content
        transcript = ""
        for pname, pval in call_props.items():
            if pname.lower() == "transcript":
                transcript = extract_rich_text(pval)
                break

        if not transcript or transcript.strip() == "" or transcript.strip() == "No transcript available":
            print(f"    SKIP: {title} -- No transcript content")
            skipped.append({"page_id": call_id, "title": title, "reason": "No transcript"})
            continue

        # Filter 3: Not-a-call check
        call_eval = ""
        for pname, pval in call_props.items():
            if pname.lower() == "call evaluation":
                call_eval = extract_rich_text(pval)
                break

        if call_eval.startswith("NOT A COACHING CALL"):
            print(f"    SKIP: {title} -- Marked as not a coaching call")
            skipped.append({"page_id": call_id, "title": title, "reason": "Not a coaching call"})
            continue

        # Extract date
        call_date = ""
        for pname, pval in call_props.items():
            if pval.get("type") == "date" and "date" in pname.lower():
                call_date = extract_date(pval)
                break

        # If no date property, try to parse from title
        if not call_date:
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", title)
            if date_match:
                call_date = date_match.group(1)

        print(f"    PASS: {title} (date: {call_date}, transcript: {len(transcript)} chars)")
        passing_calls.append({
            "page_id": call_id,
            "title": title,
            "date": call_date,
            "transcript": transcript,
        })

    # Sort by date and assign call numbers
    passing_calls.sort(key=lambda c: c.get("date", ""))
    for i, call in enumerate(passing_calls, 1):
        call["call_number"] = i

    print(f"\n  Results: {len(passing_calls)} calls to analyze, {len(skipped)} filtered out")

    # Write transcripts
    for call in passing_calls:
        n = call["call_number"]
        transcript_file = transcripts_dir / f"call-{n}-transcript.md"
        frontmatter = (
            f"---\n"
            f"client: {short_name}\n"
            f"client_page_id: {client_info['client_page_id']}\n"
            f"transcript_page_id: {call['page_id']}\n"
            f"session: {n}\n"
            f"date: {call['date']}\n"
            f"title: {call['title']}\n"
            f"plugin_version: {PLUGIN_VERSION}\n"
            f"created_at: {now}\n"
            f"---\n\n"
        )
        transcript_file.write_text(frontmatter + call["transcript"])
        print(f"  Wrote: {transcript_file.name}")

    # Write manifest
    manifest = {
        "client": short_name,
        "client_page_id": client_info["client_page_id"],
        "essentials_page_id": client_info["essentials_page_id"],
        "folder_name": client_info["folder"],
        "plugin_version": PLUGIN_VERSION,
        "created_at": now,
        "total_pages_in_relation": len(call_page_ids),
        "filtered_out": len(skipped),
        "calls_to_analyze": [
            {
                "call_number": c["call_number"],
                "transcript_page_id": c["page_id"],
                "date": c["date"],
                "title": c["title"],
                "transcript_file": f"1-transcripts/call-{c['call_number']}-transcript.md",
            }
            for c in passing_calls
        ],
        "skipped": skipped,
    }
    manifest_file = transcripts_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2))
    print(f"  Wrote: manifest.json")

    # Append to pipeline.log
    log_file = folder_path / "pipeline.log"
    skip_reasons = {}
    for s in skipped:
        r = s["reason"]
        skip_reasons[r] = skip_reasons.get(r, 0) + 1
    reasons_str = ", ".join(f"{v}x {k}" for k, v in skip_reasons.items()) if skip_reasons else "none"

    log_entry = (
        f"[{now}] [v{PLUGIN_VERSION}] [stage-1:phase-a:retrieval] [{short_name}]\n"
        f"  Status: SUCCESS\n"
        f"  Total pages in relation: {len(call_page_ids)}\n"
        f"  Filtered out: {len(skipped)} ({reasons_str})\n"
        f"  Calls to analyze: {len(passing_calls)}\n"
        f"  Transcript files written: {', '.join('call-' + str(c['call_number']) + '-transcript.md' for c in passing_calls)}\n"
        f"  Manifest: 1-transcripts/manifest.json\n\n"
    )
    with open(log_file, "a") as f:
        f.write(log_entry)

    print(f"  Logged to pipeline.log")
    return manifest


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pull-transcripts.py <client|all|--list>")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--list":
        print("Available clients:")
        for short, info in CLIENTS.items():
            print(f"  {short:20s} {info['full_name']}")
        sys.exit(0)

    token = get_token()

    if arg.lower() == "all":
        clients_to_process = list(CLIENTS.items())
    else:
        # Find matching client (case-insensitive)
        match = None
        for short, info in CLIENTS.items():
            if arg.lower() in (short.lower(), info["full_name"].lower()):
                match = (short, info)
                break
        if not match:
            print(f"ERROR: Unknown client '{arg}'. Use --list to see options.", file=sys.stderr)
            sys.exit(1)
        clients_to_process = [match]

    results = {}
    for short_name, client_info in clients_to_process:
        manifest = process_client(token, short_name, client_info)
        results[short_name] = manifest

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for short_name, manifest in results.items():
        if manifest:
            n = len(manifest["calls_to_analyze"])
            f = manifest["filtered_out"]
            print(f"  {short_name:20s} {n} calls to analyze, {f} filtered out")
        else:
            print(f"  {short_name:20s} ERROR - see above")


if __name__ == "__main__":
    main()
