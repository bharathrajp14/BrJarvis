# 20 — CONTRADICTION ENGINE & CROSS-VALIDATION

## 1. Overview of Detected Contradictions
The contradiction engine continuously compares evidence across documentation, code implementations, tests, and configurations.

---

## 2. Catalog of Identified Architectural Contradictions

### CONTRADICTION 01: Model Gateway vs Direct Backends
- **Documentation / Spec**: Claims a single unified `gateway/model_gateway.py` routes all requests with circuit breaking.
- **Code Reality**: `backends/gemini.py` and `router/core.py` independently make direct API calls bypassing `gateway/model_gateway.py`.
- **Impact**: Inconsistent rate limit tracking and duplicate retry loops.
- **Resolution**: Route all model invocations strictly through a single Gateway layer.

### CONTRADICTION 02: Dual Action & Tool Execution Layers
- **Documentation / Spec**: Claims tools are registered in declarative schemas in `tools/`.
- **Code Reality**: `actions/` contains 58 legacy procedural scripts directly invoked by `core/intent_engine.py`, bypassing tool validation.
- **Impact**: Security policy checks can be bypassed if an intent invokes an action directly.
- **Resolution**: Consolidate `actions/` into standard tools and connectors.

### CONTRADICTION 03: Dual Bootstrapping Sequences
- **Documentation / Spec**: `core/bootstrap.py` is the official DI bootstrapper.
- **Code Reality**: `start.py` contains 1,000 lines of legacy bootstrapping code that re-implements container instantiation.
- **Resolution**: Make `start.py` a thin launcher delegating 100% to `core/bootstrap.py`.

### CONTRADICTION 04: Storage Disconnect
- **Documentation / Spec**: Claims a single Unified Memory system.
- **Code Reality**: 8 distinct databases and storage JSON files are written independently across `.jarvis/`, `memory_db/`, and `workspace/`.
- **Resolution**: Unify all relational schemas into `.jarvis/jarvis_core.db`.
