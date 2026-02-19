---
name: coaching-call-analyzer
description: >
  Stage 1 of the Project Evident pipeline. Retrieves all coaching call transcripts
  from Notion, filters out cancellations and non-sessions, then spawns parallel
  subagents to analyze each transcript independently. Produces transcript copies
  and evaluation files in the client's Working Files folder.
  Use for "analyze call", "evaluate transcript", "run stage 1 for [client]".
---

# Coaching Call Analyzer (Stage 1)

Two-phase architecture running as **autonomous background subagents**:

- **Phase A** (background orchestrator): Retrieves and filters coaching calls from
  Notion, writes raw transcripts and manifest to disk, then spawns Phase B agents.
- **Phase B** (parallel background agents): One per transcript, each with a fresh
  context window for independent analysis.

Both phases run in the background via `run_in_background: true`. The main conversation
stays free for other work. Progress is tracked in `pipeline.log`.

**Plugin version: 1.1.0**

## Prerequisites

- Notion MCP connector for fetching coaching call pages.
- Load these reference files BEFORE launching any background agents:
  - `references/org-mapping.md` -- client page IDs, essentials page IDs, folder names
  - `references/endpoint-map.md` -- the 50 Notion field names (know what you're extracting for)
  - `references/simon-criteria.md` -- the 7 Essential Elements quality gate

**CRITICAL: Background agents cannot access plugin files.** The caller (main agent or
command) MUST read all three reference files and embed their content directly in the
subagent prompt. Do NOT tell subagents to read from `${CLAUDE_PLUGIN_ROOT}` -- they
will not have permission. Instead, include the full text of each reference file in the
prompt itself.

## Constants

```
ARTIFACT_ROOT = ~/Dev/claude-cowork/Clients/Project Evident Updates
PLUGIN_VERSION = 1.1.0
```

---

# PHASE A: Retrieval & Enumeration (Background Orchestrator)

Phase A runs as a background subagent (`run_in_background: true`). It fetches
metadata, filters, writes raw transcripts to disk, produces a manifest, and
then spawns Phase B agents. It should NOT do any analysis itself.

**Launch Pattern (from caller):**

The caller reads all three reference files first, then embeds their content:

```
# Caller reads these before spawning:
org_mapping = Read("${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/org-mapping.md")
endpoint_map = Read("${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/endpoint-map.md")
simon_criteria = Read("${CLAUDE_PLUGIN_ROOT}/skills/coaching-call-analyzer/references/simon-criteria.md")

Task(
  subagent_type: "general-purpose",
  description: "Stage 1 Phase A: {client} retrieval",
  run_in_background: true,
  prompt: "You are the Phase A orchestrator for the Project Evident call analyzer.
    Your job is to retrieve coaching calls from Notion, filter them, write transcripts
    and a manifest to disk, then spawn Phase B analysis agents.

    Client: {Short Name}
    Client Page ID: {client_page_id}
    Essentials Page ID: {essentials_page_id}
    Folder: {ARTIFACT_ROOT}/{folder_name}/

    Follow the Phase A steps below (A0-A6), then execute Phase B (B0-B1).
    Phase B agents should also run in background (run_in_background: true).

    IMPORTANT: When spawning Phase B agents, embed the endpoint-map and simon-criteria
    content directly in each agent's prompt (shown below). Phase B agents cannot read
    plugin files.

    ## Reference: Org Mapping
    {org_mapping content}

    ## Reference: Endpoint Map
    {endpoint_map content}

    ## Reference: Simon Criteria
    {simon_criteria content}

    After Phase B agents are launched, write a PHASE_A_COMPLETE entry to pipeline.log
    and return the manifest summary. Phase B results will arrive asynchronously."
)
```

**The caller does NOT wait for Phase A to finish.** It launches the background
agent and returns immediately. The user checks progress via `pipeline.log` or
by reading the output files.

## Step A0: Resolve Client and Validate IDs

1. Match the client name/shortname to org-mapping.md.
2. Extract these three values -- ALL are required:
   - `client_page_id` -- Clients DB Page ID
   - `essentials_page_id` -- Essentials DB Page ID
   - `folder_name` -- e.g., "ALAS Working Files"

3. **HALT if `client_page_id` or `essentials_page_id` is missing or empty.** Do not
   proceed. Report: "Cannot run Stage 1 for {client}: missing {which ID} in org-mapping.md."

4. Create folder structure if it doesn't exist:
   ```bash
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/1-transcripts"
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/2-evaluations"
   mkdir -p "${ARTIFACT_ROOT}/{folder_name}/3-essentials"
   ```

## Step A1: Fetch Client Page and Enumerate Coaching Calls

1. Fetch the client org page using `client_page_id` via Notion MCP `fetch` tool.
2. Extract the **Coaching Calls** relation -> list of coaching call page IDs.
3. Log: "Found {N} pages in Coaching Calls relation."

## Step A2: Fetch and Filter Each Coaching Call Page

For each page ID in the Coaching Calls relation, fetch the page via Notion `fetch`.

**Apply these filters IN ORDER:**

### Filter 1: Page Type
Read the `Page Type` property.
- `"Cancellation"` -> **SKIP**, log as cancelled
- `"THS Cancelled"` -> **SKIP**, log as THS-side cancellation
- `"Client Page"` -> **SKIP**, this is the org page itself (shouldn't be here but sometimes is)
- `"Coaching Call"` -> **CONTINUE to Filter 2**
- Any other value -> **CONTINUE with caution**, log the unexpected type

### Filter 2: Transcript Content
Read the `Transcript` property (NOT the page body -- the transcript is a property field).
- Property missing, empty, or "No transcript available" -> **SKIP**, log: "No transcript content"
- Content is under 500 characters -> **Check Filter 3** (might be a cancellation note)
- Content is 500+ characters -> **CONTINUE to Filter 3**

### Filter 3: Not-A-Call Check
Read the `Call Evaluation` property if it exists.
- Starts with "NOT A COACHING CALL" -> **SKIP**, log: "Marked as not a coaching call"
- Otherwise -> **PASS** -- this is a real coaching call with a transcript

**For pages that pass all filters:**
- Extract: date (from page properties or content), attendees (if visible), title
- Assign a sequential call number based on date ordering (earliest = Call 1)

## Step A3: Sort and Number Calls

1. Sort all passing calls by date (earliest first).
2. Assign sequential call numbers: Call 1, Call 2, Call 3, etc.
3. This ensures consistent numbering regardless of Notion page order.

## Step A4: Write Raw Transcripts to Disk

For each passing call, write the raw transcript:

**File:** `{ARTIFACT_ROOT}/{folder_name}/1-transcripts/call-{N}-transcript.md`

```markdown
---
client: {Short Name}
client_page_id: {from org-mapping}
transcript_page_id: {Notion page ID of this coaching call}
session: {N}
date: {YYYY-MM-DD}
title: {page title from Notion}
plugin_version: 1.1.0
created_at: {ISO 8601 timestamp}
---

{Raw transcript content from Notion -- verbatim, no analysis}
```

**NOTE:** The raw transcript content comes from the `Transcript` property on the
coaching call page, NOT from the page body. Use `notion-fetch` or `get-design-content`
to read the full property value.

**HALT if `transcript_page_id` can't be resolved.** Don't write a file with a blank ID.

## Step A5: Write Manifest File

After writing ALL transcripts, write a manifest that Phase B will use to spawn agents:

**File:** `{ARTIFACT_ROOT}/{folder_name}/1-transcripts/manifest.json`

```json
{
  "client": "{Short Name}",
  "client_page_id": "{from org-mapping}",
  "essentials_page_id": "{from org-mapping}",
  "folder_name": "{folder_name}",
  "plugin_version": "1.1.0",
  "created_at": "{ISO 8601 timestamp}",
  "total_pages_in_relation": {N},
  "filtered_out": {count},
  "calls_to_analyze": [
    {
      "call_number": 1,
      "transcript_page_id": "{Notion page ID}",
      "date": "YYYY-MM-DD",
      "title": "{page title}",
      "transcript_file": "1-transcripts/call-1-transcript.md"
    },
    ...
  ],
  "skipped": [
    {
      "page_id": "{id}",
      "title": "{title}",
      "reason": "Cancellation" | "No transcript" | "Not a coaching call" | "THS Cancelled"
    },
    ...
  ]
}
```

## Step A6: Log Phase A Completion

Append to pipeline.log:
```
[{ISO 8601 timestamp}] [v1.1.0] [stage-1:phase-a:retrieval] [{Short Name}]
  Status: SUCCESS
  Total pages in relation: {N}
  Filtered out: {count} ({reasons})
  Calls to analyze: {count}
  Transcript files written: {list}
  Manifest: 1-transcripts/manifest.json
```

---

# PHASE B: Parallel Analysis (Background Subagents)

Phase B spawns one background Task subagent per transcript (`run_in_background: true`).
Each subagent gets its own context window -- this is why the architecture works for
clients with many calls. All Phase B agents run concurrently in the background.

## Step B0: Read Manifest and Prepare Subagent Launches

1. Read `1-transcripts/manifest.json`.
2. For each entry in `calls_to_analyze`, prepare a subagent prompt.

## Step B1: Spawn Parallel Background Subagents

**CRITICAL: Launch ALL subagents in a SINGLE message using multiple Task tool calls,
each with `run_in_background: true`.** This runs them concurrently in the background.

For each call in the manifest, spawn:

```
Task(
  subagent_type: "general-purpose",
  description: "Analyze {client} call {N}",
  run_in_background: true,
  prompt: "You are analyzing a single coaching call transcript for a Project Evident
    coaching client. Your job is to perform semantic topic clustering, speaker attribution,
    component-level evaluation, and Essential Elements coverage tracking.

    ## Context
    Client: {Short Name}
    Client Page ID: {client_page_id}
    Essentials Page ID: {essentials_page_id}
    Call Number: {N}
    Date: {date}
    Transcript Page ID: {transcript_page_id}

    ## Instructions

    1. Read the transcript file at: {ARTIFACT_ROOT}/{folder_name}/1-transcripts/call-{N}-transcript.md

    2. Use the reference content embedded below (Endpoint Map and Simon Criteria)
       for evaluation criteria. Do NOT try to read plugin files.

    3. Perform the analysis described below (Topic Clustering, Speaker Attribution,
       Component Evaluation, Essential Elements Scorecard).

    4. Write the evaluation file to:
       {ARTIFACT_ROOT}/{folder_name}/2-evaluations/call-{N}-evaluation.md

    5. Append a log entry to:
       {ARTIFACT_ROOT}/{folder_name}/pipeline.log

    ## Analysis Steps

    ### Topic Clustering
    Break the transcript into Topic Clusters:
    - Unified semantic theme, natural conversation boundaries
    - 300-2000 words typical, may overlap if genuinely multi-topic

    For each cluster:
    - Number, descriptive name (5-10 words), time range, ~word count
    - Coherence (High / Medium / Low)

    Embedding rule: If a cluster is under ~1000 words, include the FULL cluster
    text in the evaluation. Don't summarize small clusters -- Stage 2 needs the
    material. For clusters over ~1000 words, write a rich summary that preserves
    ALL specifics: tool names, people names, data types, numbers, process steps.

    ### Speaker Attribution Log
    For each notable statement, log:

    {Name} (client): \"{What they said or did}\"
      Context: Unprompted | Response to coach | Repeated theme | Demonstrated action
      Weight: Calculated together | Repeated across sessions | Said with conviction | Passing comment
      Components: C1P1, C4, etc.

    {Tim} (coach): \"{What Tim said}\"
      Context: Introduced concept | Asked question | Demonstrated tool
      NOTE: Coach statements = context, not evidence of client adoption.

    Weight rules:
    1. Numbers calculated together in session -> strongest
    2. Client action taken between sessions -> strong
    3. Client returning to topic across sessions -> strong
    4. Client describing in own words -> moderate
    5. Coach introduced, client used in own words later -> moderate
    6. Client passing comment once -> weak
    7. Coach introduced, client nodded -> NOT evidence

    Value discovery signals -- scan for ALL of these:
    - Direct time questions: \"How long?\" / \"How many hours?\"
    - Frequency multipliers: \"How often?\" / \"Is that weekly?\"
    - Cost comparisons: \"What do you pay?\" / \"How much is the consultant?\"
    - Game-changing signals: \"This is huge\" / \"golden ticket\"
    - Before/after contrasts
    - Capacity language: \"freed up\" / \"used to take\" / \"now it's\"
    - Team impact: \"my staff\" / \"everyone\" / \"we've been using it\"

    ### Component-Level Evaluation
    Evaluate each cluster against 7 component/phase buckets:

    | Bucket | What to Look For |
    |--------|-----------------|
    | C1P1: Pain Point | Specific operational challenge, quantified impact, team alignment |
    | C1P2: AI Solution | Tools discussed/selected, cost/fit considerations |
    | C2: Policy | AI policy work, governance, data ethics |
    | C3P1: Foundation | Tools purchased, data identified, integrations |
    | C3P2: Testing | Pilot running, test results, training, feedback |
    | C3P3: Rollout | Full team using it, system operational |
    | C4: Progress | Before/after comparisons, savings, productivity, outcomes |

    For each bucket touched:
    - Confidence score (0-100%)
    - What's present vs. what's missing
    - Which attribution log entries support it

    Determine call type and confidence threshold:

    | Call Type | Threshold | When |
    |-----------|-----------|------|
    | Rapport | 60% | Early relationship building |
    | Exploration | 70% | Testing ideas, building understanding |
    | Traction | 70% | Clear implementation work |
    | Wrap | 70% | Confirmed achievements |

    ### Essential Elements Scorecard
    Track which of Simon's 7 Essential Elements are addressed with actual content.
    (See simon-criteria.md for specificity tests.)

    ## Output Format

    Write the evaluation file with this exact structure:

    ---
    client: {Short Name}
    client_page_id: {client_page_id}
    essentials_page_id: {essentials_page_id}
    transcript_page_id: {transcript_page_id}
    session: {N}
    date: {date}
    call_type: {Rapport|Exploration|Traction|Wrap}
    plugin_version: 1.1.0
    created_at: {ISO 8601 timestamp}
    source_transcript: ../1-transcripts/call-{N}-transcript.md
    ---

    # Call {N} Evaluation: {Org Name}

    ## Call Info
    Call No. {N}: {Call Type} with {Org Name}
    {type} | {duration} | {#} Attendees: {names}

    ## Topic Clusters

    ### #{num}: {Topic Name}
    {duration} | ~{word count} words

    {Full text if <1000 words, OR rich summary preserving all specifics}

    Component Coverage:
      C1P1 Pain Point: {Yes/No} ({confidence}%) -- {1-line what's there}
      C1P2 Solution: {Yes/No} ({confidence}%) -- {1-line what's there}
      C2 Policy: {Yes/No} ({confidence}%) -- {1-line what's there}
      C3P1 Foundation: {Yes/No} ({confidence}%) -- {1-line what's there}
      C3P2 Testing: {Yes/No} ({confidence}%) -- {1-line what's there}
      C3P3 Rollout: {Yes/No} ({confidence}%) -- {1-line what's there}
      C4 Progress: {Yes/No} ({confidence}%) -- {1-line what's there}

    Essential Elements addressed: {list with actual content found}

    {Repeat for each cluster}

    ## Speaker Attribution Log
    {Full attribution log}

    ## Session Coverage Summary

    Component     | Clusters | Confidence | What's There
    C1P1 Pain Pt  | #1, #3   | 85%        | {summary}
    C1P2 Solution | #2       | 72%        | {summary}
    C2 Policy     |          |            |
    C3P1 Found.   |          |            |
    C3P2 Testing  |          |            |
    C3P3 Rollout  |          |            |
    C4 Progress   |          |            |

    ## Essential Elements Scorecard

    Element              | Status      | Content Found
    AI Tech              | Specific    | {actual content}
    Personnel            | Named       | {actual content}
    Data                 | Vague       | {what's there, what's missing}
    Pre-AI Workflow      | Missing     | --
    Post-AI Workflow     | Missing     | --
    Quantitative Impact  | Measured    | {actual content}
    Qualitative Impact   | Partial     | {what's there, what's missing}

    ## Wins
    {Best client achievement this session}

    ## Best Client Quote
    {Direct quote -- not Tim, not Human Stack staff}

    ## Essential Elements Gaps
    {What's missing and which future session should target it}

    ## Pipeline Log Entry

    After writing the evaluation file, append to pipeline.log:

    [{ISO 8601 timestamp}] [v1.1.0] [stage-1:phase-b:analyzer] [{Short Name}] [call-{N}]
      Status: SUCCESS
      Output: 2-evaluations/call-{N}-evaluation.md
      transcript_page_id: {Notion page ID}
      session: {N}
      date: {date}
      call_type: {type}
      topics: {#} clusters
      confidence: {best confidence}%

    ## Reference: Endpoint Map
    {endpoint_map content -- embedded by the Phase A orchestrator}

    ## Reference: Simon Criteria
    {simon_criteria content -- embedded by the Phase A orchestrator}

    Return to the caller: SUCCESS, file path, call type, top-level Essential Elements scorecard.
  "
)
```

**IMPORTANT CONSTRAINTS on subagent spawning:**
- Launch ALL subagents in a SINGLE response with multiple Task tool calls
- Every subagent uses `run_in_background: true` -- they run autonomously
- Each subagent analyzes exactly ONE transcript
- Each subagent reads its own reference files (fresh context window)
- Each subagent writes its own evaluation file and log entry
- If a client has 8 calls, spawn 8 background subagents simultaneously
- The orchestrator does NOT wait for Phase B agents to finish -- it logs
  the launch and returns. Each agent writes its own SUCCESS/FAILED to pipeline.log

## Step B2: Log Phase B Launch (Orchestrator)

The Phase A orchestrator does NOT wait for Phase B agents to return. Instead:

1. Log the launch of all Phase B agents to pipeline.log:
   ```
   [{ISO 8601 timestamp}] [v1.1.0] [stage-1:phase-b:launched] [{Short Name}]
     Status: AGENTS_LAUNCHED
     Agents spawned: {N} (one per transcript)
     Calls: call-1 through call-{N}
     Mode: background (run_in_background: true)
     Monitor: Check pipeline.log for per-call SUCCESS/FAILED entries
   ```

2. Return to the caller with: manifest summary, how many agents were spawned,
   and instruction to monitor pipeline.log.

**Each Phase B agent is responsible for writing its own SUCCESS/FAILED log entry
when it finishes.** The pipeline.log becomes the coordination mechanism.

## Step B3: Completion Detection (Evaluator/Caller)

The evaluator (or user) checks whether Stage 1 is fully complete by:

1. Reading `1-transcripts/manifest.json` to get the expected call count.
2. Counting evaluation files in `2-evaluations/` that match `call-*-evaluation.md`.
3. Reading `pipeline.log` for per-call SUCCESS/FAILED entries from `stage-1:phase-b:analyzer`.

**Stage 1 is complete when:** evaluation file count matches manifest `calls_to_analyze` count.

If some agents are still running (fewer evaluations than expected), the evaluator
reports partial progress and can be re-checked later.

When all agents have finished, the evaluator writes:

```
[{ISO 8601 timestamp}] [v1.1.0] [stage-1:complete] [{Short Name}]
  Status: COMPLETE
  Calls analyzed: {N} of {total in manifest}
  Successes: {count}
  Failures: {count} ({which ones})
  Call types: Call 1={type}, Call 2={type}, ...
  Ready for Stage 2: {YES/NO}
```

## Step B4: Report to User

When asked for status (or when the evaluator detects completion), present:
- How many coaching call pages were in the relation
- How many were filtered out (with reasons)
- How many have been analyzed so far (of total expected)
- For each completed call: session number, date, call type, top Essential Elements
- Any failures and why
- Whether all agents have finished or some are still running
- File paths written
- Recommendation: "Stage 1 complete. Run Stage 2 to populate essentials."
  OR "Stage 1 in progress. {N} of {M} calls analyzed. Check back shortly."

---

## What This Skill Produces

Per call:
- `1-transcripts/call-{N}-transcript.md` -- raw Notion transcript with frontmatter
- `2-evaluations/call-{N}-evaluation.md` -- analytical output with attribution log,
  component coverage, Essential Elements scorecard

Per client:
- `1-transcripts/manifest.json` -- enumeration of all calls and filtering decisions
- Appended entries in `pipeline.log`

## What This Skill Does NOT Do

- Write to Notion (file system is the artifact store)
- Extract 50 field-level values (that's Stage 2: essentials-populator)
- Generate the Essentials document or summary sentence
- Track or recommend component statuses
- Advance to Stage 2 (that's the evaluator's job)
- Generate extra summary reports or scorecards not specified above
