# BR JARVIS — MASTER MODERNIZATION & ARCHITECTURAL REBUILD PLAN (17 PHASES)

## 1. Strategy & Zero-Breaking Principle
The modernization plan is partitioned into **17 sequential phases**. Each phase is atomic, independently verifiable via automated pytest suites, and preserves full runtime backward compatibility.

---

## 2. Phase-by-Phase Implementation Specifications

### Phase 1: Correctness & Process Baseline
- **Goal**: Lock repository snapshot, verify zero unmonitored file mutations.
- **Files**: `docs/forensic/CURRENT_STATE_SNAPSHOT.md`, `.gitignore`.
- **Verification**: `git status` clean, all 2,070 files verified in `01_FILE_INVENTORY.md`.

### Phase 2: Architecture & Control Plane Consolidation
- **Goal**: Unify bootstrapper into `core/bootstrap.py`; make `start.py` thin launcher.
- **Files**: `core/bootstrap.py`, `core/bootstrapper.py`, `core/runtime.py`, `start.py`.
- **Verification**: `pytest tests/unit/test_bootstrap.py` & `python scripts/test_bootstrap.py`.

### Phase 3: Provider Gateway & Multi-Model Routing
- **Goal**: Unify all LLM calls through `gateway/model_gateway.py` with multi-key rotation and circuit breakers.
- **Files**: `gateway/model_gateway.py`, `router/smart_router.py`, `backends/gemini.py`, `backends/anthropic.py`.
- **Verification**: `pytest tests/unit/test_model_gateway.py tests/unit/test_smart_model_router.py`.

### Phase 4: Tools & Actions System Consolidation
- **Goal**: Migrate procedural `actions/` routines into declarative tools in `tools/` and connectors in `connectors/`.
- **Files**: `tools/reminder_tools.py`, `tools/system_tools.py`, `tools/browser_tools.py`, `tools/registry.py`.
- **Verification**: `pytest tests/unit/test_tool_runtime.py tests/unit/test_tool_suite_audit.py`.

### Phase 5: Verification & Post-Condition Semantics
- **Goal**: Guarantee every tool execution verifies physical state before returning `success=True`.
- **Files**: `agent/verifier.py`, `agent/executor.py`, `tools/sandbox_process.py`.
- **Verification**: `pytest tests/unit/test_sandboxed_process.py tests/unit/test_regression_fixes.py`.

### Phase 6: Artifacts, Sandbox & Browser Host Export
- **Goal**: Enforce `sandbox_path != host_path` with automatic SHA256 export to prevent browser `ERR_FILE_NOT_FOUND`.
- **Files**: `agent/artifacts.py`, `tools/export_tools.py`, `core/workspace_engine.py`.
- **Verification**: `pytest tests/unit/test_artifact_manager.py tests/e2e/test_sandbox_artifact_lifecycle.py`.

### Phase 7: Memory & Database Store Unification
- **Goal**: Consolidate 8 fragmented databases into `.jarvis/jarvis_core.db` operating in SQLite WAL mode.
- **Files**: `memory/canonical_db.py`, `memory/unified_memory.py`, `memory/sqlite_lock.py`.
- **Verification**: `pytest tests/unit/test_sqlite_lock.py tests/unit/test_relationship_resolution.py`.

### Phase 8: Voice & Audio Multimodal Pipeline
- **Goal**: Polish full-duplex voice loop: Silero VAD v5 + Faster-Whisper + Edge TTS with priority queue and barge-in.
- **Files**: `voice/assistant.py`, `voice/silero_vad.py`, `voice/tts_queue.py`, `voice/tts.py`.
- **Verification**: `pytest tests/unit/test_voice_latency.py tests/unit/test_voice_pipeline.py`.

### Phase 9: Vision & Screen Automation
- **Goal**: Optimize DXGI screen capture, Win32 UIAutomation accessibility tree, and Windows OCR.
- **Files**: `vision/screen_analyst.py`, `vision/hybrid_pipeline.py`, `vision/accessibility.py`, `computer/operator.py`.
- **Verification**: `pytest tests/unit/test_semantic_vision.py tests/unit/test_vision_engine.py`.

### Phase 10: Workflows & DAG Scheduling
- **Goal**: Verify Kahn's topological sort and asynchronous parallel step execution.
- **Files**: `workflow/task_dag.py`, `agent/stage_decomposer.py`, `agent/task_scheduler.py`.
- **Verification**: `pytest tests/unit/test_parallel_dag_executor.py tests/unit/test_stage_decomposer.py`.

### Phase 11: Security & Threat Model Enforcement
- **Goal**: Enforce 6-tuple policy evaluation and path security tiers across all tool proposals.
- **Files**: `security/policy_engine.py`, `security/path_policy.py`, `guardian/prompt_injection_shield.py`.
- **Verification**: `pytest tests/unit/test_path_security_hardening.py tests/unit/test_prompt_injection_shield.py`.

### Phase 12: User Interface & Dashboard Modernization
- **Goal**: Modularize `ui/main_window.py` and mount web dashboard onto FastAPI `api/routes/`.
- **Files**: `ui/main_window.py`, `ui/widgets.py`, `dashboard/server.py`, `server.py`.
- **Verification**: `pytest tests/unit/test_ui_mark.py tests/unit/test_server_web.py`.

### Phase 13: Testing Suite Hardening & Mock Sanitization
- **Goal**: Expand assertion strength across all 116 test files to verify physical postconditions.
- **Files**: `tests/unit/*`, `tests/integration/*`, `tests/e2e/*`.
- **Verification**: `pytest tests/` (100% pass across all 420 test functions).

### Phase 14: Performance & Startup Optimization
- **Goal**: Split monolithic regex tables in `core/intent_engine.py`; lazy load non-critical skills.
- **Files**: `core/intent_engine.py`, `skills/loader.py`.
- **Verification**: Cold boot startup time < 800ms.

### Phase 15: Repository Cleanup & Legacy Deletion
- **Goal**: Remove dead code files, empty directories, and obsolete temporary artifacts.
- **Files**: `workspace/*.md`, `docs/forensic/` archive management.
- **Verification**: `git status` clean, zero orphaned references.

### Phase 16: Documentation Harmonization
- **Goal**: Update README, developer walkthroughs, and architecture blueprints to reflect unified MK40.2 runtime.
- **Files**: `readme.md`, `DEVELOPER_WALKTHROUGH.md`, `PROJECT_SUMMARY.md`.
- **Verification**: All commands and code paths in documentation tested and functional.

### Phase 17: Final Production Certification & Release
- **Goal**: Full-stack E2E verification, soak testing, and release manifest generation.
- **Files**: `config/release_manifest.json`, `scripts/smoke_startup.py`, `scripts/test_toughest_tasks.py`.
- **Verification**: All 12/12 smoke tests pass; E2E multi-step tasks verified.
