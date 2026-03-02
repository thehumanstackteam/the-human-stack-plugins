# JTBD Analysis Skill

Run Jobs-to-be-Done analysis on call transcripts using Tim Lockie's structured framework. This skill powers both the `jtbd-analysis` command and the standalone `jtbd-analysis` skill.

## Quick Reference

- **Analysis Prompt**: `Jobs To Be Done/Jobs 2B Done - Plugin & Skills/JTBD-Analysis-Prompt.md`
- **Synthesis Prompt**: `Jobs To Be Done/Jobs 2B Done - Plugin & Skills/JTBD-Synthesis-Prompt.md`
- **JTBD Analyses Notion DB**: ID `2f218faa725b41828194e8fc0f93453b`, data source `collection://fbf274fd-5cf0-4afe-9eaf-cb511cae6b94`
- **Database Schema**: Inline in `commands/jtbd-analysis.md` Step 6 (authoritative source for all valid property values)
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
   - Clay URL (if available)
7. **Save** to `Jobs To Be Done/[Folder]/Calls & Meetings/[Company]/[filename].md`
8. **Populate JTBD Analyses DB** — create a page in the Notion database (data source `collection://fbf274fd-5cf0-4afe-9eaf-cb511cae6b94`) with:
   - **Page body**: The COMPLETE analysis text, verbatim (never summarize or truncate)
   - **Properties**: Using exact valid values from command file Step 6b
   - **Meeting Transcript**: Two-way relation to source transcript (auto-creates back-link)

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

## Notion DB Population

After saving the .md file, always create a JTBD Analyses record. The database serves as the queryable, filterable index across all analyses. The .md file remains the authoritative full-text source.

**Use `notion-create-pages`** with:
```
parent: { data_source_id: "fbf274fd-5cf0-4afe-9eaf-cb511cae6b94" }
```

**CRITICAL -- Page body content comes first.** The complete, unmodified analysis text (the exact .md file content) MUST be pasted as the page body. Do NOT summarize, truncate, or paraphrase. Every section, every quote, every line -- verbatim.

**Property mapping**: See `commands/jtbd-analysis.md` Step 6b for the complete field-by-field mapping with exact valid values for every select/multi-select field.

**Meeting Transcript** is a two-way relation to the Meeting Transcripts DB (`collection://669e7e0b-dfe6-43c4-b4c3-d7b734e06ed5`). Setting this relation automatically creates a back-link visible on the transcript page under "JTBD Analyses".

**Multi-select values must match exactly** — only use values listed in Step 6b. Omit rather than guess or create unknown options.

## Enrichment Mode

When asked to "update connections" on existing files:
1. Scan all `Calls & Meetings/` across all folders
2. Find files with missing or `[Add link]` connections
3. Run ~~CRM lookups and ~~knowledge base searches
4. Update only placeholder fields — never overwrite existing links
5. Check if a corresponding JTBD Analyses DB record exists — if not, create one
