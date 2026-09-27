# BR JARVIS — FINAL REMEDIATION TEST & VERIFICATION PLAN

## 1. Test Pyramid Strategy
Every identified root cause is paired with explicit automated tests across all 6 testing tiers:

1. **Unit Tests**: Parameter validation, contract envelopes, state machine transitions, math transforms.
2. **Integration Tests**: Tool dispatch, policy enforcement, gateway failover, database locking.
3. **E2E Tests**: Sandbox artifact export, visible browser navigation, voice command loop.
4. **Regression Tests**: `ERR_FILE_NOT_FOUND` prevention, DPI coordinate accuracy.
5. **Security Tests**: Path traversal denial, prompt injection detection, token isolation.
6. **Failure & Recovery Tests**: 429 rate limit recovery, broken tool fallback, malformed JSON recovery.

---

## 2. Test Mapping Matrix

| Root Cause ID | Target Unit Test | Target Integration Test | Target E2E / Regression Test |
| :--- | :--- | :--- | :--- |
| **RC-01 (Sandbox Export)** | `test_artifact_manager.py` | `test_export_tools.py` | `test_sandbox_artifact_lifecycle.py` |
| **RC-02 (Verification Truth)** | `test_task_state.py` | `test_action_verifier.py` | `test_master_task_lifecycle.py` |
| **RC-03 (DPI Scaling)** | `test_dpi_transform.py` | `test_vision_operator.py` | `test_screen_click_accuracy.py` |
| **RC-04 (Provider Failover)** | `test_circuit_breaker.py` | `test_smart_router.py` | `test_multi_backend_routing.py` |
| **RC-05 (Compound Intent)** | `test_stage_decomposer.py` | `test_intent_engine.py` | `test_task_dag_lifecycle.py` |
| **RC-06 (Database Lock)** | `test_sqlite_lock.py` | `test_canonical_db.py` | `test_concurrent_memory_writes.py` |
| **RC-07 (Acoustic Echo)** | `test_silero_vad.py` | `test_voice_barge_in.py` | `test_voice_dialogue_loop.py` |
