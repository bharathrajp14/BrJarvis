# BR JARVIS MK40.2+ — Canonical Database & Schema Audit

## Canonical Database Architecture
- **Location**: `.jarvis/jarvis_canonical.db`
- **Engine**: SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`)
- **Concurrency**: Thread-safe with busy timeouts (30.0s) and recursive locking.
- **Relational Tables**:
  1. `career_applications_v2` (32 canonical fields, composite indexing on `job_id`, `company`, `status`, `updated_at`).
  2. `career_application_events` (Immutable append-only audit event log).
  3. `career_interviews` (Round, timestamps, timezone, meeting links, interviewers).
  4. `career_offers` (Candidate terms, compensation, conditions, status, expiry date).
  5. `career_followups` (Milestone due dates, status, drafted messages).
  6. `career_email_records` (Idempotent audit records for all parsed recruitment emails).
  7. `career_contacts` (Recruiters, hiring managers, sourcers).

## Schema Validation
- All tables execute with strict foreign key constraints and `ON DELETE CASCADE` where applicable.
- Integrity check passes with `PRAGMA integrity_check` returning `"ok"`.
