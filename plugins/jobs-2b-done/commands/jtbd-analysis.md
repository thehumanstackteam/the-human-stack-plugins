---
description: Run Jobs-to-be-Done analysis on a call transcript from pasted text, ~~conversation intelligence link, or ~~knowledge base meeting transcript. Saves to company folder with ~~CRM connections and populates the JTBD Analyses Notion database.
argument-hint: "<transcript text, Notion link, or Fathom/app URL>"
---

# JTBD Call Analysis

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../CONNECTORS.md).

Analyze a call transcript through Tim Lockie's Jobs-to-be-Done framework. Produces a structured analysis file saved to a company folder under `Jobs To Be Done/`, then creates a corresponding record in the **JTBD Analyses** Notion database.

**Related commands:** Use after sales calls (pairs with `sales:call-summary`), for product research synthesis (pairs with `product-management:synthesize-research`), and for productivity tracking (pairs with `productivity:update`).

## Key References

- **JTBD Analyses Notion DB**: `2f218faa725b41828194e8fc0f93453b`
- **JTBD Analyses Data Source**: `collection://fbf274fd-5cf0-4afe-9eaf-cb511cae6b94`
- **Meeting Transcripts DB**: `8368d3474cac4e71bf945934fce957f7`, collection `669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5`
- **HubSpot Portal**: `22283601`
- **Database Schema**: Inline below in Step 6b (authoritative source for all valid property values)

## Workspace Structure

The `Jobs To Be Done/` workspace is organized into top-level folders. Each folder has its own `Calls & Meetings/` and `Synthesis/` subfolders:

```
Jobs To Be Done/
├── Diagnostic & Managed Success/
│   ├── Calls & Meetings/[Company]/     ← client call analyses
│   └── Synthesis/                       ← cross-call synthesis reports
├── Project Evident Coaching/
│   ├── Calls & Meetings/[Company]/
│   └── Synthesis/
├── Webinars & Speaking/
│   ├── Calls & Meetings/[Company]/
│   └── Synthesis/
└── Jobs 2B Done - Plugin & Skills/      ← prompts, templates, plugin files
```

**New folders may be added at any time.** Always scan for the current list of top-level folders.

---

## Workflow

### 1. Acquire Transcript

Accept transcript from ONE of these sources. If unclear, ask which:

**Option A — Pasted text**: User pastes transcript directly. Use as-is.

**Option B — ~~conversation intelligence link**: User provides a URL (e.g., Fathom, Fireflies, Gong). Use WebFetch to retrieve transcript content. Save the source URL for the Fathom Recording connection field.

**Option C — ~~knowledge base Meeting Transcript**: User provides either:
- A direct Notion page link → Use `notion-fetch` tool to retrieve it
- A company/meeting name to search → Use `notion-search` tool with `data_source_url: "collection://669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5"` to find the transcript in the Meeting Transcripts database (ID: `8368d3474cac4e71bf945934fce957f7`). If multiple matches, present options and ask user to pick.

**Extract from ~~knowledge base transcripts:**
- Notion page ID/URL (for Connections section and Meeting Transcript link)
- `Fathom ID` property (if present, construct Fathom video link)
- `Fathom Invitees` / `Attendees 1` properties (participant names)
- Page title and created date (for file naming)
- Full transcript content from page body

### 2. Identify Company, Participants & Folder

From the transcript content, extract:
- **Company name** — the prospect/client organization (NOT The Human Stack)
- **Individual participant names** and their roles
- **Call date** — from metadata, transcript header, or ask user

**Determine which folder to save in:**

1. List the current top-level folders in `Jobs To Be Done/` (excluding `Jobs 2B Done - Plugin & Skills/`)
2. If the company already has a folder under one of them, use that one (check all `Calls & Meetings/` subfolders)
3. If the call type/context makes the folder obvious (e.g., diagnostic engagement → `Diagnostic & Managed Success`, coaching session for Project Evident → `Project Evident Coaching`, webinar/keynote → `Webinars & Speaking`), use it
4. **If neither condition is met, ask the user** which folder to file under. Present the available folders as options.

**Company folder matching within the selected folder:**
1. List existing subfolders in `Jobs To Be Done/[Folder]/Calls & Meetings/`
2. If a folder name is >=90% similar to the identified company name (case-insensitive), use that existing folder
3. Only create a new company folder if no match meets the 90% threshold
4. If the `Calls & Meetings/` subfolder doesn't exist yet, create it

### 3. Load and Run JTBD Analysis

1. **Read the master prompt** from: `Jobs To Be Done/Jobs 2B Done - Plugin & Skills/JTBD-Analysis-Prompt.md`
2. **Apply the full prompt framework** to the transcript — all 9 analysis dimensions
3. **Generate the complete analysis** following the OUTPUT FORMAT in that prompt file
4. **Analysis rules:**
   - Be specific, not generic ("get 12-person team to use CRM for case notes" NOT "improve technology adoption")
   - Quote liberally with exact language from the transcript
   - Distinguish explicit statements from inferences (mark with [INFERRED] or [IMPLIED])
   - Flag contradictions between what they say vs. behavior/evidence
   - Intensity = importance (repeated phrases, long explanations, emotional language)
   - Context matters — same JTBD means different things from prospect vs. 90-day client

### 4. Build Connections Section

Prepend a `## CONNECTIONS` section at the top of the analysis. Populate each field:

```markdown
## CONNECTIONS

**Fathom Recording**: [URL from input or ~~knowledge base Fathom ID field, or "[Add link]"]
**Notion Meeting Notes**: [~~knowledge base page URL if source was Notion, or "[Add link]"]
**HubSpot Account**: [~~CRM company record link]
**HubSpot Contacts**: [~~CRM linked contact names]
**HubSpot Deal**: [~~CRM deal link or "[Add link]"]
**Clay URL**: [Clay enrichment URL if available, or "[Add link]"]
```

**~~CRM lookup procedure:**

1. **Company**: Search CRM objects (objectType: `COMPANY`) by company name. Get the company ID.
2. **Contacts**: For each participant name, search CRM objects (objectType: `CONTACT`). Get contact IDs.
3. **Deals**: Search CRM objects (objectType: `DEAL`) filtered by company association. Get active deal IDs.
4. **Construct URLs** using HubSpot portal ID `22283601`:
   - Company: `https://app.hubspot.com/contacts/22283601/record/0-2/{companyId}`
   - Contact: `https://app.hubspot.com/contacts/22283601/record/0-1/{contactId}`
   - Deal: `https://app.hubspot.com/contacts/22283601/record/0-3/{dealId}`
5. Format contacts as: `[Person Name](hubspot_url)`
6. If no ~~CRM match found: `[Person Name - Add link]`

### 5. Assemble and Save File

**File naming convention:**
- **Single external participant**: `[YYYY-MM-DD] - [First Last, Company Name] - JTBD Analysis.md`
- **Multiple participants from same org**: `[YYYY-MM-DD] - [Company Name] - JTBD Analysis.md`

Examples:
- `2025-07-02 - Haley MacDonald, Imagine Canada - JTBD Analysis.md`
- `2025-07-22 - Episcopal Relief & Development - JTBD Analysis.md`

**Save to**: `Jobs To Be Done/[Folder]/Calls & Meetings/[Company Name]/[filename].md`

**Always show the user the completed analysis before saving** so they can review.

### 6. Populate JTBD Analyses Notion Database

After saving the .md file, create a page in the **JTBD Analyses** database. This is the structured, queryable layer that links back to the full analysis and the source transcript.

**Database**: `2f218faa725b41828194e8fc0f93453b`
**Data source**: `collection://fbf274fd-5cf0-4afe-9eaf-cb511cae6b94`

Use `notion-create-pages` with `parent: { data_source_id: "fbf274fd-5cf0-4afe-9eaf-cb511cae6b94" }`.

#### 6a. Page Body Content (MANDATORY -- DO THIS FIRST)

The Notion page body MUST contain the **complete, unmodified analysis text** -- the exact same content saved in the .md file. This is the most important part of the database record.

**HARD RULES:**
- Copy the ENTIRE .md file content into the page body. Every section, every quote, every line.
- Do NOT summarize, truncate, abbreviate, or paraphrase any part of the analysis.
- Do NOT skip sections to save space or reduce length.
- Do NOT rewrite headings, quotes, or formatting.
- The page body must be a verbatim copy of the saved .md file.
- If the Notion API has length limits, split across multiple content blocks -- never cut content.

#### 6b. Property Mapping (exact valid values)

Extract properties from the completed analysis. For select/multi-select fields, use ONLY the exact values listed below. If a value from the analysis doesn't match any listed option, OMIT the field -- never guess or create new values.

**Text properties:**

| Property | Source |
|----------|--------|
| Name | File title (e.g., "2025-07-02 - Haley MacDonald, Imagine Canada") |
| Organization | Company name from Step 2 |
| Date | Call date from Step 2 (use `date:Date:start` with ISO-8601 date) |
| File Path | Full path where .md was saved |
| Primary JTBD | From `### PRIMARY JTBD` one-sentence synthesis |
| Quick Summary | From `### QUICK SUMMARY` -- concatenate all 5 summary lines |
| Persona Label | From `### AUDIENCE SEGMENT` -> Persona Label |
| Known Pattern | From `### PATTERN RECOGNITION` -> Known Pattern |
| Emerging Pattern | From `### PATTERN RECOGNITION` -> Emerging Pattern |
| HubSpot Contacts | From CONNECTIONS -- formatted as "Name (link), Name (link)" |

**Select properties (pick exactly ONE from the listed values):**

| Property | Source | Valid Values |
|----------|--------|-------------|
| Engagement Stage | `CONTEXT METADATA` -> Engagement Stage | `Pre-sale`, `Discovery`, `Active 0-90`, `Active 90+`, `Alumni` |
| Best-Fit Offering | `### PRODUCT/OFFERING IMPLICATIONS` | `Coaching`, `Diagnostic`, `Managed Success`, `Training`, `Speaking`, `Upskillerator` |
| Urgency Level | `### SWITCH TRIGGER` -> Urgency Level | `High`, `Medium`, `Low`, `Unclear` |
| Confidence Score | `### DETAILED JTBD ANALYSIS` | `High`, `Medium`, `Low` |
| Speaker Role | `CONTEXT METADATA` -> Primary Speaker role | `CEO/ED`, `COO/VP`, `CTO/Tech Director`, `Program Director`, `Development/Fundraising`, `Operations`, `Board Member`, `Consultant/Partner`, `Other` |
| Speaker POV | `CONTEXT METADATA` -> Primary Speaker POV | `Executive`, `Practitioner`, `Influencer`, `Champion`, `End User`, `Channel Partner` |
| Decision Authority | `### AUDIENCE SEGMENT` | `Decision-maker`, `Influencer`, `Champion`, `End User` |
| Org Size | `CONTEXT METADATA` -> Org Size | `Small (<50)`, `Mid (50-500)`, `Large (500+)` |
| Sector | `CONTEXT METADATA` -> Sector | `Human Services`, `Education`, `Health`, `Faith-based`, `Infrastructure`, `Arts`, `Environment`, `Cross-sector Consulting`, `Other` |

**Multi-select properties (pick one or more from the listed values, pass as JSON array):**

| Property | Source | Valid Values |
|----------|--------|-------------|
| Product Context | `CONTEXT METADATA` -> Product | `Diagnostic`, `Managed Success`, `Training`, `Speaking`, `Consulting` |
| Pillar Focus | `CONTEXT METADATA` -> Pillar | `Capacity`, `Strategy`, `Transformation` |
| Frameworks Applied | `### IP & FRAMEWORK APPLICATION` | `Digital Guidance`, `Digital Health Framework`, `Culture Eats Tech`, `Capacity Building`, `Orchestra Metaphor` |
| Themes | Scan analysis for theme indicators (see below) | `vendor-dependency`, `tech-trauma`, `lone-wolf`, `permission-to-lead`, `AI-anxiety`, `change-saturation`, `bright-shiny-object`, `training-gap`, `trust-deficit`, `silo`, `accidental-techie`, `governance-vacuum`, `channel-partner`, `strategy-execution-gap`, `lone-ranger-blocker` |

**URL properties (omit if value is `[Add link]` or empty):**

| Property | Source |
|----------|--------|
| Fathom Recording | From CONNECTIONS section |
| HubSpot Account | From CONNECTIONS section |
| HubSpot Deal | From CONNECTIONS section |
| Clay URL | From CONNECTIONS section |

**Relation property:**

| Property | Source |
|----------|--------|
| Meeting Transcript | Notion page URL of source transcript (from Step 1, Option C). This is a relation to collection `669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5`. |

#### 6c. Themes Detection

Scan the analysis for these theme indicators and tag accordingly:

| Theme tag | Indicators in transcript/analysis |
|-----------|----------------------------------|
| `vendor-dependency` | consultant/vendor lock-in, outsourced knowledge |
| `tech-trauma` | past failed implementations, burned by technology |
| `lone-wolf` | single person carrying all tech responsibility |
| `permission-to-lead` | seeking validation to make decisions |
| `AI-anxiety` | fear or uncertainty about AI adoption |
| `change-saturation` | too many changes happening at once |
| `bright-shiny-object` | chasing new tools without strategy |
| `training-gap` | staff lack skills to use systems |
| `trust-deficit` | low trust in systems, data, or leadership |
| `silo` | disconnected departments, data, or systems |
| `accidental-techie` | non-technical staff managing technology |
| `governance-vacuum` | no decision framework for technology |
| `channel-partner` | intermediary/partner relationship |
| `strategy-execution-gap` | good strategy but poor implementation |
| `lone-ranger-blocker` | individual blocking organizational progress |

### 7. Enrich Existing Files (Optional)

If user asks to update connections on existing files, or says "update all connections":

1. List all `.md` files across ALL `Calls & Meetings/` subdirectories in every top-level folder
2. For each file, check if it has a `## CONNECTIONS` section
3. If missing or incomplete (contains `[Add link]` placeholders):
   - Extract company name from folder name
   - Extract participant names from file content
   - Run ~~CRM lookups (Step 4)
   - Search ~~knowledge base Meeting Transcripts database for matching meetings by date/company
   - Update ONLY the `[Add link]` placeholder fields — never overwrite existing valid links
4. Also check if a corresponding JTBD Analyses DB record exists. If not, create one (Step 6).

## Important Notes

- The `JTBD-Analysis-Prompt.md` in `Jobs 2B Done - Plugin & Skills/` is the single source of truth for methodology. Always read it fresh — it gets updated.
- Fuzzy match company folders aggressively. Only create new folders for clearly different organizations.
- ~~CRM searches may return multiple results. Use the most likely match. If ambiguous, ask.
- If the transcript source was ~~knowledge base, always include the page link in connections AND in the Meeting Transcript property.
- After saving, mention related next steps: run `jtbd-synthesis` to update cross-call patterns, log concepts with `thought-leadership-librarian`, or prep for next call with `sales:call-prep`.
- The Notion DB record is the queryable index. The .md file is the full human-readable analysis. Both get created every time.
