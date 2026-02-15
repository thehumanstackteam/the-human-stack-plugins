# JTBD Analysis Skill

Run Jobs-to-be-Done analysis on call transcripts using Tim Lockie's structured framework. This skill powers both the `jtbd-analysis` command and the standalone `jtbd-analysis` skill.

## Quick Reference

- **Analysis Prompt**: `Jobs To Be Done/Jobs 2B Done - Plugin & Skills/JTBD-Analysis-Prompt.md`
- **Synthesis Prompt**: `Jobs To Be Done/Jobs 2B Done - Plugin & Skills/JTBD-Synthesis-Prompt.md`
- **Database Schema**: `Jobs To Be Done/Jobs 2B Done - Plugin & Skills/JTBD-Database-Schema.md`
- **Notion Meeting Transcripts DB**: ID `8368d3474cac4e71bf945934fce957f7`, collection `669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5`
- **HubSpot Portal**: `22283601`

## Transcript Sources

1. **Pasted text** — use directly
2. **~~conversation intelligence URL** (Fathom, Fireflies, Gong) — fetch via WebFetch
3. **~~knowledge base Meeting Transcript** — fetch via `notion-fetch` or search via `notion-search` with `data_source_url: "collection://669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5"`

## Folder Structure

```
Jobs To Be Done/
├── Diagnostic & Managed Success/
│   ├── Calls & Meetings/[Company]/
│   └── Synthesis/
├── Project Evident Coaching/
│   ├── Calls & Meetings/[Company]/
│   └── Synthesis/
├── Webinars & Speaking/
│   ├── Calls & Meetings/[Company]/
│   └── Synthesis/
└── Jobs 2B Done - Plugin & Skills/
```

**Always scan for current folders** — new ones may appear.

## Core Workflow

1. **Get transcript** from one of the three sources
2. **Extract** company name, participants, call date
3. **Determine folder** — check if company already exists in a folder; if obvious from context, auto-select; otherwise ask the user
4. **Read `JTBD-Analysis-Prompt.md`** fresh every time (it evolves)
5. **Run full 9-dimension analysis** per the prompt
6. **Build CONNECTIONS section** at top of output:
   - Fathom Recording link
   - Notion Meeting Notes link
   - HubSpot Account (search ~~CRM companies, portal `22283601`, record type `0-2`)
   - HubSpot Contacts (search ~~CRM contacts, record type `0-1`)
   - HubSpot Deal (search ~~CRM deals, record type `0-3`)
7. **Save** to `Jobs To Be Done/[Folder]/Calls & Meetings/[Company]/[filename].md`

## File Naming

- Single participant: `[YYYY-MM-DD] - [First Last, Company] - JTBD Analysis.md`
- Multiple from same org: `[YYYY-MM-DD] - [Company] - JTBD Analysis.md`

## Company Folder Matching

- Fuzzy match at >=90% similarity (case-insensitive)
- Only create new folder if no match meets threshold
- Create `Calls & Meetings/` subfolder if it doesn't exist

## Analysis Rules

- Specific over generic
- Quote exact language from transcript
- Mark inferences with [INFERRED] or [IMPLIED]
- Flag contradictions (stated vs. observed)
- Intensity = importance
- Context matters (prospect vs. 90-day client)

## Execution Strategy

**Write files directly.** When performing analysis, write the output file directly to the target path. Do not generate content in memory and write it separately -- that forces regenerating thousands of tokens.

**If using a subagent**, pass the target file path in the prompt and instruct the subagent to write the file itself using the Write tool. The subagent has access to Write. Never have a subagent return content for the parent to re-write.

**Do not use task tracking** (TaskCreate/TaskUpdate) for this workflow. It adds overhead with no value.

## Multiple Transcripts

When given multiple transcript files in one invocation:
1. Process them **sequentially**, one at a time
2. Complete the FULL workflow (analyze, build connections, save) for each file before starting the next
3. Do NOT use task tracking or parallel processing
4. Share HubSpot lookups across files if they are for the same company (avoid redundant searches)

## Binary Transcript Files (.docx, .pdf)

If the user provides .docx files, convert them to text using `textutil -convert txt -stdout "<path>"` (macOS) before processing. For PDFs, use the Read tool with the `pages` parameter.

## Enrichment Mode

When asked to "update connections" on existing files:
1. Scan all `Calls & Meetings/` across all folders
2. Find files with missing or `[Add link]` connections
3. Run ~~CRM lookups and ~~knowledge base searches
4. Update only placeholder fields — never overwrite existing links
