# BR JARVIS — MASTER RISK REGISTER & MITIGATION STRATEGY

## 1. Identified Risks & Mitigation Matrix
| Risk ID | Title | Probability | Impact | Severity | Mitigation Strategy | Fallback / Rollback Plan |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **R-01** | Path Security Bypass in Host OS Execution | LOW | CRITICAL | CRITICAL | Strictly enforce 6-tuple policy and `PathSecurityPolicy` before every file/process action | Immediate execution block; raise `SecurityViolationError` |
| **R-02** | Browser User Profile Secret Exposure in Git | HIGH | HIGH | HIGH | Purge `workspace/browser_user_data/` from git index and enforce in `.gitignore` | Local cache re-instantiation on demand |
| **R-03** | SQLite Write Concurrency Lock Deadlock | MEDIUM | HIGH | HIGH | Enforce asynchronous single-writer lock queue via `memory/sqlite_lock.py` with 5.0s timeout | Retry with exponential jitter; fallback to memory cache |
| **R-04** | Cloud Provider Rate Limit & Quota Exhaustion | HIGH | MEDIUM | HIGH | Automatic multi-key rotation in `backends/gemini.py` + circuit breaker failover to local Ollama | Graceful degradation to offline mode |
| **R-05** | UI Thread Block during Audio/Model Streaming | MEDIUM | HIGH | MEDIUM | Enforce Qt Signals (`Signal`) across thread boundaries; zero synchronous I/O on UI thread | UI remains responsive; background task can be cancelled via kill switch |
