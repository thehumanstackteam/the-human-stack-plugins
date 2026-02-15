---
description: Run Jobs-to-be-Done analysis on a call transcript from pasted text, ~~conversation intelligence link, or ~~knowledge base meeting transcript. Saves to company folder with ~~CRM connections.
argument-hint: "<transcript text, Notion link, or Fathom/app URL>"
---

# JTBD Call Analysis

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../CONNECTORS.md).

Analyze a call transcript through Tim Lockie's Jobs-to-be-Done framework. Produces a structured analysis file saved to a company folder under `Jobs To Be Done/`.

**Related commands:** Use after sales calls (pairs with `sales:call-summary`), for product research synthesis (pairs with `product-management:synthesize-research`), and for productivity tracking (pairs with `productivity:update`).

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
- Notion page ID/URL (for Connections section)
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

**Write the file directly** as you generate the analysis. Do not hold content in memory and write it separately -- that forces regenerating thousands of tokens. If using a subagent, pass the target file path and instruct the subagent to write the file itself using the Write tool. Never have a subagent return content for the parent to re-write.

### 6. Enrich Existing Files (Optional)

If user asks to update connections on existing files, or says "update all connections":

1. List all `.md` files across ALL `Calls & Meetings/` subdirectories in every top-level folder
2. For each file, check if it has a `## CONNECTIONS` section
3. If missing or incomplete (contains `[Add link]` placeholders):
   - Extract company name from folder name
   - Extract participant names from file content
   - Run ~~CRM lookups (Step 4)
   - Search ~~knowledge base Meeting Transcripts database for matching meetings by date/company
   - Update ONLY the `[Add link]` placeholder fields — never overwrite existing valid links

## Multiple Transcripts

When given multiple transcript files in one invocation:
1. Process them **sequentially**, one at a time
2. Complete the FULL workflow (acquire, identify, analyze, connect, save) for each file before starting the next
3. Do NOT use task tracking (TaskCreate/TaskUpdate) -- it adds overhead with no value
4. Share HubSpot lookups across files if they are for the same company (avoid redundant searches)

## Binary Transcript Files (.docx, .pdf)

If the user provides .docx files, convert them to text using `textutil -convert txt -stdout "<path>"` (macOS) before processing. For PDFs, use the Read tool with the `pages` parameter.

## Important Notes

- The `JTBD-Analysis-Prompt.md` in `Jobs 2B Done - Plugin & Skills/` is the single source of truth for methodology. Always read it fresh — it gets updated.
- Fuzzy match company folders aggressively. Only create new folders for clearly different organizations.
- ~~CRM searches may return multiple results. Use the most likely match. If ambiguous, ask.
- If the transcript source was ~~knowledge base, always include the page link in connections.
- After saving, mention related next steps: run `jtbd-synthesis` to update cross-call patterns, log concepts with `thought-leadership-librarian`, or prep for next call with `sales:call-prep`.
