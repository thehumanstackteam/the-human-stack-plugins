---
description: Find meeting transcripts from the past week (or N days) that don't have a JTBD analysis yet, and run analysis on each one as background agents.
argument-hint: "[days back, default 7]"
---

# JTBD Catchup

Find unanalyzed meeting transcripts and run JTBD analysis on each. Designed to be run manually (`/jtbd-catchup`) or scheduled via `claude -p "/jtbd-catchup"`.

## Key References

- **Meeting Transcripts DB**: `8368d3474cac4e71bf945934fce957f7`, collection `669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5`
- **JTBD Analyses DB**: `2f218faa725b41828194e8fc0f93453b`, data source `collection://fbf274fd-5cf0-4afe-9eaf-cb511cae6b94`

## Workflow

### 1. Determine Time Window

- If `$ARGUMENTS` is a number, use that as days back (e.g., `/jtbd-catchup 14` = past 14 days)
- If no argument, default to **7 days**
- Calculate the cutoff date: today minus N days

### 2. Find Unanalyzed or Outdated Transcripts

Query the **Meeting Transcripts** Notion DB for recent transcripts that need analysis (new or outdated):

1. Use `notion-query-database-view` with data source `collection://669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5`
2. Filter: created date >= cutoff date
3. For each transcript, check the **JTBD Analyses** relation property:
   - **Empty** → needs analysis (new)
   - **Has relation** → fetch the linked JTBD Analyses page and check the `Plugin Version` property

#### Version Check

For transcripts that already have an analysis, compare the analysis's `Plugin Version` against the current plugin version (`5.0.0`):

- **No `Plugin Version` property** → pre-v5, needs upgrade
- **Version < current** → outdated, needs upgrade
- **Version = current** → up to date, skip

#### Categorize Results

Group transcripts into three buckets:
- **New** — no analysis exists
- **Outdated** — analysis exists but was created by an older plugin version
- **Current** — analysis exists at current version (skip these)

### 3. Report Findings

Before launching agents, report to the user:

```
Found [N] transcripts needing work in the past [days] days:

New (no analysis):
1. [Date] - [Title] - [Organization]

Outdated (needs upgrade from v[X] to v5.0.0):
2. [Date] - [Title] - [Organization] — missing: SERIES, EXPECTATION MAP
3. [Date] - [Title] - [Organization] — missing: EXPECTATION MAP

Up to date: [M] transcripts (skipped)

Launching [K] background agents.
```

If nothing needs work, report that and exit.

### 4. Dispatch Background Agents

Handle each transcript based on its category:

#### New Transcripts (no analysis exists)

For each, launch a background agent following the JTBD Analysis dispatch pattern (see `jtbd-analysis.md` Dispatch Architecture):

1. **Read the transcript** from Notion using `notion-fetch`
2. **Extract** company name, participants, date from the transcript content and properties
3. **Launch background agent** with the full transcript text and context

```
Agent(
  subagent_type: "general-purpose",
  description: "JTBD Catchup: {company} ({date})",
  run_in_background: true,
  prompt: "You are the autonomous JTBD analysis runner...
    [same prompt template as jtbd-analysis.md Dispatch Architecture]
    ...with this transcript:
    {full_transcript_text}"
)
```

#### Outdated Transcripts (analysis exists, older version)

For each, launch a background agent that upgrades the existing analysis using the batch upgrade logic (see `jtbd-analysis.md` Step 7b):

1. **Fetch the existing analysis** from the Notion JTBD Analyses page
2. **Fetch the raw transcript** from the linked Meeting Transcript relation
3. **Determine what's missing** based on version (e.g., pre-v5 = missing SERIES + EXPECTATION MAP)
4. **Backfill missing sections**:
   - SERIES: Query DB for session count, insert after CONTEXT METADATA
   - EXPECTATION MAP: Run `uxinator:expectation-mapper` against the raw transcript, append
   - Plugin Version: Add/update to current version
5. **Update both** the local .md file and the Notion page body (full text, no truncation)

```
Agent(
  subagent_type: "general-purpose",
  description: "JTBD Upgrade: {company} ({date}) v{old} -> v5.0.0",
  run_in_background: true,
  prompt: "You are the autonomous JTBD upgrade runner.
    Upgrade this existing analysis to v5.0.0.

    ## Existing Analysis (Notion page)
    {notion_page_url}

    ## Raw Transcript (for Expectation Map)
    {transcript_notion_url}

    ## Missing Sections
    {list of what needs to be added}

    ## Instructions
    - Fetch the existing analysis page content
    - Fetch the raw transcript
    - Add missing sections per jtbd-analysis.md Step 7b
    - Update Plugin Version to 5.0.0
    - Update the local .md file at {file_path}
    - Update the Notion page body with FULL text (use curl fallback if needed)
    - Update the Plugin Version property on the Notion DB record

    Do NOT re-run the full JTBD analysis. Only add the missing sections.
    Do NOT modify existing sections."
)
```

**Launch all agents (new + upgrade) in a single message** for maximum parallelism.

### 5. Summary

After dispatching all agents, tell the user:
- How many analyses are running
- Where files will be saved (`/Users/tim/Dev/claude-cowork/Clients/[Org]/Meetings/Analysis/`)
- That each will also push to the JTBD Analyses Notion DB
- Do NOT block waiting for results

## Scheduling

This command is designed for `claude -p` automation:

```bash
# Run weekly via cron (Sunday night)
0 22 * * 0 claude -p "/jtbd-catchup 7" --allowedTools '*'

# Run daily catchup
0 6 * * * claude -p "/jtbd-catchup 1" --allowedTools '*'
```

## Important Notes

- Transcripts that are cancellations, rescheduling notices, or non-substantive should be skipped. Check the transcript title and content -- if it's clearly not a real session, skip it.
- If a transcript has fewer than 500 words of actual conversation, skip it and log as "too short."
- Each background agent runs the full pipeline: JTBD analysis, series context, expectation map, CRM lookups, file save, Notion push.
- This command never asks questions. It finds work, dispatches it, and reports.
