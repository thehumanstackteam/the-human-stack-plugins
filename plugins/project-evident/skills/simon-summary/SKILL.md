---
name: simon-summary
description: >
  Stage 4 of the Project Evident pipeline. Reads the essentials-review.md output
  for a coaching client and generates a funder-ready summary sentence covering
  Simon's 6 characteristics. Written to the "Simon Summary" property on the
  client's page in the Clients database. The sentence must read like a case study
  lead that Simon can drop into a funder report without editing.
  Use for "write simon summary", "generate summary for [client]", "run stage 4",
  "simon summary for [client]".
---

# Simon Summary (Stage 4)

Read the essentials-review.md for a client -> write a funder-ready summary
sentence -> push to the "Simon Summary" rich_text property on the client's
page in the Clients database.

**Plugin version: 1.2.0**

## The Meta-Task

Give Simon a sentence he can drop directly into a funder report without editing it.

Not "fill a template." Not "check boxes." Write prose that a program officer reads
and thinks "this is real." If it reads like a form, it's wrong. If it reads like
a case study opening, it's right.

Simon needs to prove to funders that the coaching program produces concrete,
reportable results. Each summary sentence is a line item that justifies the next
round of funding. The 6 characteristics are his specificity test: if the sentence
can't name the tech, the people, the data, the before, the after, and the impact,
then the engagement didn't produce something defensible enough to report.

## Simon's 6 Characteristics

| # | Characteristic | What It Proves |
|---|---------------|---------------|
| 1 | AI Tech used | Specific tools, not vague "AI" |
| 2 | Personnel involved (the users) | Named roles, not "staff" |
| 3 | Data involved | What data feeds the workflow |
| 4 | Pre-AI workflow (steps and key activities) | What it was like before -- countable steps |
| 5 | Post-AI workflow (steps and key activities) | What it's like now -- countable steps |
| 6 | Impact (quantitative AND qualitative) | Numbers + mission outcomes |

## Simon's Number Pattern

Simon builds summaries around concrete before-and-after contrasts with specific
numbers. The numbers themselves become the narrative of change.

The formula: [before steps] -> [after steps], [before time] -> [after time],
for [N people/things], enabling [what they can now do].

No dollar amounts. The numbers prove the transformation happened at scale, and
the qualitative pieces show what it means for the mission.

Example: "10-step manual workflow to 3-step automated system, 4 hours per week
to 30 minutes for 10-20 people" -- step count reduction + time reduction + volume.

## Prerequisites

- Completed essentials-review.md (Stage 2 output)
- Quality gate passed (or pipeline proceeded with flagged gaps)
- Notion MCP connector for writing to Client page

Load reference files:
  - `references/org-mapping.md` -- client page IDs and folder names
  - `references/simon-criteria.md` -- the 7 Essential Elements

## The 7-Step Process

This is the actual methodology for writing the sentence. Follow in order.

### Step 1: Gather the 6 Raw Ingredients

Read essentials-review.md and extract content for each characteristic:

| Characteristic | Primary Source Fields |
|---------------|---------------------|
| AI Tech | C1P2, C3P1T1F2 |
| Personnel | All Owner fields (C3P1T1F3, C3P1T2F3, C3P1T3F3, C3P2T1F3, C3P3T1F3) |
| Data | C3P1T2F2 |
| Pre-AI Workflow | C4P1F1, C1P1T1, C1P1T2 |
| Post-AI Workflow | C4P1F2, C3P2T1F2, C3P3T1F2 |
| Impact | C4P2 fields (all), value calculation tables, Coaching Notes |

### Step 2: Read Through the Funder Lens

Ask "what can Simon report" -- NOT "how far along is the client."

- Adoption that spread to other staff is reportable
- An unfinished exploration is still reportable as "exploring"
- Nothing needs to be complete to be funder-ready
- Don't undersell. Don't assume the client's story is weaker than it is

### Step 3: Count the Actual Steps

Go back to the evaluation files if needed. Count the before-workflow steps.
Count the after-workflow steps. Someone counted "10-step manual intake" for the
JotForm example -- that wasn't magic, someone enumerated the workflow.

If the essentials-review says "manual process" without step counts, dig into
the evaluations. The steps are there.

### Step 4: Extract the Reportable Specifics

Pull out:
- Named tools (not "AI tools")
- Titles and roles (not names -- "Deputy Director of Operations" not "Sarah")
- Volume numbers (newsletters, articles, cities, clients served)
- Time recovered (annualized from the L/M/H proxy Med scenario)
- Qualitative shift (in plain language -- what changed about how people work)

### Step 5: Write It as Narrative Prose

Structure: lead with the people, then the tools, then the workflow change, then
the impact.

Pattern that works:
> "The [titles] at [org] have adopted [tools] for [process], replacing
> [pre-AI workflow with step count] with [post-AI workflow with step count],
> recovering [time/volume], and [qualitative impact]."

Rules:
- No bold template markers
- No consultant jargon
- No field codes or stage numbers
- Two sentences if one gets too long -- but aim for one
- It must read like a case study opening, not a checklist

### Step 6: Test It

Ask: could Simon paste this into a report to a program officer with zero edits?

If not, what's stopping him? Fix that.

Check:
- Does it name specific tools? (not "AI")
- Does it name roles? (not "staff")
- Does it have a before/after contrast with numbers?
- Does it sound like something happened, or like a plan was made?
- Is there anything a funder would need explained?

### Step 7: Write to File and Push

Save to `{ARTIFACT_ROOT}/{folder_name}/4-summary/simon-summary.md`:

```markdown
---
client: {Short Name}
client_page_id: {from org-mapping}
plugin_version: 1.2.0
created_at: {ISO 8601 timestamp}
source: 3-essentials/essentials-review.md
---

# Simon Summary: {Org Full Name}

{The summary sentence(s)}
```

Push to the "Simon Summary" rich_text property on the Client page
(`client_page_id` from org-mapping.md).

If the summary exceeds 2000 characters (Notion rich_text limit), split into
multiple rich_text array elements at sentence boundaries.

Append to pipeline.log:
```
[{ISO 8601 timestamp}] [v1.2.0] [stage-4:simon-summary] [{Short Name}]
  Status: SUCCESS
  Output: 4-summary/simon-summary.md
  Target: Client page {client_page_id} -> "Simon Summary" property
  Characteristics: 6/6 present
  Length: {char count}
```

## Worked Example: SV@Home

Input (from essentials-review.md):
- AI Tech: Promptinator, Google Gemini, ChatGPT
- Personnel: Deputy Directors of Operations and Strategy
- Data: Salesforce membership data exports
- Pre-AI: Staff individually drafted 6-15 articles across 3-4 monthly newsletters
  covering 15 cities, no structured process, previous AI attempts unsatisfactory
- Post-AI: Describe need -> Promptinator structures prompt -> AI generates draft
- Impact: ~240 hours/year recovered; team shifted from AI resistance to independent
  adoption; prompt libraries as organizational infrastructure

Output:
> "The Deputy Directors of Operations and Strategy at Silicon Valley at Home
> adopted the Promptinator, Google Gemini, and ChatGPT for newsletter production
> and membership data analysis, replacing a manual process where staff
> individually drafted 6 to 15 articles across 3 to 4 monthly newsletters
> covering 15 Santa Clara County cities. Staff now use a structured
> prompt-to-draft workflow that recovers approximately 240 hours annually, and
> adoption has spread beyond the coaching participants to additional newsletter
> staff with minimal onboarding. Leadership is building reusable prompt
> libraries as organizational infrastructure while exploring Salesforce data
> exports through Gemini to address long-standing gaps in membership attribution
> tracking."

Why it works:
- Leads with the people (titles, not names)
- Names the tools
- Shows the volume (6-15 articles, 3-4 newsletters, 15 cities)
- States the time recovered (240 hours/year)
- Shows spread beyond the initial participants
- Mentions the in-progress work honestly ("exploring")
- Reads like a case study, not a template

## What This Skill Produces

- `4-summary/simon-summary.md` -- the funder-ready summary with frontmatter
- "Simon Summary" property updated on the Client page in Notion
- Appended entry in `pipeline.log`

## What This Skill Does NOT Do

- Analyze transcripts (Stage 1)
- Populate the 50 fields (Stage 2)
- Push essentials to the Essentials page (Stage 3)
- Generate the Google Doc
- Update component statuses
