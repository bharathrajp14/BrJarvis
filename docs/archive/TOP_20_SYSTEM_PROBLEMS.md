# BR JARVIS — TOP 20 SYSTEM-LEVEL PROBLEMS & REMEDIATIONS

## 1. Problem Ranking Ledger

| Rank | Problem Title | Severity | Impacted Workflows | Architectural Leverage | Risk | Primary Fix |
| :---: | :--- | :---: | :--- | :---: | :---: | :--- |
| **1** | **Unverified Success Synthesis** | **CRITICAL** | All Agent & Tool Workflows | **MAXIMUM** | LOW | Require `ActionVerifier` pass before `status=COMPLETED`. |
| **2** | **Sandbox Path Host Conflation** | **CRITICAL** | Artifacts, Browser, Report Export | **HIGH** | LOW | Mandatory `ensure_host_artifact()` SHA256 export. |
| **3** | **Unscaled Display DPI Coordinates** | **HIGH** | UI Automation, Screen Click, Vision | **HIGH** | LOW | Inject `GetDpiForWindow` coordinate scaling transform. |
| **4** | **Unprotected Cloud Quota Failover** | **HIGH** | LLM Reasoning, Planning, Coding | **HIGH** | LOW | Dynamic mid-flight circuit-breaker failover to secondary model. |
| **5** | **Compound Intent Dropping in Voice** | **HIGH** | Voice Dialogue, Multi-action Tasks | **HIGH** | LOW | Route multi-clause queries through `StageDecomposer`. |
| **6** | **Concurrent SQLite Lock Contention** | **HIGH** | Multi-Agent, Memory, Experience | **HIGH** | LOW | Serialize 100% of SQLite writes through `sqlite_lock.py`. |
| **7** | **Acoustic Self-Echo Feedback** | **MEDIUM** | Hands-Free Voice Dialogue | **MEDIUM** | LOW | Drain microphone buffer during active TTS synthesis. |
| **8** | **Background vs Visible Browser Confusion**| **MEDIUM**| Web Search, Browser Interaction | **MEDIUM**| LOW | Explicit separation of `web_search` and `browser_navigate`. |
| **9** | **Untyped String Error Serialization**| **MEDIUM** | Diagnostics, Telemetry, Recovery | **MEDIUM** | LOW | Enforce structured `TaskExecutionDiagnostic` envelope. |
| **10** | **Path Traversal via Reparse Points** | **HIGH** | File Security, Sandbox Isolation | **HIGH** | LOW | Enforce `PathSecurityPolicy.canonicalize()` on all paths. |
| **11** | **Bypassed Vector Context Injection** | **MEDIUM** | Project Memory, Context Recall | **MEDIUM** | LOW | Inject hybrid search (Vector + BM25) into model context. |
| **12** | **Unbounded Process Execution** | **HIGH** | CLI Controller, Sandbox Process | **MEDIUM** | LOW | Enforce structured token arguments & hard process timeouts. |
| **13** | **Silent Event Bus Exception Swallowing**| **LOW** | Telemetry, Event Monitoring | **LOW** | LOW | Publish `event.handler.failed` telemetry on catch. |
| **14** | **Unvalidated Argument Types** | **LOW** | Tool Runtime, API Adapters | **MEDIUM** | LOW | Standardize `ArgumentNormalizer` across all invocations. |
| **15** | **Stale SQLite FTS5 Search Indexes** | **LOW** | Full-Text Search, Memory Search | **LOW** | LOW | Atomic FTS index updates within DB transaction triggers. |
| **16** | **Synchronous UI Main Thread Blocking**| **MEDIUM**| Desktop HUD, System Tray, Web App| **MEDIUM** | LOW | Qt Signal/Slot bridge for all worker thread dispatches. |
| **17** | **Unsynchronized Multi-Session State** | **LOW** | Web Dashboard vs CLI Sessions | **LOW** | LOW | Centralize active session registry in memory database. |
| **18** | **Model Profile Capability Mismatch** | **LOW** | Multimodal Vision Tasks | **MEDIUM** | LOW | Capability-based routing filter in `SmartRouter`. |
| **19** | **Plugin Registration Drift** | **LOW** | Dynamic Tool Discovery | **LOW** | LOW | Enforce schema validation and immutable names in registry. |
| **20** | **Unbounded Audio Ring Buffer Memory** | **LOW** | Continuous Voice Listening | **LOW** | LOW | Bounded circular ring buffer with automatic drop-oldest. |
