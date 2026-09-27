# BR JARVIS — SUBSYSTEM DEPENDENCY GRAPH & DIRECTIONALITY

## 1. Direction of Dependency Invariant
Dependencies strictly flow downward from presentation and API layers to core domain and platform abstractions:

```text
Presentation Layer (UI / CLI / start.py)
       ↓
API Layer (api/server.py / WebSocket)
       ↓
Application Core (core/runtime.py / core/bootstrap.py)
       ↓
Cognitive & Orchestration (orchestrator/ / router/ / gateway/ / agent/)
       ↓
Policy & Security (security/ / guardian/)
       ↓
Tool Execution Runtime (tools/ / actions/)
       ↓
Storage & State (memory/ / database/)
       ↓
Platform Abstraction & OS Adapters (platform/ / computer/ / voice/ / vision/)
```

---

## 2. Invariant Rules
1. Platform adapters and OS integration never import from UI or API layers.
2. Tool handlers never bypass `security/policy_engine.py` or `security/path_policy.py`.
3. Memory mutations always route through `memory/sqlite_lock.py` to ensure thread-safe SQLite WAL access.
