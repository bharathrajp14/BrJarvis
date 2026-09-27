# BR JARVIS — Multi-Tool Orchestration Architecture (MK40)

## Executive Summary
BR JARVIS MK40 introduces a **Capability-Driven Multi-Tool Orchestration Engine**. The system transitions from single-turn, isolated tool calls into a resilient, dependency-aware Directed Acyclic Graph (DAG) execution pipeline.

```text
                               ┌─────────────────────────┐
                               │       USER TASK         │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │ Stage Decomposer / Plan │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │   Tool Dependency DAG   │
                               └────────────┬────────────┘
                                            │
                     ┌──────────────────────┼──────────────────────┐
                     ▼                      ▼                      ▼
             ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
             │ Wave 1: Tool │       │ Wave 1: Tool │       │ Wave 1: Tool │
             │  Web Search  │       │  Repo Scan   │       │ System Diag  │
             └───────┬──────┘       └───────┬──────┘       └───────┬──────┘
                     └──────────────────────┼──────────────────────┘
                                            ▼
                               ┌─────────────────────────┐
                               │    Step Result Store    │
                               │  & Dynamic Input Mapper │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │ Wave 2: Synthesis & Doc │
                               │     (DOCX Creation)     │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │  Wave 3: Verifier Engine│
                               │  (Integrity Validation) │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │  Wave 4: App Launcher   │
                               │    & Open Verifier      │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │   Memory & Experience   │
                               │     Learning Update     │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │ Verified Final Summary  │
                               └─────────────────────────┘
```

---

## 1. Core Architectural Pillars

### A. Separation of Reasoning and Execution
- **Planner / LLM**: Analyzes user intent, required capabilities, and dynamic dependencies.
- **Orchestrator (`ParallelToolExecutor`)**: Enforces bounded concurrency, wave scheduling, parameter resolution, timeouts, and resource locks.
- **Action Verifier (`ActionVerifier`)**: Independently verifies file creation, structural integrity (DOCX, PDF, XLSX, JSON), OS processes, and window handles.
- **State Store (`TaskCheckpointer`)**: Records atomic SQLite WAL checkpoints after every state transition, enabling safe crash recovery without repeating dangerous actions.

### B. Dynamic Input Mapping & Structured Result Passing
Rather than hallucinating paths or requiring the LLM to manually copy strings between tool turns:
- Tools reference upstream results using `$steps.<step_id>.output.<field>` or `$task.<field>`.
- The `StepResultStore` maintains structured outputs and resolves URI references:
  - `result://<task_id>/<step_id>`
  - `artifact://<task_id>/<filename>`
  - `file://<absolute_path>`

### C. Capability-Driven Tool Health & Fallback Chains
- Tools are categorized by capability: `WEB_SEARCH`, `OFFICE_DOC`, `BROWSER`, `FILE_SYSTEM`, `REPO_ANALYSIS`, `SYSTEM_DIAG`, `CODE_EXEC`, `COMMUNICATION`.
- Tools track health states: `READY`, `DEGRADED`, `DISABLED`, `BLOCKED`, `UNAVAILABLE`.
- When a primary tool fails (e.g. API quota or missing driver), the orchestrator automatically cascades to a compatible fallback tool (e.g. `tavily_search` -> `web_search` -> `fetch_page`).

---

## 2. Component Class Overview

| Component | Responsibility |
|:---|:---|
| `ToolPlan` | Task contract containing ordered `ToolStep` definitions, budgets, and completion predicates. |
| `ToolStep` | Atomic unit of work with tool name, category, parameters, input mappings, fallback tools, and resource locks. |
| `ExecutionGraph` | Topological sort, Kahn's cycle detection, and wave scheduler with reader-writer resource exclusion. |
| `StepResultStore` | Thread-safe key-value store for intermediate results and artifact URIs. |
| `ToolInputMapper` | Resolves `$steps` and `$task` placeholders into concrete arguments at execution time. |
| `ToolHealthManager` | Health tracker and fallback registry for seamless tool failover. |
| `ParallelToolExecutor` | Thread-pool wave executor with checkpoints, retry backoff, and progress callbacks. |
| `TaskCheckpointer` | SQLite WAL persistence engine supporting instant resumption after restarts. |
| `ActionVerifier` | Multi-layered empirical verifier confirming filesystem mutations and OS window states. |

---

## 3. Execution Lifecycle

1. **Decomposition**: Prompt is evaluated by `StageDecomposer` / `PlannerEngine` and transformed into a `ToolPlan`.
2. **Graph Validation**: `ExecutionGraph` checks dependencies and verifies acyclicity.
3. **Wave Execution**: Independent steps are grouped into conflict-free waves and executed concurrently in a worker pool.
4. **Result Resolution**: Downstream steps dynamically pull resolved values from `StepResultStore`.
5. **Action Verification**: Each step is empirically validated via `ActionVerifier`.
6. **Checkpointing**: Every step state change is saved to SQLite WAL.
7. **Task Synthesis**: Final report derives strictly from verified execution evidence records.
