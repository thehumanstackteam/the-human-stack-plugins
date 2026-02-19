# Connectors

## Required

| Connector | Tools Used | Purpose |
|-----------|-----------|---------|
| **Notion** | `notion-fetch`, `notion-search` | Read coaching data (transcripts, call pages) from the Coaching DB. |
| **Notion Writer** | `update-page-properties` | Push approved Essentials fields to the Essentials Endpoint Map database. Only used by Stage 3 after Tim approves. |

## Setup

When you install this plugin, Cowork will prompt you to connect Notion if it's not already connected. Authorize with a Notion account that has access to the Project Evident Coaching workspace. The Notion Writer MCP is provided automatically with the Notion connection.

## Notes

- Both Notion and Notion Writer MCPs are provided by the single Notion connector
- No API tokens or environment variables needed
- Stage 1 and Stage 2 only READ from Notion — all writes go to the local filesystem
- Stage 3 writes to Notion autonomously. Tim vetoes after via Notion comments
