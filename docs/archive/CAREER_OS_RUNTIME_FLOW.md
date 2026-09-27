# BR JARVIS MK40.2+ — Career OS Runtime Flow & Pipeline

Comprehensive execution flow from incoming event signals to persistence, Excel projection, and UI notifications.

## 1. 11-Stage Single Event Bus Pipeline

```
┌─────────────────┐
│  EVENT SOURCE   │ (Gmail, Outlook, Calendar, Job Portals, User Actions, CLI, Voice)
└────────┬────────┘
         ▼
┌─────────────────┐
│ 1. NORMALIZER   │ Normalize text encoding, dates to ISO 8601, clean HTML/whitespace
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. VALIDATOR    │ Validate required payload fields, timestamps, and data types
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. DEDUPLICATOR │ Compute composite hash (provider:id:timestamp) to reject replays
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. APP MATCHER  │ Multi-factor matching (company, role, IDs, domains). Review gate <0.70
└────────┬────────┘
         ▼
┌─────────────────┐
│ 5. STATE MACHINE│ Deterministic 24-state transition graph; blocks illegal state jumps
└────────┬────────┘
         ▼
┌─────────────────┐
│ 6. PERSISTENCE  │ Write to SQLite WAL (career_applications_v2, career_application_events)
└────────┬────────┘
         ▼
┌─────────────────┐
│ 7. EXCEL PROJ.  │ Concurrency-safe atomic projection to BR_JARVIS_Career_Tracker.xlsx
└────────┬────────┘
         ▼
┌─────────────────┐
│ 8. MEMORY SYNC  │ Persist verified outcomes & learning insights to UnifiedMemory
└────────┬────────┘
         ▼
┌─────────────────┐
│ 9. NOTIFICATION │ Emit prioritized alerts (CRITICAL, HIGH, MEDIUM, LOW) to Web/Voice
└────────┬────────┘
         ▼
┌─────────────────┐
│ 10. ANALYTICS   │ Recompute career funnel metrics, response rates, conversion ratios
└─────────────────┘
```

## 2. Security Invariants
- External text is strictly encapsulated in `<UNTRUSTED_EXTERNAL_CONTENT>`.
- Offer letters require explicit human confirmation (`OFFER_DETECTED` $\rightarrow$ `OFFER_CONFIRMED`).
- Applications require explicit human review before external submission (`READY_FOR_REVIEW` $\rightarrow$ `SUBMITTED`).
- Excel is a read projection; the Canonical Database is the single authoritative source of truth.
