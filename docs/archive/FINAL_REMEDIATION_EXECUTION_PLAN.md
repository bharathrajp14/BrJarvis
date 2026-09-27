# BR JARVIS — FINAL REMEDIATION EXECUTION PLAN (ORDERED BY DEPENDENCY)

## 1. Strategic Phasing & Dependency Flow
```text
PHASE 1: Core Contracts & Type Normalization
   ↓
PHASE 2: Runtime State Machine & Truth Model
   ↓
PHASE 3: Provider Gateway & Circuit-Breaker Fallback
   ↓
PHASE 4: Tool Runtime & Argument Normalization
   ↓
PHASE 5: Physical Observation & Verification Engine
   ↓
PHASE 6: Memory & Concurrency Governance
   ↓
PHASE 7: Vision & DPI Coordinate Mapping
   ↓
PHASE 8: Voice Acoustic Isolation & Barge-In
   ↓
PHASE 9: Artifact Sandbox & Host Export Pipeline
   ↓
PHASE 10: Task DAG & Workflow Decomposition
   ↓
PHASE 11: Security & Path Confinement
   ↓
PHASE 12: Observability & Distributed Tracing
   ↓
PHASE 13: UI Non-Blocking Signal Bridge
   ↓
PHASE 14: Master Test Suite Hardening
   ↓
PHASE 15: Full E2E Master Task Production Certification
```

---

## 2. Phase Deliverable Gates
- **Phase 1 Gate**: `ToolResult`, `Observation`, and `TaskExecutionDiagnostic` standardized across all modules.
- **Phase 2 Gate**: `TaskStateMachine` prohibits `EXECUTED -> COMPLETED` without `VERIFIED`.
- **Phase 3 Gate**: Mid-flight automatic provider failover verified on cloud 429 quota exhaustion.
- **Phase 4 Gate**: Path, URL, and boolean normalization applied prior to tool policy check.
- **Phase 5 Gate**: Universal file, process, DOM, and system setting verification hooks operational.
- **Phase 6 Gate**: 100% of SQLite database writes routed through `sqlite_lock.py`.
- **Phase 7 Gate**: Click coordinates accurately hit target UI buttons on Windows 125%/150% displays.
- **Phase 8 Gate**: Mic ring buffer drained during active speech synthesis (<15ms barge-in mute).
- **Phase 9 Gate**: `sandbox_path != host_path` invariant strictly verified before host browser launch.
- **Phase 10 Gate**: Multi-intent queries decomposed into topological dependency DAGs.
- **Phase 11 Gate**: Canonical path policy blocks symlink and junction traversal attempts.
- **Phase 12 Gate**: Trace IDs attached to all task execution spans and error logs.
- **Phase 13 Gate**: Background worker dispatches execute asynchronously off the Qt GUI thread.
- **Phase 14 Gate**: 100% pass across all 473+ unit, security, and integration tests.
- **Phase 15 Gate**: Complete autonomous execution of master multimodal audit task certified.
