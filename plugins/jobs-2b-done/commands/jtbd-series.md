---
description: Find all meetings in a coaching/training/recurring series for an organization and run JTBD analysis on the full series, building session-by-session context.
argument-hint: "<organization name>"
---

# JTBD Series Analysis

Analyze an entire meeting series for an organization -- coaching engagements, Upskillerator cohorts, weekly meetings, or any recurring relationship. Finds all transcripts, orders them chronologically, and runs JTBD analysis on each with full series context.

## Key References

- **Meeting Transcripts DB**: `8368d3474cac4e71bf945934fce957f7`, collection `669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5`
- **JTBD Analyses DB**: `2f218faa725b41828194e8fc0f93453b`, data source `collection://fbf274fd-5cf0-4afe-9eaf-cb511cae6b94`

## Workflow

### 1. Identify the Organization

- `$ARGUMENTS` is the organization name (e.g., `/jtbd-series Downtown Boxing Gym`)
- If no argument provided, ask the user which organization

### 2. Find All Transcripts for the Organization

Fetch the **Meeting Transcripts** Notion DB and filter for this org:

1. Use `notion-fetch` with `id: "8368d3474cac4e71bf945934fce957f7"` to get all transcripts
2. Filter results for the organization name (also check common abbreviations, e.g., "DBG" for "Downtown Boxing Gym")
3. Collect all matching transcript pages
4. Sort chronologically by date (ascending -- oldest first)

**Do NOT use `notion-search`, `notion-query-meeting-notes`, or `notion-query-database-view`.**

### 3. Check Existing Analyses & Versions

Query the **JTBD Analyses DB** for this organization to find which transcripts have analyses and whether they're current:

1. Filter by `Organization` matching the org name
2. For each record, check:
   - `Meeting Transcript` relation -- which transcript does it cover?
   - `Plugin Version` property -- is it current (`6.1.0`)?
3. Categorize each transcript:
   - **Current** -- has analysis at current plugin version (skip)
   - **Outdated** -- has analysis but older plugin version (needs upgrade)
   - **New** -- no analysis exists (needs full analysis)

### 4. Report and Confirm

```
Series: [Organization Name]
Total transcripts found: [N]

Current (v6.1.0): [A] sessions (skipped)
Outdated (needs upgrade): [B] sessions
  - Session 3 (2025-04-16) — v4.1.0, missing: SERIES, EXPECTATION MAP
  - Session 5 (2025-05-14) — v4.1.0, missing: SERIES, EXPECTATION MAP
New (needs full analysis): [C] sessions
  - Session 8 (2025-06-18) — no analysis
  - Session 9 (2025-06-25) — no analysis

Launching sequential agent for [B+C] sessions.
```

If ALL transcripts are current, report that and offer to run a synthesis instead (`/jtbd-synthesis [org name]`).

### 5. Dispatch Sequential Processing

**Use the two-phase dispatch from SKILL.md** for each session. The key difference from catchup is that series runs **sequentially, not in parallel** -- each session's SERIES section references the previous one.

#### For "New" sessions (full analysis)

For each new session in chronological order:
1. Fetch the full transcript content using `notion-fetch`
2. Extract company name, participants, date
3. **Include series context**: list of prior sessions (Current + already-processed) so the agent can build the SERIES section and reference how expectations shifted
4. Launch a background agent using the **Phase 1 template from SKILL.md**, adding series context to the prompt
5. **Wait for completion** before starting the next session
6. Run **Phase 2 from SKILL.md** (Notion push) before moving to the next session

#### For "Outdated" sessions (upgrade only)

Use the same upgrade agent template as jtbd-catchup (see Step 5, "Outdated" section). Process sequentially with Phase 2 after each.

#### Series-specific rules

- **Sequential, not parallel** -- launch one agent at a time, wait for completion + Phase 2, then proceed to next
- **Series context** -- each agent receives the list of prior sessions (both existing and just-completed) so it can build accurate SERIES sections and track JTBD evolution
- **Long series (20+ sessions)** -- process in batches of 10 to avoid context limits, chaining agents for the next batch

### 6. After Completion

Once the series agent finishes, suggest next steps:
- **Run synthesis**: `/jtbd-synthesis {org name}` to surface patterns across the full series
- **Review evolution**: The SERIES sections in each analysis track how the JTBD shifted session to session
- **Check expectation trends**: The EXPECTATION MAP sections show how the relationship evolved

## Series Types

This command handles any recurring meeting series:

| Series Type | Example | How Detected |
|------------|---------|-------------|
| Coaching | Weekly AI coaching with DBG | Recurring org, "coaching" in title |
| Upskillerator | 6-session cohort program | "Upskillerator" in title, fixed cadence |
| Weekly meeting | Standing team call | Same org, weekly cadence |
| Diagnostic | Multi-session diagnostic | "Diagnostic" in title, 3-5 sessions |
| Training | Multi-day training series | "Training" or "Workshop" in title |

The command doesn't need to distinguish between types -- it finds all transcripts for the org and analyzes them in order regardless.

## Important Notes

- **Sequential, not parallel** -- series context depends on order. Each session references the previous.
- **Idempotent** -- already-analyzed sessions are skipped. Safe to re-run after adding new transcripts.
- **Session numbering** -- determined by chronological position in the full series, not just the unanalyzed subset.
- Transcripts that are cancellations or non-substantive (< 500 words) are skipped and logged.
- For very long series (20+ sessions), the background agent may hit context limits. In that case, it should process in batches of 10 and chain to a new agent for the next batch.
