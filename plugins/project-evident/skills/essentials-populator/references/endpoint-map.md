# Essentials Endpoint Field Map

All 50 fields in the Essentials database. Property names must be used exactly
as shown — Notion requires the full name including the code prefix.

## Field Naming Convention

Pattern: **C[component]P[phase]T[task]F[field]**

## Component 1: AI Solution and Pain Point (3 fields)

| # | Exact Notion Property Name | Type |
|---|---------------------------|------|
| 01 | `C1P1T1: Pain Point` | text |
| 02 | `C1P1T2: Current Impact` | text |
| 03 | `C1P2: Reviewed AI Solutions and Tools` | text |

## Component 2: Policy/Guidelines (2 fields)

| # | Exact Notion Property Name | Type |
|---|---------------------------|------|
| 04 | `C2T1F1: Policy Document Link` | url |
| 05 | `C2T1F2: Policy Notes` | text |

## Component 3: Execution Checklist (20 fields)

### Phase 1: Foundation & Setup

| # | Exact Notion Property Name | Type |
|---|---------------------------|------|
| 06 | `C3P1T1F1: AI Tools Purchase Checked` | checkbox |
| 07 | `C3P1T1F2: Description of AI Tools Purchase` | text |
| 08 | `C3P1T1F3: Owner for AI Tools Purchase` | text |
| 09 | `C3P1T1F4: Progress Indicators for AI Tools Purchase` | text |
| 10 | `C3P1T2F1: Data Identified Checked` | checkbox |
| 11 | `C3P1T2F2: Description of Data Identified and Readiness` | text |
| 12 | `C3P1T2F3: Owner for Data Identification` | text |
| 13 | `C3P1T2F4: Progress Indicators for Data Readiness` | text |
| 14 | `C3P1T3F1: Technology Integration Complete Checked` | checkbox |
| 15 | `C3P1T3F2: Description of Technology Integration` | text |
| 16 | `C3P1T3F3: Owner for Technology Integration` | text |
| 17 | `C3P1T3F4: Progress Indicators for Technology Integration` | text |

### Phase 2: Testing & Training

| # | Exact Notion Property Name | Type |
|---|---------------------------|------|
| 18 | `C3P2T1F1: Small Scale Test Run Checked` | checkbox |
| 19 | `C3P2T1F2: Description of Small Scale Test` | text |
| 20 | `C3P2T1F3: Owner for Small Scale Test` | text |
| 21 | `C3P2T1F4: Progress Indicators for Small Scale Test` | text |

### Phase 3: Launch & Rollout

| # | Exact Notion Property Name | Type |
|---|---------------------------|------|
| 22 | `C3P3T1F1: Wider Rollout Checked` | checkbox |
| 23 | `C3P3T1F2: Description of Wider Rollout` | text |
| 24 | `C3P3T1F3: Owner for Wider Rollout` | text |
| 25 | `C3P3T1F4: Progress Indicators for Wider Rollout` | text |

## Component 4: Progress Monitoring (25 fields)

### Before/After

| # | Exact Notion Property Name | Type |
|---|---------------------------|------|
| 26 | `C4P1F1: Before AI` | text |
| 27 | `C4P1F2: After AI` | text |

### Benefit Categories

| # | Exact Notion Property Name | Type |
|---|---------------------------|------|
| 28 | `C4P2T1F1: Cost Savings Checked` | checkbox |
| 29 | `C4P2T1F2: Description of Cost Savings` | text |
| 30 | `C4P2T1F3: Evidence of Cost Savings` | text |
| 31 | `C4P2T2F1: Productivity Gains Checked` | checkbox |
| 32 | `C4P2T2F2: Description of Productivity Gains` | text |
| 33 | `C4P2T2F3: Evidence of Productivity Gains` | text |
| 34 | `C4P2T3F1: Policy Changes Checked` | checkbox |
| 35 | `C4P2T3F2: Description of Policy Changes` | text |
| 36 | `C4P2T3F3: Evidence of Policy Changes` | text |
| 37 | `C4P2T4F1: Service Delivery Improvements Checked` | checkbox |
| 38 | `C4P2T4F2: Description of Service Delivery Improvements` | text |
| 39 | `C4P2T4F3: Evidence of Service Delivery Improvements` | text |
| 40 | `C4P2T5F1: Outcomes Improved Checked` | checkbox |
| 41 | `C4P2T5F2: Description of Outcomes Improved` | text |
| 42 | `C4P2T5F3: Evidence of Outcomes Improved` | text |
| 43 | `C4P2T6F1: Increased Funding Checked` | checkbox |
| 44 | `C4P2T6F2: Description of Increased Funding` | text |
| 45 | `C4P2T6F3: Evidence of Increased Funding` | text |
| 46 | `C4P2T7F1: Other Changes Checked` | checkbox |
| 47 | `C4P2T7F2: Description of Other Changes` | text |
| 48 | `C4P2T7F3: Evidence of Other Changes` | text |

### Narrative Fields

| # | Exact Notion Property Name | Type |
|---|---------------------------|------|
| 49 | `Coaching Notes` | text |
| 50 | `Aha Moments` | text |

## Checkbox Values

- `__YES__` = checked
- `__NO__` = unchecked

## Value Calculation Reference

| Role | Fully Loaded Rate |
|------|------------------|
| Staff | $65/hour |
| Executive Director | $100/hour |
| Consultant (external) | $200/hour |

Only calculate meaningful savings. Symbolic improvements = values-alignment, not financial.
