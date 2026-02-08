# Jobs 2B Done

JTBD (Jobs to be Done) call transcript analysis plugin for The Human Stack. Analyzes sales, coaching, and industry calls through a structured framework, enriches with CRM and knowledge base connections, and saves to organized folders.

## Commands

### `jtbd-analysis`
Run JTBD analysis on a single call transcript. Accepts pasted text, a conversation intelligence URL, or a Notion meeting transcript. Outputs a structured analysis with a CONNECTIONS section linking to HubSpot and Notion records. Saves to a company folder under the appropriate top-level folder in `Jobs To Be Done/`.

### `jtbd-synthesis`
Synthesize patterns across multiple JTBD analyses. Scopes to all calls, a single folder, a single company, a date range, or engagement stage. Cross-references established findings, validates archetypes, and tracks evidence levels (N=1 hypothesis, N=2 pattern, N=3+ finding).

## Connectors

| Connector | Purpose |
|-----------|---------|
| HubSpot | Company, contact, and deal lookups for CONNECTIONS section |
| Notion | Meeting transcript retrieval and page linking |
| Fireflies | Call transcript retrieval |

## Workspace

Analyses live in `Jobs To Be Done/` organized by top-level folders, each with `Calls & Meetings/[Company]/` and `Synthesis/` subfolders. The prompts and templates live in `Jobs 2B Done - Plugin & Skills/`.
