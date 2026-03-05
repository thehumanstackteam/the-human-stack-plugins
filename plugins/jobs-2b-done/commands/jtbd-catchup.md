---
description: Find meeting transcripts from the past week (or N days) that don't have a JTBD analysis yet, and run analysis on each one as background agents.
argument-hint: "[days back, default 7]"
---

# JTBD Catchup

Find unanalyzed meeting transcripts and run JTBD analysis on each. Designed to be run manually (`/jtbd-catchup`) or scheduled via `claude -p "/jtbd-catchup"`.

**DO NOT check the filesystem. DO NOT check the JTBD Analyses DB first. DO NOT use `notion-query-meeting-notes` (that queries Notion's built-in notetaker, which is WRONG). START by querying the Meeting Transcripts Notion database using `notion-query-database-view`.**

## Step 1: Determine Time Window

- If `$ARGUMENTS` is a number, use that as days back (e.g., `/jtbd-catchup 14` = past 14 days)
- If no argument, default to **7 days**
- Calculate the cutoff date: today minus N days

## Step 2: Fetch the Meeting Transcripts Database

**Use `notion-fetch` with the database ID. Do NOT use `notion-search`, `notion-query-meeting-notes`, or `notion-query-database-view`.**

```
notion-fetch({ id: "8368d3474cac4e71bf945934fce957f7" })
```

This returns all pages in the Meeting Transcripts database. Filter the results for transcripts created in the past N days.

## Step 3: For Each Transcript, Check if a JTBD Analysis Exists

Each transcript page in the Meeting Transcripts DB has a **"JTBD Analyses"** relation property. This relation links to the JTBD Analyses DB (`collection://fbf274fd-5cf0-4afe-9eaf-cb511cae6b94`).

For each transcript returned in Step 2:
1. Check the **"JTBD Analyses"** relation on the transcript page
2. If the relation is **empty** → this transcript has NO analysis → mark as **"New"**
3. If the relation has a value → fetch that JTBD Analyses page and check its `Plugin Version` property:
   - No `Plugin Version` or version < `6.1.0` → mark as **"Outdated"**
   - Version >= `6.1.0` → mark as **"Current"** (skip)

## Step 4: Report Findings

```
Checked [total] transcripts from the past [N] days:

New (no analysis):
1. [Date] - [Title] - [Organization]
2. [Date] - [Title] - [Organization]

Outdated (needs upgrade):
3. [Date] - [Title] - [Organization] — v4.1.0, missing: SERIES, EXPECTATION MAP

Up to date: [M] transcripts (skipped)

Launching [K] background agents.
```

If nothing needs work, report "All [total] transcripts from the past [N] days have current analyses." and exit.

## Step 5: Dispatch Background Agents

**Use the two-phase dispatch from SKILL.md.** Read the SKILL.md "Dispatch Architecture (Two-Phase)" section for the canonical agent prompt template and Phase 2 procedure.

### For "New" transcripts (no analysis exists)

1. Fetch the full transcript content using `notion-fetch` with the transcript's page URL
2. Extract company name, participants, date from the transcript content and properties
3. Launch a background agent using the **Phase 1 template from SKILL.md**, filling in `{company}`, `{participants}`, `{date}`, `{full_transcript_text}`, and `{notion_transcript_url}`

### For "Outdated" transcripts (analysis exists, older version)

1. Fetch the existing JTBD Analyses page content
2. Fetch the raw transcript from the linked Meeting Transcript
3. Launch a background agent to upgrade:

```
Agent(
  subagent_type: "general-purpose",
  description: "JTBD Upgrade: {company} ({date}) v{old} -> v6.1.0",
  run_in_background: true,
  prompt: "You are the autonomous JTBD upgrade runner.
    Upgrade this existing analysis to v6.1.0. Do NOT re-run the full analysis.

    ## Existing Analysis
    Notion page: {analysis_notion_url}

    ## Raw Transcript
    Notion page: {transcript_notion_url}

    ## Missing Sections
    {list of what needs to be added}

    ## Instructions
    - Fetch the existing analysis page content from Notion
    - Fetch the raw transcript from Notion
    - Add SERIES section after CONTEXT METADATA (query DB for session count)
    - Run uxinator:expectation-mapper against raw transcript, append as EXPECTATION MAP
    - Add Plugin Version: 6.1.0 to CONTEXT METADATA
    - Update the local .md file at the File Path property value

    YOUR JOB ENDS after saving the file. Do NOT push to Notion.
    Do NOT call notion-create-pages, notion-update-page, or any Notion write tool.

    When complete, output the JTBD_COMPLETE status block (see SKILL.md).

    Do NOT modify existing analysis sections.
    Do NOT re-run the JTBD analysis. Only add missing sections."
)
```

**Launch all agents in a single message** for maximum parallelism.

### Phase 2: After All Agents Complete

Run the **Phase 2 batch loop from SKILL.md** for each completed agent — read .md from disk, push to Notion as deterministic passthrough, verify, backfill transcript Organization.

## Step 6: Summary

After dispatching, tell the user:
- How many analyses are running (new + upgrade)
- Where files will be saved
- Do NOT block waiting for results
- Phase 2 (Notion push) will run after all agents finish

## Scheduling

```bash
# Daily catchup at 6am
0 6 * * * claude -p "/jtbd-catchup 1" --allowedTools '*'

# Weekly catchup Sunday night
0 22 * * 0 claude -p "/jtbd-catchup 7" --allowedTools '*'
```

## Rules

- **ALWAYS start with the Notion Meeting Transcripts database query.** Never check the filesystem first.
- Transcripts that are cancellations or non-substantive (< 500 words) → skip and log
- This command never asks questions. It finds work, dispatches it, and reports.
- Each background agent runs autonomously — do not block waiting for results.
