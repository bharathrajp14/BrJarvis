# BR JARVIS — Execution Graph & DAG Resolution Specification

## 1. Graph Model & Topological Ordering

The `ExecutionGraph` models task decomposition as a Directed Acyclic Graph (DAG) $G = (V, E)$, where:
- $V = \{s_1, s_2, \dots, s_n\}$ represents atomic `ToolStep` capability invocations.
- $E = \{(s_i, s_j)\}$ indicates that step $s_j$ depends on the completed result of $s_i$.

```text
              ┌─── Web Search (OpenClaw) ───┐
              │                             │
Task Request ─┼── Repo Scan (BR JARVIS) ────┼──> Comparative Synthesis ──> DOCX Create ──> Verifier ──> Host App Open
              │                             │
              └─── System Hardware Audit ───┘
```

### Topological Wave Formation (Kahn's BFS)
1. Compute in-degree $\text{deg}(s)$ for all $s \in V$.
2. Push all nodes with $\text{deg}(s) = 0$ into the ready queue.
3. Form non-conflicting execution waves bounded by `max_concurrency` (default: 4 parallel workers).
4. Cycle detection triggers a deterministic `ValueError` if processed nodes $< |V|$.

---

## 2. Dynamic Input Mapping Resolution

Inputs to downstream steps are evaluated dynamically via `ToolInputMapper` at dispatch time:

```json
{
  "step_id": "step_create_report",
  "tool": "document_creator",
  "dependencies": ["step_web_search", "step_repo_scan", "step_compare"],
  "input_mappings": {
    "title": "OpenClaw vs BR JARVIS Comparison Report",
    "content": "$steps.step_compare.output.markdown_content",
    "filename": "workspace/Documents/OpenClaw_vs_BR_JARVIS_Comparison.docx"
  }
}
```

### Supported Mapping Syntax
- `$task.user_query` / `$task.goal` — Injects the raw or augmented user request.
- `$steps.<id>.output` — Injects the complete return payload of an upstream step.
- `$steps.<id>.output.<field>` — Deep key extraction from dictionary/JSON outputs.
- `result://<task_id>/<step_id>` — Resolves cached tool execution records.
- `artifact://<task_id>/<filename>` — Resolves absolute host filesystem path of generated artifacts.
- `file://<path>` — Resolves local workspace filesystem path.

---

## 3. Concurrency & Resource Exclusion Rules

To prevent filesystem and database race conditions during concurrent tool execution, `ExecutionGraph` enforces Reader-Writer exclusion locks:

| Lock Mode | Behavior | Compatible With |
|:---|:---|:---|
| **Shared Read (`is_write=False`)** | Step only inspects data (e.g. `web_search`, `file_read`, `system_diagnostic`). | Other Shared Reads on same `resource_keys`. |
| **Exclusive Write (`is_write=True`)** | Step mutates persistent state (e.g. `document_creator`, `file_write`). | Cannot run concurrently with any reads or writes sharing `resource_keys`. |

---

## 4. Checkpoint & Resumption Lifecycle

```text
[Step Dispatched] ──> SQLite WAL Checkpoint (Status: RUNNING)
       │
       ▼
[Tool Invocation] ──> ActionVerifier Evaluation
       │
       ▼
[Step Completed]  ──> StepResultStore Saved ──> SQLite WAL Checkpoint (Status: SUCCESS_VERIFIED)
       │
   (Crash/Restart)
       │
       ▼
[Task Resume]     ──> Load from SQLite DB ──> Skip Completed Steps ──> Resume Pending Wave
```

All mutations are atomic, idempotent, and verified before proceeding to downstream dependencies.
