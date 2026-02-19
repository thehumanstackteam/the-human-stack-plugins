# Essential Document Quality Gate (Simon's Criteria)

The Essentials document must contain enough specificity to produce a single
summary sentence. If it can't, the document isn't ready.

## The 7 Essential Elements

| # | Element | Specificity Test | Bad Example | Good Example |
|---|---------|-----------------|-------------|--------------|
| 1 | AI Tech Used | Named tool with capability | "AI tools" | "JotForm with AI automation and video upload" |
| 2 | Personnel Involved | Named people with roles | "staff" | "Maria Rodriguez (intake coord), Josh Chen (ED)" |
| 3 | Data Involved | What data, what format | "their data" | "client intake forms, therapist availability calendars" |
| 4 | Pre-AI Workflow | Steps and activities defined | "it was slow" | "10-step manual intake: phone screening, paper form, staff-matched therapist assignment" |
| 5 | Post-AI Workflow | Steps and activities defined | "it's automated" | "3-step: client submits JotForm with video, AI routes to matched therapist, auto-confirms via SMS" |
| 6 | Quantitative Impact | Numbers (hours, dollars, %) | "saves time" | "4 hrs/week → 30 min/week for 10-20 intakes" |
| 7 | Qualitative Impact | Service, satisfaction, capacity | "it's better" | "clients choose clinicians, reach more people, receive services sooner" |

## Where Elements Live in the Endpoints

| Element | Primary Fields | Secondary Fields |
|---------|---------------|-----------------|
| AI Tech | C1P2 (#03), C3P1T1F2 (#07) | C3P1T3F2 (#15) |
| Personnel | C3P1T1F3 (#08), C3P1T2F3 (#12), C3P1T3F3 (#16), C3P2T1F3 (#20), C3P3T1F3 (#24) | — |
| Data | C3P1T2F2 (#11) | C3P1T2F4 (#13) |
| Pre-AI Workflow | C4P1F1 (#26) | C1P1T1 (#01), C1P1T2 (#02) |
| Post-AI Workflow | C4P1F2 (#27) | C3P2T1F2 (#19), C3P3T1F2 (#23) |
| Quantitative Impact | C4P2T1F3 (#30), C4P2T2F3 (#33) | C3 Progress Indicator fields (#09,13,17,21,25) |
| Qualitative Impact | C4P2T4F2 (#38), C4P2T5F2 (#41) | Coaching Notes (#49), Aha Moments (#50) |

## The Summary Sentence Template

When all 7 elements pass specificity:

> "The organization is using **[AI Tech]** with **[Personnel]** for
> **[Data/Process]** to solve **[Pre-AI Workflow problem]**, achieving
> **[Post-AI Workflow improvement]**, **[Quantitative Impact]**,
> and **[Qualitative Impact]**."

## Validation Statuses

| Status | Meaning |
|--------|---------|
| ✓ Specific | Element present with enough detail to fill the template slot |
| ⚠ Vague | Element present but too generic — needs detail |
| ✗ Missing | Element not found in populated fields |

Ready = all 7 are ✓. Needs work = any ⚠ or ✗.

## Recommendation for Simon: Evidence Fields

The current database has paired Description/Evidence fields for each C4 benefit
category (e.g., C4P2T1F2 + C4P2T1F3). In practice these tend to repeat each other.

**Current design:** Description and Evidence serve distinct purposes when written
correctly. Description = the narrative of what changed. Evidence = the specific
measurements, observations, and actions that prove it. They should never say
the same thing.

**Future consideration:** If the team finds that even with clear guidance the
fields still duplicate, collapsing to a single rich Description field per benefit
category would simplify the database without losing information — as long as
the Description includes the verifiable specifics that Simon's criteria require.
