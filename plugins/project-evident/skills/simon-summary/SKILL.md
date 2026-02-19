---
name: simon-summary
description: >
  Stage 4 of the Project Evident pipeline. Reads the essentials-review.md output
  for a coaching client and generates a funder-ready impact statement for Simon's
  report. Written to the "Simon Summary" property on the client's page in the
  Clients database. The statement must be something Simon can drop into a funder
  report next to 10 other client summaries with zero edits.
  Use for "write simon summary", "generate summary for [client]", "run stage 4",
  "simon summary for [client]".
---

# Simon Summary (Stage 4)

Read the essentials-review.md for a client -> write a funder-ready impact
statement -> push to the "Simon Summary" rich_text property on the client's
page in the Clients database.

**Plugin version: 2.3.0**

**Invocation required:** This output must be produced by invoking this skill or
by the orchestrator reading this file from disk before running Stage 4. Do not
write a simon summary inline in conversation. If someone asks to "write a summary"
or "generate the simon summary", invoke `/project-evident:simon-summary` or
`/run-pipeline`. Summaries written without these instructions will miss critical
rules (no dollar amounts, no plumbing, staff not titles, mission not adoption).

---

## Who is Simon

Simon runs a coaching program that teaches nonprofits to adopt AI tools. Funders
pay for this program. Simon reports results to those funders to justify the next
round of funding. He has 11 clients. He writes one impact statement per client
and lines them up in a report. A program officer reads all 11, scanning for proof
that the investment produced results for the people these organizations serve.

Simon does not have time to edit. He does not want to rewrite. He needs to paste
your output directly into his report.

---

## What You Produce

Two sentences. An impact statement that answers one question: did this coaching
engagement produce results for the people this organization serves?

Not a case study. Not narrative prose. Not a story with an anecdote. An impact
statement that a program officer reads in a list of 11 and thinks "this is real."
If it reads like a case study, it's wrong. If it reads like a line item in a
funder report, it's right.

---

## The Chain of Evidence

Every impact statement answers the funder's question through a chain:

1. **They had a real problem** -- specific, not vague
2. **The problem was blocking something that matters** -- connected to mission
3. **The change is measurable** -- numbers that prove it happened
4. **And here's why it matters** -- benefits for the people the organization serves

Everything before step 4 is earning the right to say step 4. The numbers aren't
the point. The numbers are the proof. The point is: the people this organization
serves are better off.

---

## How to Write It

### Sentence 1: The Tension

Sentence 1 states a tension: what the organization needed to do for its mission
vs. what prevented them from doing it. Not a description of how staff spent their
time. A gap between what the mission required and what was possible.

Why tension, not description: "Staff spent a full day researching and writing each
letter of inquiry" describes a process. The funder understands what was happening
but not why it matters. "Texas Advocacy Project needed to cultivate a portfolio of
private family foundation prospects but each required 8 or more hours of manual
research" states a need and a constraint in tension. The funder immediately
understands the problem isn't the hours -- it's that the hours made the mission
goal impossible at scale.

### Sentence 2: The Tool and the Benefits

Sentence 2 states the tool (one platform name with a parenthetical explaining
what it does), then a comma-separated cascade of benefits sourced from the C4P2
fields. Every benefit points toward the people the organization serves.

The last words of the summary name the people being served or the mission outcome.
That's the last thing the funder reads.

---

## Choosing the Lead

Each client has a strongest card. The lead is earned by the data, not chosen at
random or by rotation. Read the benefits fields and identify the one that would
make a program officer stop skimming. Evaluate in this order:

### 1. Constraint

Does the population or context make the problem unusually hard to solve? If the
solution had to navigate barriers most organizations don't face (digital divide,
language, trauma, accessibility, regulatory), lead with the constraint. The
constraint explains why the solution matters before you describe the solution. A
funder reads it and thinks "this is hard" -- then everything after proves the
coaching cracked it.

Example: Building Promise serves justice-impacted individuals where 25% lack
phones and many don't read English. The AI solution had to navigate barriers
most organizations don't face. The constraint IS the headline.

### 2. Blockage

Was something stuck, growing, or impossible before? If backlogs were accumulating,
outreach was stalled, or staff couldn't do their actual job, lead with what was
blocked. Small time savings become meaningful when you show what they were
preventing.

Example: TAP needed to cultivate a portfolio of foundation prospects but each
required a full day of manual work. The mismatch between the need and the
capacity is the story, not the hours themselves.

### 3. Time Collapse

Is the before/after time contrast dramatic on its own? If the numbers are large
enough that a funder immediately grasps the scale (a full day to minutes, 240
hours/year recovered), lead with the problem and let the time contrast land.

Use this only when the per-unit or aggregated time savings are genuinely dramatic.
If the time savings are small (under 100 hours/year), they're not the lead --
they support a blockage or constraint lead instead.

### 4. Tool

Is the tool itself novel or unexpected for this sector? Default to this only
when the other three don't clearly win. Simon's own gold standard uses a tool
lead with JotForm because the tool-to-problem-to-impact chain flows naturally
in one sentence.

---

## Rules

### Tool Description

One platform name, then parenthetical describing capabilities. Not a list of
tool names. The funder needs to understand what the tool does, not its product
names.

Good: "Google Gemini with AI-powered image-to-table extraction (converting phone
camera photos of handwritten forms into structured data and digitizing business
cards into contact databases)"

Bad: "Google Gemini Deep Research, NotebookLM, Gemini Gems, and the Promptinator"

Why: Simon's gold standard says "JotForm with AI automation capabilities (powered
by AI-enhanced features including video upload capability and integrated text
message notifications)." One tool name, then what it does. The funder understands
the capability, not the product catalog.

### People

"Staff." Not titles. Not names. Simon's own gold standard says "with staff for
intake process automation." The role is implied by the task. "Staff for grant
writing" -- you know it's the development team. Three C-suite titles don't add
anything a funder needs.

### Benefits

Sourced from the C4P2 benefit fields (Cost Savings, Productivity Gains, Policy
Changes, Service Delivery Improvements, Outcomes Improved, Increased Funding,
Other Changes). Every checked YES with a description is a candidate. Translate
each one into what it means for the people the organization serves.

Never include internal adoption signals -- CEO readiness, staff teaching each
other, organizational culture shifts. Those describe what changed inside the
organization, not what changed for the mission. A funder reads "the CEO is
ready for a presentation" and thinks: so the CEO still isn't using AI? That's
not a win, that's a gap being spun.

The benefits in Simon's gold standard are all about the people the nonprofit
serves, not the nonprofit itself: "improved client matching allowing clients to
choose clinicians, ability to reach more people, greater client satisfaction by
receiving services sooner." Not "staff are happier" or "the CEO is on board"
or "adoption is spreading."

### Last Words

The summary must end with the people being served or the mission outcome. If
the summary ends with an internal change, move a mission benefit to the end.
The last thing the funder reads should be the reason the organization exists.

### Numbers

No dollar amounts. No ranges -- pick one defensible number. A range says "we're
not sure" and a funder can't cite it.

Identify the scale a funder thinks in. A funder doesn't think in per-unit labor.
They think in: weeks of staff time, percentage of a role, or what that time could
have funded instead. Per-unit numbers should be checked against volume:

- 8 hours per letter x 17 prospects = over 3 weeks of full-time work
- 2 hours per month x 12 = 24 hours/year (not a compelling headline)
- 4 hours per week for 10-20 people (already aggregated -- lands immediately)

Use whichever framing -- per-unit, aggregated, or reframed around blockage --
tells the strongest honest story. When the quantitative number is small (under
100 hours/year), don't lead with time. Lead with what the number was preventing.
Never inflate a small number. Reframe around blockage.

### Writing Style

Reportorial. AP style with a side of social impact. Facts carry the weight. The
social impact context gives the facts meaning.

- No adjectives doing persuasion work ("dramatic," "innovative," "transformative,"
  "significant," "powerful") -- the facts persuade
- No consultant jargon ("AI-assisted grant writing pipeline" is consultant
  framing; "grant writing" is a plain noun)
- No hedging ("staff now capture" not "staff are now able to capture")
- No emotional language -- the more painful the constraint or impressive the
  result, the flatter the tone. Let the reader have the reaction. Don't have
  it for them.
- Numbers are concrete but not decorated ("over a year's backlog" not "a
  staggering 12-month backlog")
- Constraints and problems are stated flatly, not dramatized ("25% of attendees
  lack phones" not "a quarter of vulnerable participants struggle without access
  to mobile devices")
- Benefits are listed as outcomes, not claims ("recovering the Director of
  Programs for program management" not "empowering the Director to focus on
  what matters most")
- Present tense for the after, past tense for the before
- Third person, no "we" or "our"
- If any word is doing emotional work instead of factual work, cut it.
  "Dramatic reduction" becomes "reduction from X to Y."

### Never Include

- **Pipeline architecture** (tool A feeds tool B feeds tool C). Never describe
  how tools work. Describe what changed because of them. Simon's gold standard
  never tells you how JotForm routes forms or sends SMS. It says "3-step
  automated system" and moves on to impact.
- **Internal adoption signals** (CEO readiness, staff teaching each other,
  organizational culture shifts, "magical-to-mechanical" progression)
- **Ranges** instead of single numbers
- **Anecdotes or narrative storytelling** -- no moonshot stories, no "when X
  arrived with a Monday deadline" drama
- **Anything that describes organizational change without connecting to the
  people served**
- **Plumbing** (Drive folders, custom instructions, source selection,
  human-in-the-loop architecture)

---

## Self-Evaluation

After drafting, run these checks. If any check fails, don't patch -- rewrite
the failing element.

### 1. Tension Test

Cover sentence 2. Read sentence 1 alone. Does it contain a "needed X but Y"
tension where X connects to mission and Y is the constraint? If it reads as
"staff did X using Y," it's a description, not a tension. Rewrite sentence 1
around the gap between what the mission required and what was possible.

Why this matters: a description tells the funder what was happening. A tension
tells them why it matters. "Staff spent a full day researching" is a description.
"Needed to cultivate a portfolio but each required a full day" is a tension. The
funder feels the gap before they see the solution.

### 2. Plumbing Test

Does any clause describe how a tool works internally? "Stacks files into Drive
folders," "synthesizes through NotebookLM with custom instructions,"
"human-in-the-loop at each stage" -- that's plumbing. If the clause describes
what happens inside the pipeline rather than what changed for the organization,
cut it.

Why this matters: Simon's gold standard never tells you how JotForm routes forms.
A funder reading "stacks files into curated Google Drive folders" thinks "so
what?" That's implementation architecture, not impact.

### 3. Mission Test

Read each benefit in the cascade. Ask: does this benefit the people the org
serves, or the org itself? "CEO moving to readiness" benefits the org.
"Recovering staff time for direct legal services to domestic violence survivors"
benefits the people served. Cut any benefit that stops at the org.

Why this matters: the funder funded a nonprofit that serves people. They want
to know those people are better off. Not that staff learned AI. Not that the
CEO is ready for a presentation. The gold standard ends with: "clients choose
clinicians, reach more people, services sooner." All mission.

### 4. Last Words Test

What are the final words of the summary? They should name the people being
served or the mission outcome. If they name an internal change, move a mission
benefit to the end.

Why this matters: the last thing the funder reads is what they remember. If it's
"staff teaching colleagues unprompted," they remember internal adoption. If it's
"direct legal services to domestic violence survivors," they remember the mission.

### 5. Adjective Test

Scan for any adjective carrying the argument: "dramatic," "transformative,"
"innovative," "significant," "powerful," "comprehensive." If removing the
adjective loses no factual information, it was doing emotional work. Cut it.

Why this matters: reportorial style. The facts persuade. If you need an adjective
to make the impact sound impressive, the impact isn't stated specifically enough.
"Dramatic reduction from 10-step to 3-step" -- remove "dramatic" and you still
have the proof. The adjective added nothing.

### 6. Hedge Test

Scan for "able to," "enables," "allows," "helps," "can now," "positioned to,"
"expected to." Replace with direct verbs. "Staff are now able to capture" becomes
"staff now capture." "The workflow enables faster response" becomes "faster
response to time-sensitive grants."

Why this matters: hedging signals uncertainty. Simon needs certainty. If the
thing happened, state it. If it didn't happen, don't include it.

### 7. Scale Test

Find the quantitative number. Is it per-unit? Multiply by volume. Does the
per-unit number, the aggregated number, or reframing around blockage tell the
strongest honest story? Use that framing.

- Per-unit is strong when the contrast is dramatic: "8 hours to 10 minutes"
- Aggregated is strong when the volume is large: "over 3 weeks of full-time work"
- Blockage reframe is strong when the number is small: "backlogs blocking
  program reporting and vendor outreach"

If the aggregated number is still small, don't lead with it -- lead with what
it was blocking. Never inflate. Reframe.

---

## Prerequisites

- Completed essentials-review.md (Stage 2 output)
- Quality gate passed (or pipeline proceeded with flagged gaps)
- Notion MCP connector for writing to Client page

Load reference files:
  - `references/org-mapping.md` -- client page IDs and folder names
  - `references/simon-criteria.md` -- the 7 Essential Elements

---

## The Process

### Step 1: Extract the raw ingredients

Read essentials-review.md and pull content for each element:

| Element | Primary Source Fields |
|---------|---------------------|
| AI Tech | C1P2, C3P1T1F2 |
| Pre-AI Workflow | C4P1F1, C1P1T1, C1P1T2 |
| Post-AI Workflow | C4P1F2, C3P2T1F2, C3P3T1F2 |
| Benefits | C4P2 fields (all checked YES with descriptions) |
| Mission context | Coaching Notes, organization description |

Note: Personnel is always "staff" in the output. You still need to understand
who was involved to accurately describe what changed, but the summary uses
"staff" not titles or names.

### Step 2: Choose the lead

Read the benefits fields. Identify the strongest card using the lead selection
hierarchy: constraint > blockage > time collapse > tool.

### Step 3: Draft two sentences

Sentence 1: the tension (needed X but Y).
Sentence 2: the tool with parenthetical + benefit cascade ending with mission.

### Step 4: Run the self-evaluation

All 7 tests. If any fails, rewrite the failing element. Do not patch. Rewrite.

### Step 5: Write to file and push

---

## Write to File and Push

Save to `{ARTIFACT_ROOT}/{folder_name}/4-summary/simon-summary.md`:

```markdown
---
client: {Short Name}
client_page_id: {from org-mapping}
plugin_version: 2.3.0
created_at: {ISO 8601 timestamp}
source: 3-essentials/essentials-review.md
---

# Simon Summary: {Org Full Name}

{The two sentences}
```

Push to the "Simon Summary" rich_text property on the Client page
(`client_page_id` from org-mapping.md).

If the summary exceeds 2000 characters (Notion rich_text limit), split into
multiple rich_text array elements at sentence boundaries.

Append to pipeline.log:
```
[{ISO 8601 timestamp}] [v2.3.0] [stage-4:simon-summary] [{Short Name}]
  Status: SUCCESS
  Output: 4-summary/simon-summary.md
  Target: Client page {client_page_id} -> "Simon Summary" property
  Lead type: {constraint|blockage|time_collapse|tool}
  Self-eval: {N}/7 passed on first draft
  Length: {char count}
```

---

## Worked Examples

### Constraint Lead: Building Promise USA

**Why constraint leads:** Building Promise serves justice-impacted individuals
where 25% lack phones and many don't read English. The AI solution had to
navigate barriers most organizations don't face. The constraint explains why
the solution matters before you describe it. A funder reads it and thinks
"this is hard" -- then everything after proves the coaching cracked it.

> Building Promise USA serves justice-impacted individuals where 25% of
> attendees lack phones, many do not read English, and digital tools trigger
> the same institutional barriers participants already face -- requiring any
> data collection solution to work with nothing more than paper and a phone
> camera. Using Google Gemini with AI-powered image-to-table extraction
> (converting phone camera photos of handwritten forms into structured data
> and digitizing business cards into contact databases), staff now capture
> event data at the point of service, clearing over a year's backlog of
> unprocessed voucher forms and 150 undigitized employer contact cards that
> were blocking program reporting and vendor outreach, recovering the Director
> of Programs from manual data entry to focus on program management and
> partnerships, improving program reporting with data captured at checkout
> instead of unanswered follow-up surveys, and externalizing three years of
> institutional knowledge from one staff member's memory into documented
> systems a successor can operate.

Why it works:
- Leads with the constraint -- the funder understands why this is hard before
  seeing the solution
- Tool described by what it does, not product names
- Benefits cascade: clearing backlogs, recovering a role, improving reporting,
  knowledge transfer -- all mission-connected
- No plumbing (doesn't describe how Gemini processes images internally)
- No adoption signals (doesn't mention staff attitudes or leadership buy-in)
- Reportorial tone -- "25% of attendees lack phones" stated flatly

### Blockage Lead: Texas Advocacy Project

**Why blockage leads:** TAP's time savings are dramatic per-unit (8 hours to 10
minutes) but the real story is the mismatch -- a portfolio of prospects they
needed to cultivate but couldn't at scale. "Needed X but Y" makes the funder
feel the gap immediately.

> Texas Advocacy Project needed to cultivate a portfolio of private family
> foundation prospects but each required 8 or more hours of manual research
> and copy-pasted boilerplate. Using Google Gemini with AI-powered deep
> research and synthesis capabilities (including automated foundation prospect
> profiling, source-based document synthesis through NotebookLM, and
> specialized writing assistants through Gemini Gems), staff now complete
> foundation research in under 10 minutes per prospect, reducing grant writing
> preparation from a full day to hours, increasing capacity to pursue funding
> opportunities across the full portfolio, enabling faster response to
> time-sensitive grants, improving research quality, and recovering staff time
> from manual grant work for direct legal services to domestic violence
> survivors.

Why it works:
- Leads with blockage -- the portfolio need vs. the per-prospect constraint
- "Needed X but Y" tension in sentence 1, not a process description
- Tool described as one platform with parenthetical capabilities
- Benefits cascade ends with mission: "direct legal services to domestic
  violence survivors" -- the last thing the funder reads
- No anecdotes (the moonshot grant story is compelling but it's narrative, not
  an impact statement)
- No internal adoption (CLO teaching colleagues, CEO readiness -- cut)
- Scale: per-unit contrast (8 hours to 10 minutes) is dramatic enough to use
  directly, plus the aggregated "full day to hours" framing

### Tool Lead: Simon's Gold Standard

**Why tool leads:** Sometimes the tool itself is the clearest entry point.
Simon's own example leads with JotForm because the tool-to-problem-to-impact
chain flows naturally in one sentence. This is the default when constraint,
blockage, and time collapse don't clearly win.

> The organization is using JotForm with AI automation capabilities (powered by
> AI-enhanced features including video upload capability and integrated text
> message notifications) with staff for intake process automation to solve
> time-consuming manual 10-step intake workflow that required staff to work
> alone on intake, phone call coordination, and therapist matching, achieving
> dramatic reduction from 10-step manual workflow to 3-step automated system,
> reduced intake processing time from 4 hours per week (for 10-20 people) to
> 30 minutes, increased productivity allowing staff capacity reallocation to
> other organizational areas, improved client matching allowing clients to
> choose clinicians, ability to reach more people, greater client satisfaction
> by receiving services sooner, and saving staff time and money.

Why it works:
- Tool described by what it does, not just product name
- "Staff" not titles or names
- Problem is specific: 10-step, phone coordination, therapist matching
- Numbers land fast: 10 to 3 steps, 4 hours to 30 minutes, 10-20 people
- Benefits all point to mission: clients choose clinicians, reach more people,
  services sooner
- The funder never learns how JotForm routes forms or sends SMS internally

---

## What This Skill Produces

- `4-summary/simon-summary.md` -- the funder-ready impact statement with frontmatter
- "Simon Summary" property updated on the Client page in Notion
- Appended entry in `pipeline.log`

## What This Skill Does NOT Do

- Analyze transcripts (Stage 1)
- Populate the 50 fields (Stage 2)
- Push essentials to the Essentials page (Stage 3)
- Generate the Google Doc
- Update component statuses
