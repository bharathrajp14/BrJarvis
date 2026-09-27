# BR JARVIS MK40.2+ — Career OS File Audit & Inventory

Complete forensic inventory of all source files, schemas, and configurations participating in the Personal Career Operating System.

## 1. Directory Structure

```
career/
├── __init__.py                                 # Top-level career package exports
├── models.py                                   # Authoritative 32-field canonical domain models & 24 deterministic states
├── profile_manager.py                          # Profile storage, completeness scoring & onboarding
├── interview_prep.py                           # Automated interview prep kit generator
├── analytics.py                                # Career funnel telemetry & conversion engine
├── notifications.py                            # Priority alert dispatcher
├── memory_integration.py                       # UnifiedMemory synchronization & learning
├── tools.py                                    # Dynamic tool registry bridge
├── api_routes.py                               # Complete FastAPI router for Career Studio
├── ats_engine/
│   ├── __init__.py
│   └── scorer.py                               # 7-factor deterministic ATS scoring engine
├── resume_engine/
│   ├── __init__.py
│   ├── models.py                               # Resume schemas, sections, tokens
│   ├── templates.py                            # 10 premium typography & layout templates
│   ├── renderer.py                             # HTML/CSS renderer
│   ├── exporter.py                             # Verified multi-format exporter (DOCX, PDF, HTML)
│   ├── tailoring.py                            # Rule-based & LLM resume tailoring with diffs
│   └── version_manager.py                      # Version tracking and artifact linkage
├── cover_letter/
│   ├── __init__.py
│   └── generator.py                            # Tailored cover letter & PDF generator
├── canva/
│   ├── __init__.py
│   ├── capability.py                           # Capability probe & runtime detection
│   ├── auth.py                                 # OAuth 2.0 PKCE flow manager
│   └── adapter.py                              # Canva Connect API adapter with native fallback
├── job_engine/
│   ├── __init__.py
│   ├── models.py                               # Canonical JobPosting & MatchScore models
│   ├── deduplicator.py                         # URL/hash/title deduplicator
│   ├── matcher.py                              # 10-factor multi-signal matcher
│   ├── ranker.py                               # Job ranking engine
│   ├── finder.py                               # Search orchestrator
│   └── adapters/
│       ├── __init__.py
│       ├── base.py                             # Base adapter interface
│       ├── greenhouse.py                       # Greenhouse API adapter
│       ├── lever.py                            # Lever API adapter
│       ├── ashby.py                            # Ashby API adapter
│       ├── company_site.py                     # Generic structured job scraper
│       └── generic_browser.py                  # Playwright fallback adapter
├── application_engine/
│   ├── __init__.py
│   ├── questions.py                            # Screening question classifier & sensitive guard
│   ├── package_builder.py                      # ApplicationPackage builder
│   ├── policy.py                               # Platform automation policy engine
│   ├── assistant.py                            # Manual application assistant
│   ├── duplicate_guard.py                      # Cooldown & duplicate application guard
│   ├── tracker.py                              # Legacy tracking bridge
│   └── verifier.py                             # Physical artifact & submission verifier
├── crm/
│   ├── __init__.py
│   ├── database.py                             # Canonical SQLite WAL database & CRUD
│   ├── state_machine.py                        # 24-state deterministic state machine
│   ├── event_pipeline.py                       # 11-stage event ingestion bus
│   └── followup_engine.py                      # Milestone follow-up scheduler & DRAFT_ONLY generator
├── email_intelligence/
│   ├── __init__.py
│   ├── injection_guard.py                      # Security shield against adversarial prompt injections
│   ├── classifier.py                           # 16-category recruiter email classifier
│   ├── matcher.py                              # Multi-factor fuzzy application matcher
│   ├── offer_detector.py                       # Conservative staged offer detector
│   ├── interview_detector.py                   # Date, time, timezone parser & link extractor
│   ├── rejection_detector.py                   # Rejection discriminator
│   └── service.py                              # Idempotent email processing service
├── calendar_engine/
│   ├── __init__.py
│   └── manager.py                              # Calendar conflict checker & prep kit linker
└── spreadsheet/
    ├── __init__.py
    ├── tracker_excel.py                        # 10-sheet openpyxl workbook generator
    └── projection.py                           # Concurrency-safe atomic Excel projection engine
```

## 2. File Verification & Health Ledger

All 45+ Career OS files are present, verified, tested, and actively utilized by the runtime.
