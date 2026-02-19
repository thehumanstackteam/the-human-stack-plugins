---
name: simon-summary
description: >
  Stage 4 of the Project Evident pipeline. Reads the essentials-review.md output
  for a coaching client and generates a single summary paragraph covering all 7
  of Simon's Essential Elements. The paragraph is written to the "Simon Summary"
  property on the client's page in the Clients database.
  Use for "write simon summary", "generate summary for [client]", "run stage 4",
  "simon summary for [client]".
---

# Simon Summary (Stage 4)

Read the essentials-review.md for a client -> synthesize all 7 Essential Elements
into a single summary paragraph -> write to the "Simon Summary" rich_text property
on the client's page in the Clients database.

**Plugin version: 1.1.0**

## Prerequisites

- Completed Stage 2 output: `3-essentials/essentials-review.md` must exist
- The essentials quality gate must show 7/7 passing (or Tim must have approved
  despite gaps during HITL review)
- Notion MCP connector for writing the summary to the Client page

Load these reference files:
  - `references/org-mapping.md` -- client page IDs and folder names
  - `references/simon-criteria.md` -- the 7 Essential Elements and summary template

**When running as a background subagent:** The caller embeds reference file content
directly in the prompt. Do NOT read from `${CLAUDE_PLUGIN_ROOT}`.

## Constants

```
ARTIFACT_ROOT = ~/Dev/claude-cowork/Clients/Project Evident Updates
PLUGIN_VERSION = 1.1.0
TARGET_PROPERTY = "Simon Summary"
TARGET_PAGE = Clients DB Page ID (from org-mapping.md)
```

## Step 0: Resolve Client and Validate

1. Match the client name/shortname to org-mapping.md.
2. Extract `client_page_id` and `folder_name`.
3. **HALT if `client_page_id` is missing.**
4. Verify `3-essentials/essentials-review.md` exists. If not -> HALT with
   "Run Stage 2 first: `/populate-essentials {client}`"

## Step 1: Read Essentials Review

Read `{ARTIFACT_ROOT}/{folder_name}/3-essentials/essentials-review.md`.

Extract the content for all 7 Essential Elements from the populated fields:

| Element | Primary Source Fields |
|---------|---------------------|
| AI Tech Used | C1P2, C3P1T1F2 |
| Personnel Involved | All Owner fields (C3P1T1F3, C3P1T2F3, C3P1T3F3, C3P2T1F3, C3P3T1F3) |
| Data Involved | C3P1T2F2 |
| Pre-AI Workflow | C4P1F1, C1P1T1, C1P1T2 |
| Post-AI Workflow | C4P1F2, C3P2T1F2, C3P3T1F2 |
| Quantitative Impact | C4P2T1F3, C4P2T2F3, value calculation tables |
| Qualitative Impact | C4P2T4F2, C4P2T5F2, Coaching Notes, Aha Moments |

Also read the Essential Elements Quality Gate section to confirm status.

## Step 2: Validate Readiness

Check the quality gate results in essentials-review.md.

- If 7/7 specific -> proceed
- If < 7/7 but the file has a note like "Approved by Tim" or the HITL gate
  has been passed -> proceed
- If < 7/7 and no approval -> HALT with: "Quality gate shows {N}/7. Complete
  HITL review before generating summary."

## Step 3: Write the Summary Paragraph

Generate a single paragraph following this template structure:

> The organization is using **[AI Tech]** with **[Personnel]** for
> **[Data/Process]** to solve **[Pre-AI Workflow problem]**, achieving
> **[Post-AI Workflow improvement]**, **[Quantitative Impact]**,
> and **[Qualitative Impact]**.

### Writing Rules

1. **One paragraph.** Not bullet points, not a list, not multiple paragraphs.
   A single flowing sentence (may be compound/complex) that a funder reads
   in 30 seconds and understands what happened.

2. **All 7 elements must appear.** The paragraph is the proof that the
   Essentials document is complete. If an element can't be included with
   specificity, the document isn't ready.

3. **Specific, not generic.** Every element slot must contain the actual
   content from the essentials review:
   - Tool names, not "AI tools"
   - Person names with roles, not "staff"
   - Actual workflow steps, not "improved processes"
   - Real numbers, not "significant savings"
   - Named outcomes, not "better results"

4. **The template is a guide, not a straitjacket.** The paragraph should
   read naturally. Rearrange clauses to fit the client's story. The ALAS
   summary won't read like the EDC summary because their stories are different.

5. **Use the LMH proxy ranges when present.** If the essentials review has
   Low/Med/High value tables, use the Med scenario values in the summary
   (Tim will have adjusted these during HITL). State as approximations:
   "reducing processing time from approximately 4 hours to 30 minutes."

6. **No internal jargon.** No "Stage 2", no "C4P2T2F3", no "attribution log",
   no "quality gate". This is funder-facing text.

### Example (from a reference org, not a Project Evident client)

> The organization is using JotForm with AI automation capabilities (powered
> by AI-enhanced features including video upload capability and integrated text
> message notifications) with staff for intake process automation to solve
> time-consuming manual 10-step intake workflow that required staff to work
> alone on intake, phone call coordination, and therapist matching, achieving
> dramatic reduction from 10-step manual workflow to 3-step automated system,
> reduced intake processing time from 4 hours per week (for 10-20 people) to
> 30 minutes, increased productivity allowing staff capacity reallocation to
> other organizational areas, improved client matching allowing clients to
> choose clinicians, ability to reach more people, greater client satisfaction
> by receiving services sooner, and saving staff time and money.

### What Makes This Example Work

- **AI Tech**: "JotForm with AI automation capabilities (powered by AI-enhanced
  features including video upload capability and integrated text message
  notifications)" -- named tool with specific capabilities
- **Personnel**: "staff" is acceptable here because the org is small; for larger
  orgs, name the key people
- **Data/Process**: "intake process automation" -- specific process named
- **Pre-AI Workflow**: "time-consuming manual 10-step intake workflow that required
  staff to work alone on intake, phone call coordination, and therapist matching"
  -- steps and pain described
- **Post-AI Workflow**: "3-step automated system" -- concrete comparison
- **Quantitative Impact**: "4 hours per week to 30 minutes" and "10-20 people" --
  real numbers
- **Qualitative Impact**: "clients choose clinicians, ability to reach more people,
  greater client satisfaction by receiving services sooner" -- named outcomes

## Step 4: Write Summary to File

Save the summary paragraph to:
`{ARTIFACT_ROOT}/{folder_name}/4-summary/simon-summary.md`

```markdown
---
client: {Short Name}
client_page_id: {from org-mapping}
plugin_version: 1.1.0
created_at: {ISO 8601 timestamp}
source: 3-essentials/essentials-review.md
---

# Simon Summary: {Org Full Name}

{The summary paragraph}
```

## Step 5: Push to Notion (with confirmation)

**This step writes to the Client page in Notion.** Confirm with Tim before pushing.

1. Present the summary paragraph to Tim for approval.
2. On approval, update the "Simon Summary" property on the Client page
   (`client_page_id` from org-mapping.md) using Notion MCP.
3. The property is rich_text -- push as a single text block.

If the summary exceeds 2000 characters (Notion rich_text limit), split into
multiple rich_text array elements at sentence boundaries.

## Step 6: Append to Pipeline Log

```
[{ISO 8601 timestamp}] [v1.1.0] [stage-4:simon-summary] [{Short Name}]
  Status: SUCCESS
  Output: 4-summary/simon-summary.md
  Target: Client page {client_page_id} -> "Simon Summary" property
  Elements: 7/7 included
  Length: {char count}
```

## Step 7: Report to User

Present:
- The summary paragraph (so Tim can read it inline)
- Quality gate confirmation (7/7 elements present)
- File path: `{path}/4-summary/simon-summary.md`
- Whether it was pushed to Notion or awaiting approval
- Next client in the pipeline (if running batch)

## What This Skill Produces

- `4-summary/simon-summary.md` -- the summary paragraph with frontmatter
- "Simon Summary" property updated on the Client page in Notion
- Appended entry in `pipeline.log`

## What This Skill Does NOT Do

- Analyze transcripts (Stage 1)
- Populate the 50 fields (Stage 2)
- Push essentials to the Essentials page (Stage 3)
- Generate the Google Doc
- Update component statuses
