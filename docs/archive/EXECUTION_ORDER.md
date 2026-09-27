# BR JARVIS — PHASED EXECUTION ORDER

## 1. Zero-Breaking Execution Protocol
The rebuild follows a strict dependency order ensuring the system remains executable and testable at every single step.

```text
Phase 1: Security & Git Cleanup
  ↓
Phase 2: Bootstrapper & Core Lifecycle Consolidation
  ↓
Phase 3: Model Gateway & Provider Adapter Standardization
  ↓
Phase 4: Tool & Action Unification
  ↓
Phase 5: Memory Database Consolidation
  ↓
Phase 6: Voice & Multimodal Pipeline Polish
  ↓
Phase 7: Comprehensive Test Verification & Release
```

---

## 2. Step-by-Step Execution Sequence

### Phase 1: Security & Git Cleanup
- Update `.gitignore` to exclude `workspace/browser_user_data/`, `*.db-wal`, `*.db-shm`.
- Verify `security/path_policy.py` blocks access to sensitive system paths.

### Phase 2: Bootstrapper & Core Lifecycle Consolidation
- Consolidate `core/bootstrapper.py` and `core/sanitizer.py` into `core/bootstrap.py` and `security/sanitizer.py`.
- Refactor `start.py` to delegate initialization to `core/bootstrap.py::build_assistant_runtime()`.

### Phase 3: Model Gateway & Provider Adapter Standardization
- Route all LLM requests through `gateway/model_gateway.py`.
- Standardize multi-key rotation across all backend adapters.

### Phase 4: Tool & Action Unification
- Migrate legacy procedural `actions/` into standard tools in `tools/` and connectors in `connectors/`.
- Replace `tools/legacy_actions_tools.py` with direct tool schemas.

### Phase 5: Memory Database Consolidation
- Consolidate application usage, calendar, and reflection tables into `.jarvis/jarvis_core.db`.
- Standardize on `memory/sqlite_lock.py` for thread-safe asynchronous writes.

### Phase 6: Voice & Multimodal Polish
- Ensure Silero VAD v5 + Faster-Whisper + Edge TTS pipeline maintains < 300ms latency.
- Validate barge-in cancellation and audio device switching.

### Phase 7: Full Test Suite Validation
- Execute `pytest tests/` across all 116 test files.
- Run `python scripts/smoke_startup.py` and `python scripts/test_toughest_tasks.py`.
