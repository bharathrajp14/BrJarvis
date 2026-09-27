# BR JARVIS — SYSTEM-WIDE INTEGRATION FAILURE MATRIX

## 1. Comprehensive Subsystem Failure Analysis

| Subsystem | Integration Boundary | Real-World Scenario | Expected State | Actual State | First Broken Layer | Severity | Recommended Fix |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Browser / Web** | Tool -> Host OS Browser | "Open report in browser" | Visible browser displays rendered HTML | `ERR_FILE_NOT_FOUND` displayed | Artifact Export | **HIGH** | Enforce `ensure_host_artifact()` before opening browser |
| **Vision / OS** | OCR / Graph -> OS Operator | "Click UI button" | Mouse cursor clicks exact element center | Click offset due to 125%/150% Windows DPI scaling | Coordinate Mapping | **HIGH** | Apply `GetDpiForWindow` scaling matrix to physical coordinates |
| **Orchestrator** | Tool Execution -> Verification | "Write and verify file" | State verified on disk before reporting success | Success returned immediately on function exit | Verification Layer | **HIGH** | Block `success=True` until `ActionVerifier` passes |
| **Voice / Audio** | TTS Queue -> Microphone VAD | Barge-in interruption | JARVIS stops speaking when user talks | Speaker echo triggers false user prompt | Acoustic Isolation | **MEDIUM** | Drain mic ring buffer and mute VAD during TTS playback |
| **Gateway / Router** | Provider Adapter -> Router | API Rate limit (429) | Automatic silent failover to secondary cloud/local model | Task fails with "All backends failed" | Fallback Router | **HIGH** | Implement automatic provider circuit breaker and fallback chain |
| **Intent Engine** | Voice Input -> Router | Compound multi-intent | Decomposed into multi-step DAG | Single intent executed, remainder dropped | Stage Decomposer | **MEDIUM** | Route multi-action queries through `StageDecomposer` |
| **Memory Store** | SQLite -> Multi-Agent | Concurrent background writes | All records persisted with busy retry | Database locked exception | Concurrency Lock | **HIGH** | Route 100% of SQLite writes through `sqlite_lock.py` |
| **Security Policy** | Model Proposal -> Execution | Path traversal attempt (`../../`) | Normalized canonical path checked against denylist | Ad-hoc regex missed Unicode/URL-encoded traversal | Path Normalization | **CRITICAL** | Enforce `PathSecurityPolicy.canonicalize()` before policy evaluation |
