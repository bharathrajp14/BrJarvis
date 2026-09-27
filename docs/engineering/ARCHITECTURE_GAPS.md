# BRJARVIS // ARCHITECTURE GAPS & CONVERGENCE ANALYSIS
**Document Version:** 1.0.0  
**Audit Date:** 2026-09-27  
**Status:** Verified Against Active Implementation  

---

## 1. Executive Summary

While BRJARVIS possesses extensive capabilities (200 operational tools, reactive control plane, multi-tier model gateway, 402 passing tests), the codebase exhibits structural dualism between the operational monolith (`src/brjarvis/`) and the clean target architecture (`src/jarvis/`). 

Closing these gaps requires evolving the canonical execution architecture without breaking functioning tools or UI surfaces.

---

## 2. Core Architectural Gaps

### GAP 1: Dual Tool Execution Runtimes
- **Current State:**
  - `src/brjarvis/tools/registry.py` holds 200 operational tools registered via global decorators, taking untyped `dict` and returning strings or ad-hoc dictionaries.
  - `src/jarvis/tools/registry.py` implements a clean `ToolRegistry` with typed `ToolContract`, `ToolResult`, and `RiskLevel`, but only hosts 3 built-in tools (`fs`, `system`, `terminal`).
- **Defect/Risk:** The LLM receives inconsistent tool schemas; outputs lack standard error contracts; security checks are applied inconsistently across legacy vs modern tools.
- **Convergence Target:** Implement an automated adapter (`LegacyToolAdapter`) in `src/jarvis/tools/` that wraps all 200 `brjarvis` tools into canonical `ToolContract` and `ToolResult` specifications, eliminating duplicate registries.

### GAP 2: Task State Durability & Concurrency
- **Current State:**
  - `src/jarvis/agent/task_state.py` defines a rigorous 14-state machine (`CREATED`, `QUEUED`, `PLANNING`, `WAITING_FOR_APPROVAL`, `RUNNING`, `WAITING_FOR_TOOL`, `WAITING_FOR_USER`, `VERIFYING`, `RECOVERING`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`, `ROLLED_BACK`) with optimistic concurrency revisions.
  - `src/brjarvis/web/api/routes/tasks.py` and `brjarvis/orchestrator/core.py` still store task records in local state or lightweight file stores without revision locking.
- **Defect/Risk:** Server restarts or concurrent operations can lead to state overwrite or task loss.
- **Convergence Target:** Wire `src/jarvis/memory/store.py` (`TaskRepository` backed by SQLite WAL) into `brjarvis.web.api.routes.tasks` and `brjarvis.core.runtime.ApplicationRuntime`.

### GAP 3: Memory Layering & Progressive Context Retrieval
- **Current State:**
  - Memory exists across `CanonicalMemoryStore`, `VectorMemory`, and raw SQLite files.
  - Memory injection is often all-or-nothing, dumping large blocks into model context rather than using layered retrieval.
- **Defect/Risk:** Context window bloat, token wastage, loss of relevant project constraints, and inability to distinguish between user preferences, project facts, and temporary working memory.
- **Convergence Target:**
  Implement the 7-layer memory hierarchy:
  1. Working Memory (Active turn, current step, recent tool output)
  2. Episodic Memory (Task outcomes, chronological event ledger)
  3. Semantic Memory (Stable facts, concepts, domain knowledge)
  4. User Preference Memory (Coding styles, communication tone, app defaults)
  5. Project Memory (Repo structures, architectural decisions, constraints)
  6. Artifact Memory (Catalog of generated documents, versions, checksums)
  7. Failure Memory (Failed tool strategies, known bad paths, recovery solutions)
  Incorporate progressive disclosure scoring (`recency * relevance * importance`).

### GAP 4: Computer & Browser Automation Reliability
- **Current State:**
  - Desktop control relies heavily on `LiveOSController` via downsampled screenshots and visual grid overlays.
  - Browser control tools (`browser_click`, `browser_open_url`) lack accessibility tree parsing and deterministic state assertions.
- **Defect/Risk:** Visual-only actions suffer from UI DPI scaling quirks, latency, and click-target ambiguity. Actions assume success without DOM verification.
- **Convergence Target:**
  - Implement a deterministic structured browser engine (Playwright-backed) that parses the DOM accessibility tree.
  - Require every computer-use action to emit: `intent`, `action`, `target`, `result`, and `verification_state`.

### GAP 5: Code Agent Workflow
- **Current State:**
  - `dev_agent.py` and `code_helper.py` were removed during dead-code pruning because they were non-functional stubs.
  - Currently, code generation relies on general LLM chat without an orchestrated pipeline.
- **Defect/Risk:** No automated syntax checks, static analysis, test runs, or diff verification before declaring a coding task complete.
- **Convergence Target:**
  Create an authoritative `CodeAgent` workflow:
  `Understand Repo` -> `Plan` -> `Inspect Symbols/Files` -> `Patch Code` -> `Run Tests` -> `Run Static Checks` -> `Compute Diff` -> `Verify` -> `Report Evidence`.

### GAP 6: Controlled Self-Improvement Engine
- **Current State:**
  - `src/brjarvis/evolution/engine.py` generates basic heuristic proposals, but lacks baseline benchmark comparison, sandbox testing, and automated rollback points.
- **Defect/Risk:** Untested self-modifications could break the runtime or corrupt configurations.
- **Convergence Target:**
  Enforce the formal Evolution Pipeline:
  `Observe` -> `Identify Weakness` -> `Form Hypothesis` -> `Design Patch` -> `Run Tests & Benchmarks` -> `Compare with Baseline` -> `Operator Approval Gate` -> `Apply Checkpoint` -> `Monitor & Auto-Rollback on Regression`.

### GAP 7: Diagnostics & Doctor Subsystem
- **Current State:**
  - `start.py doctor` provides basic CLI printouts.
  - REST endpoints (`/api/health`) report live metrics, but lack deep dependency and subsystem health checks.
- **Defect/Risk:** Operators cannot inspect granular subsystem health (tool registry errors, database locks, model latencies) via API.
- **Convergence Target:**
  Expose unified `/health`, `/ready`, `/diagnostics`, and `/metrics` returning machine-readable JSON status of all 10 core subsystems.

### GAP 8: Observability & End-to-End Tracing
- **Current State:**
  - Logs are logged to console and pushed over WebSocket, but lack persistent structured correlation IDs linking runs to model calls, tool calls, and verifications.
- **Defect/Risk:** Difficult to debug multi-step task failures or identify high-latency tool bottlenecks.
- **Convergence Target:**
  Add structured correlation metadata (`run_id`, `task_id`, `step_id`, `model_latency_ms`, `tool_latency_ms`, `token_usage`) to all event bus dispatches and execution ledger records.
