#!/usr/bin/env python3
"""
update-status.py - Update the Status field on a client's Essentials page in Notion.

Called by every pipeline agent at each stage transition. This is the live heartbeat.

Usage:
    python3 update-status.py ALAS "Pulling Transcripts"
    python3 update-status.py ALAS "Analyzing Calls"
    python3 update-status.py ALAS "Populating Fields"
    python3 update-status.py ALAS "Quality Gate"
    python3 update-status.py ALAS "Pushing to Notion"
    python3 update-status.py ALAS "Pushed To Document"
    python3 update-status.py ALAS "Revise"
    python3 update-status.py ALAS "Waiting for Review"

Requires: NOTION_API_KEY env var
"""

import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
STATUS_PROPERTY = "Status"

VALID_STATUSES = [
    "Pulling Transcripts",
    "Analyzing Calls",
    "Populating Fields",
    "Quality Gate",
    "Pushing to Notion",
    "Pushed To Document",
    "Revise",
    "Waiting for Review",
]

CLIENTS = {
    "ALAS": "cbafaee4b7334746988ea76d39f7e9ed",
    "Building Promise": "20f0abcb1b914e43aab9cc267df71d1c",
    "CPA": "a7eab654617c4031bef40af65822c007",
    "CHDC": "cb71fd8d747a4ae6b37583cdf962fc6d",
    "E4": "a6b5553660124314b0394168503922e4",
    "EDC": "01c62bde3bb6431eb10af51987b40546",
    "LAA": "5e9704da19594e1dbcbd16d7b667c0f1",
    "SV@Home": "10a3c22b981b4de4baedddb2d844c63f",
    "Sumter": "bc1e39451152408e8492d94af6a68ffa",
    "TAP": "5f99201e619e4c6688d2df2bd5be842b",
    "TIP": "f41fb0c3396d4a63aa13bb9b591bf9ee",
}


def get_token():
    token = os.environ.get("NOTION_API_KEY")
    if not token:
        print("ERROR: NOTION_API_KEY env var not set.", file=sys.stderr)
        sys.exit(1)
    return token


def update_status(token, page_id, status):
    url = f"{NOTION_API}/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    body = {
        "properties": {
            STATUS_PROPERTY: {
                "select": {"name": status}
            }
        }
    }
    data = json.dumps(body).encode()
    req = Request(url, data=data, headers=headers, method="PATCH")
    try:
        with urlopen(req) as resp:
            return True
    except HTTPError as e:
        error_body = e.read().decode()
        print(f"Notion API error {e.code}: {error_body}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 update-status.py <client> <status>")
        print(f"Valid statuses: {', '.join(VALID_STATUSES)}")
        sys.exit(1)

    client_arg = sys.argv[1]
    status = sys.argv[2]

    if status not in VALID_STATUSES:
        print(f"ERROR: Invalid status '{status}'.", file=sys.stderr)
        print(f"Valid: {', '.join(VALID_STATUSES)}", file=sys.stderr)
        sys.exit(1)

    page_id = None
    for name, pid in CLIENTS.items():
        if client_arg.lower() == name.lower():
            page_id = pid
            client_arg = name
            break

    if not page_id:
        print(f"ERROR: Unknown client '{client_arg}'.", file=sys.stderr)
        sys.exit(1)

    token = get_token()

    if update_status(token, page_id, status):
        print(f"OK: {client_arg} -> {status}")
    else:
        print(f"FAILED: {client_arg} -> {status}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
