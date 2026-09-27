# 15 — WORKFLOW & AGENT TASK SCHEDULER FORENSIC RECORD

## 1. Overview & Directed Acyclic Graph (DAG) Execution
The `workflow/` and `agent/` subsystems provide composite task decomposition, topological dependency resolution, parallel step execution, and watchdog recovery.

---

## 2. File-by-File Forensic Analysis

### `workflow/task_dag.py` (412 lines) & `agent/task_scheduler.py` (69 lines)
- **Classes**: `DAGNode`, `DAGNodeState`, `ParallelDAGExecutor`.
- **Features**:
  - Cycle detection using Kahn's algorithm (`detect_cycles()`).
  - Topological ordering for linear and branching execution graphs.
  - Asynchronous parallel execution of independent child nodes via `asyncio.gather()`.
- **Disposition**: **KEEP + IMPROVE**.

### `agent/stage_decomposer.py` (426 lines)
- **Role**: Decomposes natural language requests into structured execution stages (`StageCapability`: `SEARCH`, `CODE`, `FILE_IO`, `BROWSER`, `VERIFICATION`).
- **Disposition**: **KEEP**.

### `agent/verifier.py` (290 lines)
- **Role**: Deterministic post-condition verification.
- **Verification Methods**: `verify_file_exists()`, `verify_file_content_matches()`, `verify_process_running()`, `verify_http_status()`.
- **Disposition**: **KEEP + IMPROVE**.

### `agent/recovery_watchdog.py` (99 lines)
- **Role**: Background task monitor detecting hanging or unhandled stalled agent tasks (> 120s timeout), initiating self-healing recovery.
- **Disposition**: **KEEP**.
