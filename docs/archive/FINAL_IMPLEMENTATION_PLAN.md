# BR JARVIS — FINAL MODERNIZATION IMPLEMENTATION PLAN

## 1. Master Phased Blueprint (Phases 1 - 17)

| Phase | Title | Key Files Affected | Old Behavior | New Modernized Behavior | Verification Test Commands | Risk & Rollback |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | **Process Baseline & Git Hygiene** | `.gitignore`, `workspace/` | Browser profile cache tracked in git | Browser profiles and WAL files excluded | `git status` clean | LOW (local cache recreates) |
| **02** | **Control Plane Consolidation** | `core/bootstrap.py`, `core/bootstrapper.py`, `start.py` | Duplicate bootstrapper classes | Unified `CoreBootstrapper` with thin `start.py` launcher | `pytest tests/unit/test_bootstrap.py` | LOW (re-export shim in place) |
| **03** | **Model Gateway & Routing** | `gateway/model_gateway.py`, `router/smart_router.py` | Direct ad-hoc backend calling | Unified gateway routing with multi-key rotation | `pytest tests/unit/test_model_gateway.py` | MEDIUM (fallback to local Ollama) |
| **04** | **Tools & Actions Unification** | `tools/registry.py`, `tools/reminder_tools.py`, `tools/system_tools.py` | Procedural scripts in `actions/` | Declarative tool schemas with 6-tuple validation | `pytest tests/unit/test_tool_suite_audit.py` | MEDIUM (re-register tools) |
| **05** | **Verification Semantics** | `agent/verifier.py`, `agent/executor.py` | Success returned on return code 0 | Physical post-condition checked before `success=True` | `pytest tests/unit/test_sandboxed_process.py` | LOW (stricter checks) |
| **06** | **Artifacts & Safe Export** | `agent/artifacts.py`, `tools/export_tools.py` | Browser opened raw sandbox path (`ERR_FILE_NOT_FOUND`) | Explicit SHA256 export to host directory before open | `pytest tests/e2e/test_sandbox_artifact_lifecycle.py` | LOW (fallback to host copy) |
| **07** | **Memory & Storage Unification**| `memory/canonical_db.py`, `memory/unified_memory.py` | 8 fragmented `.db`/`.json` stores | Single `.jarvis/jarvis_core.db` in SQLite WAL mode | `pytest tests/unit/test_sqlite_lock.py` | HIGH (SQLite auto-backup) |
| **08** | **Voice Multimodal Polish** | `voice/assistant.py`, `voice/silero_vad.py` | Separate voice audio loops | Sub-300ms Silero VAD + Faster-Whisper + Edge TTS | `pytest tests/unit/test_voice_latency.py` | MEDIUM (pure Python VAD fallback) |
| **09** | **Vision Perception Optimization**| `vision/engine.py`, `vision/screen_analyst.py` | Standalone optical guessers | Hierarchical router (A11y → CDP → OCR → VLM) | `pytest tests/unit/test_semantic_vision.py` | LOW (OCR fallback) |
| **10** | **Workflows & DAG Engine** | `workflow/task_dag.py`, `agent/stage_decomposer.py` | Linear unrecoverable step loops | Parallel DAG execution with Kahn's topological sort | `pytest tests/unit/test_parallel_dag_executor.py` | MEDIUM (retry node) |
| **11** | **Security & Policy Hardening** | `security/policy_engine.py`, `security/path_policy.py` | Ad-hoc regex path checking | Deterministic 6-tuple policy with critical denylist | `pytest tests/unit/test_path_security_hardening.py` | HIGH (raise SecurityViolationError) |
| **12** | **UI & Dashboard Modernization**| `ui/main_window.py`, `dashboard/server.py` | Monolithic UI class & separate HTTP server | Modular UI controllers & FastAPI dashboard route | `pytest tests/unit/test_server_web.py` | MEDIUM (Qt signal bridge) |
| **13** | **Test Suite Hardening** | `tests/unit/*`, `tests/e2e/*` | Mock-heavy return code assertions | Assertions verify physical filesystem and OS state | `pytest tests/` (100% pass) | LOW (update test fixtures) |
| **14** | **Performance & Startup Tuning**| `core/intent_engine.py`, `skills/loader.py` | 1,811-line monolithic regex tables | Declarative config rules & SQLite skills cache | Startup cold boot < 800ms | LOW (fallback to full scan) |
| **15** | **Repository Cleanup** | `workspace/`, `docs/forensic/` | Temporary notes & obsolete logs | Clean git working tree, zero orphaned files | `git status` clean | LOW (git history preserved) |
| **16** | **Documentation Harmonization** | `readme.md`, `DEVELOPER_WALKTHROUGH.md` | Outdated MK37/MK38 instructions | Unified MK40.2 developer guides | Documentation validation | LOW (markdown update) |
| **17** | **Final Release Certification** | `config/release_manifest.json`, `scripts/smoke_startup.py` | Uncertified manual checks | Automated 12/12 smoke tests & SHA256 ledger | `python scripts/smoke_startup.py` | LOW (production ready) |
