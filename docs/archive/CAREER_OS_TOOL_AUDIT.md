# BR JARVIS MK40.2+ — Career OS Tool Registry & Schema Audit

## Registered Tool Inventory (`career/tools.py` & `tools/registry.py`)

| Tool Name | Capability / Description | Safety Policy |
| :--- | :--- | :--- |
| `career_email_process` | Ingest and classify incoming recruitment email | `ALWAYS_ALLOWED_SAFE` / Audit |
| `career_offer_confirm` | Explicitly approve and confirm detected offer terms | `DESTRUCTIVE_TOOLS` (Requires Approval) |
| `career_spreadsheet_sync` | Synchronize canonical database to 10-sheet Excel tracker | `DESTRUCTIVE_TOOLS` (File Write) |
| `career_followup_generate_draft` | Generate non-sending DRAFT_ONLY follow-up message | `DESTRUCTIVE_TOOLS` (Draft Write) |
| `career_learning_insights` | Extract and analyze career learning insights | `ALWAYS_ALLOWED_SAFE` |
| `career_profile_get` | Retrieve active candidate profile and completeness score | `ALWAYS_ALLOWED_SAFE` |
| `career_profile_update` | Update candidate skills, experience, or preferences | `ALWAYS_ALLOWED_SAFE` |
| `career_job_search` | Search live postings across Greenhouse, Lever, Ashby | `ALWAYS_ALLOWED_SAFE` |
| `career_job_match` | Score and rank candidate fit against job description | `ALWAYS_ALLOWED_SAFE` |
| `career_resume_build` | Render tailored resume across 10 typography templates | `ALWAYS_ALLOWED_SAFE` |
| `career_resume_tailor` | Tailor resume bullets and generate diff against job spec | `ALWAYS_ALLOWED_SAFE` |
| `career_resume_export` | Export resume to DOCX, PDF, and HTML formats | `ALWAYS_ALLOWED_SAFE` |
| `career_ats_evaluate` | Run 7-factor deterministic ATS compliance scoring | `ALWAYS_ALLOWED_SAFE` |
| `career_cover_letter_generate` | Generate tailored cover letter in text and PDF | `ALWAYS_ALLOWED_SAFE` |
| `career_application_prepare` | Generate application package and open job portal | `ALWAYS_ALLOWED_SAFE` |
| `career_application_submit` | Verify and record application submission | `DESTRUCTIVE_TOOLS` (External Action) |
| `career_application_verify` | Verify physical application artifacts and receipts | `ALWAYS_ALLOWED_SAFE` |
| `career_application_track` | Update application status in deterministic state machine | `ALWAYS_ALLOWED_SAFE` |
| `career_interview_prep` | Generate customized technical interview prep kit | `ALWAYS_ALLOWED_SAFE` |
| `career_analytics_report` | Calculate career funnel conversion and telemetry metrics | `ALWAYS_ALLOWED_SAFE` |
