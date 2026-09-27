# 22 — SYSTEM RISK REGISTER & MITIGATIONS

## 1. Risk Matrix & Severity Ranking
| Risk ID | Risk Title | Severity | Likelihood | Impact Area | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | Direct Subprocess Execution without Strict Path Confinement | CRITICAL | MEDIUM | Host OS Security | Route all shell/process calls strictly through `security/path_policy.py` & sandbox |
| **RSK-02** | Browser Profile & Cookie Tracking in Git | HIGH | HIGH | Privacy & Repo Bloat | Remove `workspace/browser_user_data/` from git; add to `.gitignore` |
| **RSK-03** | Concurrent SQLite Write Conflicts | HIGH | MEDIUM | Memory Corruption | Enforce single-writer lock via `memory/sqlite_lock.py` across all stores |
| **RSK-04** | Cloud Model Rate Limit Cascade | MEDIUM | HIGH | Availability | Multi-key rotation in `backends/gemini.py` + auto-fallback to local Ollama |
| **RSK-05** | Unbounded Re-entrant Agent Tool Loops | MEDIUM | LOW | API Token Cost | Hard cap `MAX_TOOL_ITERATIONS = 10` in `orchestrator/core.py` with watchdog timeout |
