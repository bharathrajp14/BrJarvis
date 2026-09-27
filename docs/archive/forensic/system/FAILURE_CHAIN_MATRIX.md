# BR JARVIS — MASTER FAILURE CHAIN MATRIX

## 1. Failure Chain Methodology & The "First Broken Invariant"
In complex AI agent architectures, user-visible failure is rarely caused by the final error message.
Instead, a subtle broken contract early in the pipeline propagates downstream until the task collapses.
This matrix identifies the **FIRST BROKEN INVARIANT** across every major user interaction workflow.

---

## 2. Failure Chains Table

| Interaction Workflow | User Prompt / Intent | Execution Chain Traced | First Broken Invariant | Manifested User Error | Root Cause |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Artifact Browser Opening** | "Create an HTML report and open it in the browser" | `Planner -> write_file -> browser_open_url -> Browser` | `sandbox_path` passed directly to host browser without explicit export | `ERR_FILE_NOT_FOUND` in Chrome/Edge | Browser cannot access sandboxed virtual workspace without `ensure_host_artifact()` export |
| **Visible Browser Search** | "Open GitHub and search for BR JARVIS" | `Intent -> web_search -> browser_open` | Web search API returned markdown text without triggering visible browser navigation | Search summary spoken, but user browser window never navigated | Architecture conflated background `web_search` with visible `browser_navigate` |
| **Unverified File Move** | "Move data.csv to archive/ and verify" | `Planner -> move_file -> Orchestrator Response` | Tool returned without checking destination file existence on disk | JARVIS reported "Moved successfully" when destination disk was write-locked | Missing `ActionVerifier.verify_file_exists()` check before reporting success |
| **Compound Voice Command** | "Check CPU, take a screenshot, and summarize" | `Mic -> VAD -> STT -> Intent -> Fast-Path` | Heuristic fast-path matched first token ("check CPU") and dropped compound clauses | Fast-path executed CPU check, ignoring screenshot and summary | Regex intent engine lacked compound multi-clause stage decomposition |
| **Cloud Quota Exhaustion** | "Analyze codebase with Gemini Pro" | `Orchestrator -> SmartRouter -> Gateway -> Gemini 429` | Gateway caught 429 but threw generic exception to orchestrator | "All backends failed" without fallback to Claude/Ollama | Router lacked dynamic mid-flight fallback re-routing on rate-limit exhaustion |
| **Database Lock Contention** | Rapid simultaneous memory updates | `Agent 1 write -> Agent 2 write -> SQLite` | Synchronous SQLite write executed on busy database without WAL lock | `sqlite3.OperationalError: database is locked` | Missing asynchronous serialized writer lock (`sqlite_lock.py`) |
| **Barge-In Echo Cancellation**| User speaks while JARVIS is speaking | `TTS Audio Playing -> Mic -> VAD -> STT` | Microphone recorded TTS speaker echo as new user speech | JARVIS interrupted itself and answered its own spoken output | Missing acoustic echo suppression / mic drain buffer on speech start |
| **Screen Element Click** | "Click the 'Submit' button on screen" | `Screen Capture -> OCR -> Semantic Graph -> Click` | Coordinate translated to logical DPI instead of native physical pixels | Mouse clicked 30px above target button | DPI scale factor mismatch between DXGI capture (physical) and Win32 SendInput (logical) |
