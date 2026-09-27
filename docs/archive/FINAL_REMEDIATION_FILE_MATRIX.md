# BR JARVIS — FINAL REMEDIATION FILE-LEVEL IMPLEMENTATION MATRIX

| File Path | Current Problem | Root Cause | Target Change | Callers | Tests Required | Risk | Phase |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| `agent/artifacts.py` | Sandbox virtual path passed to host browser. | Missing mandatory host export before URL launch. | Add `ensure_host_artifact()` with SHA256 validation. | `tools/export_tools.py`, `tools/browser_automation.py` | `test_artifact_manager.py` | LOW | Phase 9 |
| `agent/task_state.py` | Illegal state jump from EXECUTED to COMPLETED. | State machine lacked verification enforcement guard. | Block `COMPLETED` state unless `verified=True`. | `orchestrator/core.py`, `agent/executor.py` | `test_master_task_lifecycle.py` | LOW | Phase 2 |
| `computer/operator.py`| Mouse click offset on scaled Windows monitors. | Coordinates not scaled by display DPI factor. | Apply `GetDpiForWindow` transform to physical pixels. | `vision/engine.py`, `agent/executor.py` | `test_vision_operator.py` | LOW | Phase 7 |
| `gateway/model_gateway.py`| Quota error 429 collapses task immediately. | Gateway raises exception without triggering fallback. | Add automatic fallback failover to secondary provider. | `router/smart_router.py`, `orchestrator/core.py` | `test_multi_backend_routing.py` | LOW | Phase 3 |
| `tools/tool_runtime.py`| Raw string error serialization. | Absence of standardized result contract. | Enforce strongly-typed `ToolResult` envelope. | All tool callers, `tools/registry.py` | `test_tool_runtime.py` | LOW | Phase 1 |
| `memory/canonical_db.py`| Concurrent writes trigger database locked errors. | Direct SQLite connection without mutex lock. | Route all writes through `sqlite_lock.py`. | `memory/unified_memory.py`, `agent/history.py` | `test_sqlite_locking.py` | LOW | Phase 6 |
| `voice/assistant.py` | Assistant hears its own TTS speech output. | Mic buffer active during audio playback. | Drain mic buffer and mute VAD during TTS playback. | `voice/tts_queue.py`, UI voice listener | `test_voice_pipeline.py` | LOW | Phase 8 |
