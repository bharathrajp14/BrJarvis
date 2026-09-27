# BRJARVIS // PERFORMANCE BASELINE
**Recorded:** 2026-09-27 14:11:57  

| Metric | Measured Baseline | Target |
| :--- | :--- | :--- |
| **`jarvis.core.AssistantRuntime` Boot** | `5153.95 ms` | `< 50 ms` |
| **`brjarvis.core.ApplicationRuntime` Boot** | `240.23 ms` | `< 150 ms` |
| **Doctor Diagnostics Check** | `0.34 ms` | `< 30 ms` |
| **Tool Registry Hydration (200 Tools)** | `4776.45 ms` | `< 200 ms` |
| **AgentLoop Fast-Path Turn** | `14.07 ms` | `< 10 ms` |
| **TaskState 5x Transitions** | `0.0185 ms` | `< 1 ms` |
| **Regression Test Suite (402 Tests)** | `90.95 s` | `< 60 s` |
