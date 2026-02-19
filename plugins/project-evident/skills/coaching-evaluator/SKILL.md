---
name: coaching-evaluator
description: >
  Pipeline controller and router for all Project Evident coaching work. Reads pipeline
  state from the log and filesystem, validates before advancing stages, manages HITL
  review cycle, generates JSON payload, pushes to Notion on approval. The single entry
  point for "process [client]", "status on [client]", "push [client]", "batch".
---

# Coaching Evaluator (Pipeline Controller)

The front door for all Project Evident coaching work. Reads the pipeline log, validates
filesystem state, dispatches Stage 1 and Stage 2, manages the HITL review cycle,
generates the JSON payload, and pushes to Notion on Tim's approval.

**This skill knows what has and hasn't been done.** It reads `pipeline.log` and checks
the filesystem before doing anything. It never assumes a prior stage succeeded.

**Plugin version: 1.1.0**

## Prerequisites

- Notion MCP connector (read + write via `update-page-properties`).
- Load these reference files BEFORE routing or spawning any background agents:
  - `references/org-mapping.md` -- client page IDs, essentials page IDs, folder names
  - `references/endpoint-map.md` -- exact Notion property names and types (all 50 fields)
  - `references/simon-criteria.md` -- the 7 Essential Elements quality gate

**CRITICAL: Background agents cannot access plugin files.** Read all three reference
files and embed their content directly in every subagent prompt. Do NOT tell subagents
to read from `${CLAUDE_PLUGIN_ROOT}` -- they will not have permission.

## Constants

```
ARTIFACT_ROOT = ~/Dev/claude-cowork/Clients/Project Evident Updates
PLUGIN_VERSION = 1.1.0
```

## Routing Logic

Parse the request and determine the workflow:

| Request Pattern | Route |
|----------------|-------|
| "process [client]" / "run pipeline" / "full run" | **Full pipeline**: validate -> analyze (background) -> populate -> HITL -> push |
| "analyze call" / "new transcript" / "run stage 1" | **Stage 1 only**: validate -> dispatch call analyzer (background) |
| "populate essentials" / "fill endpoints" / "run stage 2" | **Stage 2 only**: validate -> dispatch essentials populator (background) |
| "push [client]" / "push to notion" / "approve" | **Push**: validate -> generate JSON -> push to Notion |
| "status on [client]" / "where is [client]" | **Status check**: read log + filesystem, report state |
| "batch" / "all clients" / "run everyone" | **Batch**: full pipeline for all 11 clients |

When ambiguous, default to **status check** -- it's the lightest lift and surfaces
whether deeper work is needed.

## Step 0: Resolve Client and Read Pipeline State

**For every route, always do this first:**

1. Match client name/shortname to org-mapping.md.
2. Extract `client_page_id`, `essentials_page_id`, `folder_name`.
3. **HALT if either Notion ID is missing.**

4. Set working directory: `{ARTIFACT_ROOT}/{folder_name}/`

5. **Read pipeline state** by checking both the log AND the filesystem:

   ```
   Check: Does pipeline.log exist?
   Check: Does 1-transcripts/manifest.json exist?
   Check: Any transcript files in 1-transcripts/?
   Check: Any Stage 1 phase-a SUCCESS entries in log?
   Check: Any AGENTS_LAUNCHED entries in log?
   Check: Any Stage 1 phase-b SUCCESS entries in log?
   Check: Any files in 2-evaluations/?
   Check: Does manifest call count match evaluation file count?
   Check: Any Stage 2 SUCCESS entry in log?
   Check: Does 3-essentials/essentials-review.md exist?
   Check: Any WAITING_FOR_HITL entry in log?
   Check: Any PUSHED_TO_NOTION entry in log?
   Check: Does 3-essentials/essentials-payload.json exist?
   Check: Any FAILED entries in log?
   ```

6. **Cross-validate log vs. filesystem:**
   - Log says Phase A SUCCESS but no manifest.json -> ERROR: "Phase A logged but manifest missing. Re-run Stage 1."
   - AGENTS_LAUNCHED in log but evaluation count < manifest count -> IN_PROGRESS: "Phase B agents still running. {N} of {M} complete."
   - Manifest exists but evaluation count < manifest call count -> WARNING: "Only {N} of {M} calls analyzed. Some subagents may still be running or may have failed."
   - Log says Stage 1 SUCCESS but no files in `2-evaluations/` -> ERROR: "Log says Stage 1 ran but evaluation files are missing. Re-run Stage 1."
   - Files exist in `2-evaluations/` but no log entry -> WARNING: "Found evaluation files but no log entry -- may be from a previous plugin version. Proceeding with caution."
   - Log says Stage 2 SUCCESS but no `essentials-review.md` -> ERROR: "Log says Stage 2 ran but review file is missing. Re-run Stage 2."

7. Determine current state:

   | State | Condition | Next Action |
   |-------|-----------|-------------|
   | NOT_STARTED | No log, no files | Run Stage 1 |
   | PHASE_A_DONE | Manifest exists, no evaluations, AGENTS_LAUNCHED in log | Wait -- Phase B agents are running |
   | STAGE_1_IN_PROGRESS | Some evaluations exist but fewer than manifest count | Wait -- background agents still running. Report progress. |
   | STAGE_1_PARTIAL | Evaluations < manifest AND no new log entries for 10+ min | Some agents may have failed. Offer to re-run missing calls. |
   | STAGE_1_DONE | All evaluations exist matching manifest | Run Stage 2 |
   | STAGE_2_IN_PROGRESS | Stage 2 dispatched (log entry exists) but no essentials-review.md yet | Wait -- background agent running |
   | STAGE_2_DONE | Stage 2 SUCCESS in log + essentials-review.md exists | Present for HITL |
   | WAITING_FOR_HITL | WAITING_FOR_HITL in log | Wait for Tim |
   | PUSHED | PUSHED_TO_NOTION in log | Report done |
   | FAILED | Any FAILED entry (most recent) | Show error, suggest fix |

## Route: Full Pipeline

1. Read state (Step 0).
2. If NOT_STARTED or no Stage 1 output -> dispatch Stage 1 (background).
3. **Stage 1 runs asynchronously.** Tell the user:
   "Stage 1 launched in background for {client}. Phase A (retrieval) and Phase B
   (analysis) will run autonomously. Run `/evaluate-session status {client}` to
   check progress, or `/evaluate-session process {client}` again when ready to continue."
4. If STAGE_1_DONE (all evaluations present) -> dispatch Stage 2 (background subagent).
5. When Stage 2 complete (`essentials-review.md` exists) -> enter HITL loop.
6. HITL loop -> on approval -> generate JSON -> push to Notion.

**Between each stage, re-read the filesystem.** Don't trust the subagent's report --
check that the files actually exist.

**The Full Pipeline does NOT block on Stage 1.** If Stage 1 is in progress (some but
not all evaluations exist), report progress and tell the user to check back. When
all evaluations are present, the pipeline continues to Stage 2.

## Route: Stage 1 Only

1. Read state (Step 0).
2. **Read all reference files, then dispatch call analyzer as a background subagent
   with reference content embedded:**

```
# Read references first (main agent has plugin file access)
org_mapping = Read("references/org-mapping.md")
endpoint_map = Read("references/endpoint-map.md")
simon_criteria = Read("references/simon-criteria.md")

Task(
  subagent_type: "general-purpose",
  description: "Stage 1: Analyze {client} coaching calls",
  run_in_background: true,
  prompt: "You are the Phase A orchestrator for the Project Evident call analyzer pipeline.

    ## Your Mission
    1. Retrieve all coaching call transcripts from Notion for this client
    2. Filter out cancellations and non-sessions
    3. Write raw transcripts and a manifest to disk
    4. Spawn one background Phase B subagent per transcript for parallel analysis

    ## Client Context
    Client: {Client Name}
    Client Page ID: {client_page_id}
    Essentials Page ID: {essentials_page_id}
    Folder: {ARTIFACT_ROOT}/{folder_name}/

    ## Instructions
    Follow the coaching-call-analyzer skill exactly:
    - Steps A0-A6: Retrieve, filter, write transcripts and manifest
    - Steps B0-B1: Read manifest, spawn one background Task subagent per call
      (run_in_background: true on each)
    - Step B2: Log the Phase B launch to pipeline.log and return

    IMPORTANT: When spawning Phase B agents, embed the endpoint-map and simon-criteria
    content in each agent's prompt. Background agents cannot read plugin files.

    Phase B agents run autonomously. Each writes its own evaluation file and
    pipeline.log entry. You do NOT wait for them to finish.

    Every file gets YAML frontmatter with client_page_id, essentials_page_id,
    transcript_page_id, and plugin_version: 1.1.0.
    If any ID can't be resolved, HALT.

    ## Reference: Org Mapping
    {org_mapping content}

    ## Reference: Endpoint Map
    {endpoint_map content}

    ## Reference: Simon Criteria
    {simon_criteria content}"
)
```

3. **Report to user immediately** (do not block):
   - "Stage 1 launched for {client} in background."
   - "Phase A (retrieval) will run first, then Phase B (analysis) agents will spawn automatically."
   - "Check progress: `/evaluate-session status {client}`"

4. **When status is checked later**, verify files exist:
   - `1-transcripts/manifest.json` must exist (Phase A done)
   - Read manifest to get expected call count
   - Count evaluation files in `2-evaluations/` (Phase B progress)
   - If evaluation count < manifest count: "Stage 1 in progress. {N} of {M} calls analyzed."
   - If evaluation count == manifest count: "Stage 1 complete. Ready for Stage 2."

**If some subagents failed but others succeeded**, report partial success and
offer to re-run only the failed calls.

## Route: Stage 2 Only

1. Read state (Step 0).
2. **Validate:** >=1 evaluation file exists in `2-evaluations/`. If not -> HALT:
   "No evaluation files found. Run Stage 1 first: `/analyze-call {client}`"
3. **If manifest exists**, check that evaluation count matches manifest count.
   If fewer evaluations than expected, warn Tim before proceeding.
4. **Read reference files, then dispatch essentials populator as a background subagent
   with reference content embedded:**

```
# Read references first (main agent has plugin file access)
endpoint_map = Read("references/endpoint-map.md")
simon_criteria = Read("references/simon-criteria.md")

Task(
  subagent_type: "general-purpose",
  description: "Stage 2: Populate essentials for {client}",
  run_in_background: true,
  prompt: "You are the Stage 2 essentials populator for Project Evident.
    Populate essentials for {Client Name}.
    Client page ID: {client_page_id}.
    Essentials page ID: {essentials_page_id}.
    Folder: {ARTIFACT_ROOT}/{folder_name}/

    Run the full workflow:
    - Glob 2-evaluations/call-*-evaluation.md to find all evaluation files
    - Validate essentials_page_id is present and consistent across all files
    - Map evaluation content to all 50 fields using the endpoint map below
    - Calculate values using $65/hr staff, $100/hr ED, $200/hr consultant rates
    - Write 3-essentials/essentials-review.md with YAML frontmatter
    - Run Essential Elements quality gate using the simon criteria below
    - Append SUCCESS or FAILED entry to pipeline.log

    ## Reference: Endpoint Map
    {endpoint_map content}

    ## Reference: Simon Criteria
    {simon_criteria content}

    Return: quality gate results, file path, any gaps."
)
```

5. **Report to user immediately** (do not block):
   - "Stage 2 launched for {client} in background."
   - "Check progress: `/evaluate-session status {client}`"

6. **When status is checked later**, verify `3-essentials/essentials-review.md` exists.
   If it exists, Stage 2 is done. Report results.

## Route: Push to Notion

1. Read state (Step 0).
2. **Validate:** `3-essentials/essentials-review.md` exists. If not -> HALT:
   "No essentials review file found. Run Stage 2 first: `/populate-essentials {client}`"
3. **Validate:** `essentials_page_id` is present in the review file's frontmatter.
   If not -> HALT: "essentials-review.md is missing the Essentials DB page ID. Cannot push."
4. Enter HITL loop (see below).

## HITL Loop

1. Append to pipeline.log:
   ```
   [{timestamp}] [v1.1.0] [stage-3:evaluator] [{client}]
     Status: WAITING_FOR_HITL
     Review file: 3-essentials/essentials-review.md
     Action needed: Tim reviews and approves or edits
   ```

2. Tell Tim:
   "Essentials review ready for {client}. File: `{path}/3-essentials/essentials-review.md`
   - Review the 50 fields in the tables
   - Edit any values directly in the file
   - Tell me 'looks good, push' or 'I edited it, re-read and push'"

3. Wait for Tim's instruction.

4. **If Tim says he edited it:**
   - Re-read `essentials-review.md` from disk (the actual file, not a cached version)
   - Show what changed vs. the original (diff the field values if possible)
   - Confirm: "Here's what changed: {changes}. Push these values?"

5. **On approval:** proceed to Generate JSON + Push.

## Generate JSON Payload

Read the approved `essentials-review.md` and generate:

**File:** `{ARTIFACT_ROOT}/{folder_name}/3-essentials/essentials-payload.json`

```json
{
  "client": "{Short Name}",
  "client_page_id": "{from frontmatter}",
  "essentials_page_id": "{from frontmatter}",
  "plugin_version": "1.1.0",
  "created_at": "{ISO 8601 timestamp}",
  "source_evaluations": [
    "2-evaluations/call-1-evaluation.md",
    "2-evaluations/call-2-evaluation.md"
  ],
  "properties": {
    "C1P1T1: Pain Point": "value from table...",
    "C1P1T2: Current Impact": "value from table...",
    ...all non-blank fields...
  }
}
```

**Conversion rules:**
- Text fields -> string values (exact text from the table)
- Checkbox -> `"__YES__"` or `"__NO__"`
- URL fields -> url string
- **Blank fields -> OMIT from properties object** (don't push empty strings to Notion)
- Property names must match endpoint-map.md exactly

**Validation before writing JSON:**
- `essentials_page_id` present -> if missing, HALT
- `client_page_id` present -> if missing, HALT
- All property names match endpoint-map.md -> if any don't, HALT with the mismatched names
- JSON is valid and parseable

## Push to Notion

1. Read `essentials-payload.json`.
2. Use `update-page-properties` (Notion Writer MCP):
   ```
   update-page-properties(
     page_id: "{essentials_page_id}",
     properties_json: '{...the properties object from the JSON...}'
   )
   ```
3. If push succeeds, append to pipeline.log:
   ```
   [{timestamp}] [v1.1.0] [stage-3:evaluator] [{client}]
     Status: PUSHED_TO_NOTION
     Target: essentials_page_id={essentials_page_id}
     Fields pushed: {count} of 50
     Payload: 3-essentials/essentials-payload.json
   ```

4. If push fails, append:
   ```
   [{timestamp}] [v1.1.0] [stage-3:evaluator] [{client}]
     Status: FAILED
     Error: {error from Notion API}
     Payload was: 3-essentials/essentials-payload.json
     Notes: JSON file preserved for retry
   ```

5. Report to Tim:
   - Fields pushed (count and which ones)
   - Notion page URL for verification
   - Any fields that were blank (not pushed)
   - Quality gate results

## Route: Status Check

1. Read state (Step 0).
2. Report:
   ```
   # {Client Name} -- Pipeline Status

   State: {current state}
   Last activity: {most recent log entry timestamp}

   Stage 1 Phase A (Retrieve): {# calls found, # filtered, or "not run" or "in progress"}
   Stage 1 Phase B (Analyze): {# calls analyzed / # expected, or "not run" or "in progress ({N}/{M})"}
   Stage 2 (Populate): {done/not run, quality gate if done}
   Stage 3 (Push): {pushed/waiting/not run}

   Files:
     Manifest: {exists/missing}
     Transcripts: {count or "none"}
     Evaluations: {count or "none"} {of {expected} if manifest exists}
     Essentials review: {exists/missing}
     JSON payload: {exists/missing}

   Next step: {what to do}
   ```

3. **For in-progress states:**
   - If PHASE_A_DONE with AGENTS_LAUNCHED: "Phase B analysis agents are running in background. {N} of {M} calls analyzed so far."
   - If STAGE_1_IN_PROGRESS: "Background agents still working. {N} of {M} evaluations complete. Check back shortly."
   - If all evaluations present but no COMPLETE entry: Write the COMPLETE entry and report "Stage 1 just finished. Ready for Stage 2."

4. If there are FAILED entries, show the most recent error and suggest fix.

## Route: Batch Mode

Process all clients in order:
```
1. ALAS -> 2. Building Promise -> 3. CPA -> 4. CHDC -> 5. E4 Youth ->
6. EDC -> 7. LAA -> 8. SV@Home -> 9. Sumter -> 10. TAP -> 11. TIP
```

For each client:
1. Read state
2. Run whatever stage is next (don't re-run completed stages)
3. Present results before moving to the next
4. Don't wait for approval between clients unless something needs a decision

At the end, produce a portfolio summary:
```
# Portfolio Status

| Client | Pages | Filtered | Analyzed | Stage 2 | Stage 3 | Quality Gate | Flags |
|--------|-------|----------|----------|---------|---------|--------------|-------|
| ALAS   | 13    | 7        | 6 / 6   |         | Pushed  | 7/7          |       |
| ...    |       |          |          |         |         |              |       |
```

## Evidence Standards

**Strong indicators:** client made decisions, action items assigned with owners,
client explains concepts in own words, team alignment, specific tools selected

**Moderate indicators:** options narrowed, general agreement, plans to test

**Weak indicators:** still exploring broadly, conceptual discussions, missing
decision-makers, vague commitments

**Red flags:** repeated discussions without progress, confusion on basics,
scope creep from efficiency goals

## What This Skill Produces

- Pipeline state validation (reads log + filesystem + manifest)
- Dispatches Stage 1 (background) and Stage 2 (background) with validation between stages
- HITL review cycle management
- `3-essentials/essentials-payload.json` -- the exact Notion push payload
- Notion Essentials DB updates via `update-page-properties`
- Pipeline log entries for all actions

## What This Skill Does NOT Do

- Analyze transcripts directly (dispatches Stage 1)
- Map content to 50 fields (dispatches Stage 2)
- Modify Google Doc Implementation Plans (provides language only)
- Update component statuses on the Client Page (coach does this)
- Push without Tim's explicit approval
