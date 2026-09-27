# BR JARVIS MK40.2+ — Career OS Security & Zero-Fabrication Audit

## Security Controls Enforced

### 1. Fail-Closed Policy Engine (`security/policy_engine.py`)
- High-impact mutations (external portal submission, offer acceptance, calendar writes, spreadsheet overwrites) are classified under `DESTRUCTIVE_TOOLS` and require explicit confirmation unless `allow_all` is chosen.

### 2. Prompt Injection Defense (`career/email_intelligence/injection_guard.py`)
- All untrusted external inputs (emails, attachments, job postings, recruiter notes) are sanitized:
  - Backtick fence blocks are defanged (`'''`).
  - Script tags (`<script>...</script>`) are neutralized.
  - Text is wrapped in strict `<UNTRUSTED_EXTERNAL_CONTENT type="...">` blocks with security notice headers preventing prompt takeover.

### 3. Staged Conservative Offer Detection
- Offers are strictly detected as candidate facts (`OFFER_DETECTED`) and NEVER auto-confirmed.
- Transitions to `OFFER_CONFIRMED` strictly require explicit user approval.

### 4. Zero-Fabrication Action Verifier (`core/execution/verifier.py`)
- Code exists $\neq$ feature works.
- Only physical proof (filesystem check, HTTP code 200, valid checksum, PDF header bytes, DB row insertion) produces `SUCCESS_VERIFIED`.
