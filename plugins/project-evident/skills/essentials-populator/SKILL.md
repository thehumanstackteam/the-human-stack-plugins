---
name: essentials-populator
description: >
  Stage 2 of the Project Evident pipeline. Reads evaluation files from the client's
  Working Files folder, maps content to 50 Essentials fields using the endpoint map,
  validates against Simon's 7 Essential Elements, and writes essentials-review.md for
  Use for "populate essentials", "fill endpoints", "run stage 2 for [client]".
---

# Essentials Populator (Stage 2)

Reads evaluation files from `2-evaluations/` → maps content to 50 Notion fields using
endpoint-map.md → validates against Simon's 7 Essential Elements → writes
`3-essentials/essentials-review.md` for Tim's review → appends to pipeline.log.

**Plugin version: 1.1.0**

## Prerequisites

- Notion MCP connector (for supplementary transcript pulls only -- NOT the primary source).
- Reference files needed (endpoint-map.md, simon-criteria.md, org-mapping.md).

**When running as a background subagent:** The caller embeds reference file content
directly in the prompt. Do NOT try to read from `${CLAUDE_PLUGIN_ROOT}` -- background
agents do not have access to plugin files. Use the reference content provided in the prompt.

**When running in the main agent:** Load these reference files directly:
  - `references/org-mapping.md` -- client page IDs, essentials page IDs, folder names
  - `references/endpoint-map.md` -- exact Notion property names and types (all 50 fields)
  - `references/simon-criteria.md` -- the 7 Essential Elements quality gate

## Constants

```
ARTIFACT_ROOT = ~/Dev/claude-cowork/Clients/Project Evident Updates
PLUGIN_VERSION = 1.1.0
```

## Step 0: Resolve Client and Validate

1. Match the client name/shortname to org-mapping.md.
2. Extract `client_page_id`, `essentials_page_id`, and `folder_name`.
3. **HALT if either ID is missing.**

4. Set working directory: `{ARTIFACT_ROOT}/{folder_name}/`

## Step 1: Load Evaluation Files

1. Glob `{working_dir}/2-evaluations/call-*-evaluation.md` to find all evaluation files.

2. **If zero files found → HALT.** Report:
   "No evaluation files found in `{working_dir}/2-evaluations/`. Run Stage 1 first:
   `/analyze-call {client}`"

3. For each evaluation file, read YAML frontmatter and extract:
   - `client_page_id`
   - `essentials_page_id`
   - `transcript_page_id`
   - `session` number
   - `date`

4. **Validate ID consistency:**
   - All files must have the same `client_page_id` — if not, HALT with mismatch error
   - All files must have the same `essentials_page_id` — if not, HALT with mismatch error
   - `essentials_page_id` MUST match what's in org-mapping.md — if not, HALT
   - Every file must have a non-empty `transcript_page_id` — warn if missing but don't halt

5. Read the full body of each evaluation file. The evaluations contain:
   - Attribution logs (who said what, weight, component mapping)
   - Full cluster text for short clusters, rich summaries for long ones
   - Component-level evaluation with Essential Elements scorecard

## Step 2: Map Content to 50 Fields

Use the evaluation content to populate each field per endpoint-map.md. The mapping
is mostly mechanical — the analytical work was done in Stage 1.

**Framing:**
> "This was an emergent process — the client found tools first, then discovered
> what problems the tools solved. Highlight the ways this client succeeded with AI."

**Right-sizing context:** These are small nonprofits (5-30 staff, budgets under
$5M) using accessible, user-appropriate tools effectively. The implementation
components (C3) must be evaluated at the right scale:

- **"AI Tools Purchase"** = have the right tools and are using them. The word
  "purchase" is misleading -- this is really "do they have appropriate AI tools?"
  Signed up for free ChatGPT, using Google Gemini, adopted the Promptinator --
  all count. Nothing needs to be bought. If they have tools and use them: ✅.
- **"Data Identified"** = figured out which spreadsheet, database export, or
  existing system holds the data they need. Not a data warehouse.
- **"Technology Integration"** = got the tool working with their actual workflow.
  Could mean learning to paste data into a prompt, connecting a Zapier, or
  exporting from Salesforce to upload to Gemini. Not API integrations.
- **"Small Scale Test"** = one person tried it on one real task and it worked
  (or didn't). A Deputy Director drafting one newsletter with AI is a test.
- **"Wider Rollout"** = other staff started using it too, or it became the
  normal way the task gets done. Three people using Promptinator independently
  IS a rollout at this scale.

Do not undersell small-org adoption by comparing it to enterprise standards.
A 6-person org where 3 people independently use AI for their work has achieved
50% adoption -- that's remarkable. Write it that way.

**Tool-constraint fit:** When the client chose a tool because it matches their
operational reality, call that out. The implementation insight isn't the tool
itself -- it's why that tool works for how they actually operate. A phone
camera capturing handwritten forms at field events is a better story than
"they used Gemini." The phone was already in their pocket, volunteers don't
need training on cameras, and it solves the constraint (no laptops at event
tables). When the client realizes what they already have in their pocket can
do something they thought required expensive systems -- that's an aha moment.
Capture that realization in the narrative. That's implementation thinking
worth highlighting in Description, Evidence, and Aha Moments fields.

### How to Write Each Field Type

**Checkbox fields** (e.g., C3P1T1F1: AI Tools Purchase Checked):
Use ✅ if the attribution log shows the client took action -- signed up, started
using, configured, tested, adopted. Use 🚫 if not. Don't check based on
discussion alone. "We've been using ChatGPT" = ✅. "We talked about maybe
trying ChatGPT" = 🚫.

**Owner fields** (e.g., C3P1T1F3: Owner for AI Tools Purchase):
Named person from the attribution log. "Maria Rodriguez, Intake Coordinator" —
not "staff" or "the team."

**Description fields** (e.g., C4P2T2F2: Description of Productivity Gains):
The narrative of what changed. Synthesizes across sessions. Reads well in a
funder-facing document. This is what goes in the Google Doc.

Write it so a reader who knows nothing about the coaching sessions understands
what happened and why it matters.

Example:
> "Staff save approximately 2 hours per newsletter using AI-assisted drafting
> through Promptinator, freeing capacity for direct client programming. The tool
> handles first-draft generation from bullet points, reducing the writing cycle
> from 3 hours to under 1 hour per piece."

Not:
> "Productivity gains were observed in newsletter production."

**Evidence fields** (e.g., C4P2T2F3: Evidence of Productivity Gains):
The specific, verifiable facts that back the Description. Who did what, what the
numbers are, what was directly observed. Written clearly — no internal tags, no
session numbers, no classification labels.

Evidence answers: "How do we know the Description is true?"

Example:
> "Sanders calculated 2 hours saved per newsletter at $65/hr staff rate ($130/article).
> Staff began using Promptinator independently between coaching sessions without
> additional training. Three newsletters produced using AI-assisted workflow in
> January with no quality complaints from readers."

Not:
> "Measured (Session 2): Sanders and Tim calculated 2 hrs/article. Observed
> (Session 3): Staff adopted tool."

**The rule:** Description and Evidence must never say the same thing. If they do,
one of them is wrong. Description = what happened. Evidence = the specific
observations, measurements, and actions that prove it happened.

**Progress Indicator fields** (e.g., C3P1T1F4: Progress Indicators for AI Tools Purchase):
Concrete metrics of what happened. Hours saved, tasks automated, adoption rate.
Same standard as Evidence — specific and verifiable.

**Before/After fields** (C4P1F1, C4P1F2):
Describe the actual workflow steps, not feelings. "Before" should read like a
process document for the old way. "After" should read like a process document
for the new way.

**Narrative fields** (Coaching Notes, Aha Moments):
Coaching Notes = summary of the coaching arc. What the client figured out, how
they got there, what the coach contributed.
Aha Moments = the specific moments when something clicked. Named person, what
they realized, why it mattered.

### Value Calculations

When the attribution log contains time/cost data, calculate:
1. Find the unit (hours per task)
2. Find frequency (weekly, monthly)
3. Annualize (units × frequency × 52 or 12)
4. Apply rate: Staff $65/hr, ED $100/hr, Consultant $200/hr
5. State in Description: "saving approximately $6,760/year in staff time"
6. State in Evidence: "Sanders calculated 2 hrs/newsletter × 52 weeks × $65/hr"

Only calculate meaningful savings. Paper reduction is values alignment, not financial.

### Low/Med/High Value Proxy

When value data is projected but not confirmed by direct measurement, DO NOT use
a single point estimate. Build a three-scenario range table:

| Scenario | Assumptions | Calculation | Annual Value |
|----------|------------|-------------|-------------|
| **Low** | Conservative scope, minimum hours | {show work} | ${amount} |
| **Med** | Most likely based on transcript evidence | {show work} | ${amount} |
| **High** | Full scope + effects client may not have named | {show work} | ${amount} |

Rules:
- Each scenario must show its full calculation chain (units x frequency x rate)
- "Low" must be defensible from transcript alone -- no assumptions
- "Med" is the best interpretation of what the client described
- "High" accounts for hidden time (tasks the person doesn't recognize as related)
- The summary table uses Confirmed/Projected confidence labels per category
- Tim picks the right scenario during review (veto via Notion comments)

This proxy allows the Quantitative Impact essential element to pass the quality
gate when approximate but not precise values exist. It was validated in the ALAS
run -- the quality gate went from 6/7 (blocked) to actionable with L/M/H ranges
that Tim could refine.

Include the range table in essentials-review.md after the 50 fields, before the
quality gate section.

**When to use the proxy -- ALL conditions must be met:**
1. The evaluation files contain a specific value signal FROM THE CLIENT:
   a named number, time estimate, cost, frequency, or before/after comparison
2. The signal was stated with enough specificity to anchor the Low scenario
   using ONLY what was directly stated -- no assumptions added
3. Med and High extend scope or account for hidden time, but Low is transcript-only

**When NOT to use the proxy -- leave the value blank or mark qualitative:**
- Generic statements ("saves time", "been helpful") with no numbers -> qualitative
- Coach-stated values the client never confirmed or repeated -> not client evidence
- "Reasonable" assumptions about how long a task should take -> fabrication
- Analogies from other clients ("ALAS saved X so...") -> never cross-pollinate
- No value signals exist in the attribution logs at all -> blank field

The proxy structures EXISTING approximate data into actionable ranges.
It does not generate plausible numbers where none exist.

### Formatting: Line Breaks in Lists

When a field value contains multiple items (numbered or bulleted), each item
MUST be on its own line with a blank line between items. This applies to
essentials-review.md AND essentials-payload.json (where `\n` becomes actual
line breaks in Notion rich_text).

Good:
```
(1) Dr. H's culturally-informed AI adoption strategy: "I need to create
jealousy..." -- organic demand-generation over forced adoption.

(2) Marisela's insight on prompting: "You just essentially direct it on how
to think" -- Tim called this "the best explanation of prompting I've ever heard."

(3) Dr. H on Promptinator: "This right here just cut a solid hour or two."
```

Bad:
```
(1) Dr. H's culturally-informed AI adoption strategy... (2) Marisela's insight on prompting... (3) Dr. H on Promptinator...
```

The bad version is unreadable in both the review file and Notion. Every numbered
or bulleted item gets its own line. No exceptions.

### Framing: Staff Transitions and Organizational Change

This is a funder-facing document. Write about staffing changes the way a
funder report would: as organizational resilience, knowledge transfer, and
continuity planning.

- Staff departures = "staffing transition" or "role transition", not "loss"
- Reduced capacity = "lean team" or "streamlined operations", not "survival mode"
- Paused programs = "on hold pending [specific milestone]", not "inability to deliver"
- Someone leaving = what they built, what they handed off, what's ready for the next person
- Focus on what the organization DID with the situation, not the disruption itself

Good: "Theo developed the phone photo workflow and prepared a program packet
to support onboarding a successor. The organization plans to deploy the
AI-assisted data collection process when the new program manager is in place
for the spring 2026 HIRE event."

Bad: "The organization is in survival mode with only two staff after Theo's
transition to contractor status. The HIRE program is paused due to inability
to deliver with current staffing."

Both describe the same facts. The first reads like a funder report. The second
reads like an incident report.

### What Never Goes in Any Field

- Internal classification tags (Measured, Stated, Observed, etc.)
- Session numbers or dates
- Attribution log codes
- Coach frameworks attributed to the client
- Polite acknowledgments treated as adoption
- Marketing copy where observations should be
- Anything that sounds plausible but wasn't in the transcript
- Crisis language about staffing changes (survival mode, inability, loss)
- Editorializing about motivations ("created to satisfy a grant requirement",
  "only did this because...", "reluctantly adopted")
- Explaining why something WASN'T done -- if it's not done, leave blank or
  state plainly: "No formal AI use policy has been completed." Full stop.

## Step 3: Supplementary Transcript Pull (If Needed)

If the evaluations have significant gaps in any component area, fetch transcripts
directly from Notion for targeted extraction. Never load more than 2-3 transcripts.

Any new transcripts fetched get saved to `1-transcripts/` with proper frontmatter
(same format as Stage 1).

## Step 4: Write essentials-review.md

**File:** `{ARTIFACT_ROOT}/{folder_name}/3-essentials/essentials-review.md`

```markdown
---
client: {Short Name}
client_page_id: {from org-mapping / validated from evaluations}
essentials_page_id: {from org-mapping / validated from evaluations}
source_evaluations:
  - 2-evaluations/call-1-evaluation.md
  - 2-evaluations/call-2-evaluation.md
plugin_version: 1.0.0
created_at: {ISO 8601 timestamp}
---

# Essentials Review: {Org Full Name}

**Status:** Ready for Tim's review. Edit any values below, then tell the evaluator to push.

## Component 1: Pain Point & AI Solution

| Field | Value |
|-------|-------|
| C1P1T1: Pain Point | {value or blank} |
| C1P1T2: Current Impact | {value or blank} |
| C1P2: Reviewed AI Solutions and Tools | {value or blank} |

## Component 2: Policy/Guidelines

**C2 is ONLY about AI governance/responsible use policy** -- acceptable use
guidelines, data privacy rules, responsible AI principles. It is NOT about the
AI Implementation Plan Essentials document (the coaching deliverable/template).

**C2T1F1 (Policy Document Link):** Include a link if one exists in the client's
properties. But a link alone does not mean C2 is complete.

**C2T1F2 (Policy Notes):** Content about the Essentials document, implementation
plan, or coaching template does NOT belong in this field. This field is exclusively
for AI governance/usage policy work. If no governance policy work was done,
leave it blank.

**C2 checkbox logic:** The policy link existing is not enough. C2T1F1 gets a link
if one exists. C2T1F2 reflects whether the linked document contains substantive,
adopted governance policy -- not whether a link was pasted. An empty template,
abandoned draft, or "pretty discursory" draft = not completed.

| Field | Value |
|-------|-------|
| C2T1F1: Policy Document Link | {url or blank} |
| C2T1F2: Policy Notes | {value or blank} |

## Component 3: Execution — Phase 1: Foundation & Setup

| Field | Value |
|-------|-------|
| C3P1T1F1: AI Tools Purchase Checked | ✅ or 🚫 |
| C3P1T1F2: Description of AI Tools Purchase | {value} |
| C3P1T1F3: Owner for AI Tools Purchase | {value} |
| C3P1T1F4: Progress Indicators for AI Tools Purchase | {value} |
| C3P1T2F1: Data Identified Checked | ✅ or 🚫 |
| C3P1T2F2: Description of Data Identified and Readiness | {value} |
| C3P1T2F3: Owner for Data Identification | {value} |
| C3P1T2F4: Progress Indicators for Data Readiness | {value} |
| C3P1T3F1: Technology Integration Complete Checked | ✅ or 🚫 |
| C3P1T3F2: Description of Technology Integration | {value} |
| C3P1T3F3: Owner for Technology Integration | {value} |
| C3P1T3F4: Progress Indicators for Technology Integration | {value} |

## Component 3: Execution — Phase 2: Testing & Training

| Field | Value |
|-------|-------|
| C3P2T1F1: Small Scale Test Run Checked | ✅ or 🚫 |
| C3P2T1F2: Description of Small Scale Test | {value} |
| C3P2T1F3: Owner for Small Scale Test | {value} |
| C3P2T1F4: Progress Indicators for Small Scale Test | {value} |

## Component 3: Execution — Phase 3: Launch & Rollout

| Field | Value |
|-------|-------|
| C3P3T1F1: Wider Rollout Checked | ✅ or 🚫 |
| C3P3T1F2: Description of Wider Rollout | {value} |
| C3P3T1F3: Owner for Wider Rollout | {value} |
| C3P3T1F4: Progress Indicators for Wider Rollout | {value} |

## Component 4: Progress Monitoring — Before/After

| Field | Value |
|-------|-------|
| C4P1F1: Before AI | {value} |
| C4P1F2: After AI | {value} |

## Component 4: Progress Monitoring — Cost Savings

| Field | Value |
|-------|-------|
| C4P2T1F1: Cost Savings Checked | ✅ or 🚫 |
| C4P2T1F2: Description of Cost Savings | {value} |
| C4P2T1F3: Evidence of Cost Savings | {value} |

## Component 4: Progress Monitoring — Productivity Gains

| Field | Value |
|-------|-------|
| C4P2T2F1: Productivity Gains Checked | ✅ or 🚫 |
| C4P2T2F2: Description of Productivity Gains | {value} |
| C4P2T2F3: Evidence of Productivity Gains | {value} |

## Component 4: Progress Monitoring — Policy Changes

| Field | Value |
|-------|-------|
| C4P2T3F1: Policy Changes Checked | ✅ or 🚫 |
| C4P2T3F2: Description of Policy Changes | {value} |
| C4P2T3F3: Evidence of Policy Changes | {value} |

## Component 4: Progress Monitoring — Service Delivery

| Field | Value |
|-------|-------|
| C4P2T4F1: Service Delivery Improvements Checked | ✅ or 🚫 |
| C4P2T4F2: Description of Service Delivery Improvements | {value} |
| C4P2T4F3: Evidence of Service Delivery Improvements | {value} |

## Component 4: Progress Monitoring — Outcomes

| Field | Value |
|-------|-------|
| C4P2T5F1: Outcomes Improved Checked | ✅ or 🚫 |
| C4P2T5F2: Description of Outcomes Improved | {value} |
| C4P2T5F3: Evidence of Outcomes Improved | {value} |

## Component 4: Progress Monitoring — Funding

| Field | Value |
|-------|-------|
| C4P2T6F1: Increased Funding Checked | ✅ or 🚫 |
| C4P2T6F2: Description of Increased Funding | {value} |
| C4P2T6F3: Evidence of Increased Funding | {value} |

## Component 4: Progress Monitoring — Other Changes

| Field | Value |
|-------|-------|
| C4P2T7F1: Other Changes Checked | ✅ or 🚫 |
| C4P2T7F2: Description of Other Changes | {value} |
| C4P2T7F3: Evidence of Other Changes | {value} |

## Narrative

| Field | Value |
|-------|-------|
| Coaching Notes | {value} |
| Aha Moments | {value} |

---

## Essential Elements Quality Gate

Element              | Verdict     | What's in the fields
AI Tech              | {✓/⚠/✗}   | {content or gap}
Personnel            | {✓/⚠/✗}   | {content or gap}
Data                 | {✓/⚠/✗}   | {content or gap}
Pre-AI Workflow      | {✓/⚠/✗}   | {content or gap}
Post-AI Workflow     | {✓/⚠/✗}   | {content or gap}
Quantitative Impact  | {✓/⚠/✗}   | {content or gap}
Qualitative Impact   | {✓/⚠/✗}   | {content or gap}

**Result:** {#}/7 passing | {Ready / Needs work}

{If all 7 pass, generate summary sentence per simon-criteria.md template}

{If gaps exist: which field needs it, which transcript likely has it}
```

**All 50 fields must appear.** Blank fields shown as blank, not omitted.
Checkbox fields show ✅ or 🚫.

**The file must be human-editable.** Tim opens this in a text editor, changes values,
saves, then tells the evaluator to push. No special formatting beyond markdown tables.

## Step 5: Append to Pipeline Log

Append to `{ARTIFACT_ROOT}/{folder_name}/pipeline.log`:

```
[{ISO 8601 timestamp}] [v1.0.0] [stage-2:essentials-populator] [{Short Name}]
  Status: SUCCESS
  Input: 2-evaluations/call-1-evaluation.md, call-2-evaluation.md
  Output: 3-essentials/essentials-review.md
  Quality gate: {#}/7 pass, {#} vague ({which elements}), {#} missing ({which elements})
```

Or on failure:
```
[{ISO 8601 timestamp}] [v1.0.0] [stage-2:essentials-populator] [{Short Name}]
  Status: FAILED
  Error: {what went wrong}
```

## Step 6: Report to User

Present:
- Which evaluation files were consumed
- Quality gate results (7 elements)
- Summary sentence if all 7 pass
- Gaps and which transcript to target
- File path: "Review file ready at `{path}/3-essentials/essentials-review.md`"
- Next step: "Edit the file if needed, then tell the evaluator to push to Notion."

## What This Skill Produces

- `3-essentials/essentials-review.md` — human-readable, editable review document with
  all 50 fields, quality gate, and YAML frontmatter with Notion IDs
- Appended entry in `pipeline.log`

## What This Skill Does NOT Do

- Write to Notion (that's Stage 3: evaluator, after Tim approves)
- Analyze raw transcripts from scratch (use Stage 1: call-analyzer)
- Update component statuses on the Client Page
- Generate the Google Doc (use the Essentials DB button)
- Generate essentials-payload.json (that's Stage 3)
