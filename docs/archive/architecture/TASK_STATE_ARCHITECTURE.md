# TASK STATE ARCHITECTURE — BR JARVIS MK40.2

## 1. Single Source of Truth Task State Model

In BR JARVIS MK40.2, task execution state is strictly authoritative, persisted via SQLite WAL checkpointing, and cannot be overridden by model hallucinations or optimistic client claims.

```text
[TaskState Object]
 ├── task_id / session_id
 ├── normalized_request (Extracted Goal)
 ├── current_phase (CREATED -> UNDERSTANDING -> PLANNING -> RUNNING -> VERIFYING -> COMPLETED)
 ├── criteria: List[TaskCriterion] (C1..Cn discrete requirement contracts)
 ├── planned_steps / completed_steps / failed_steps / blocked_steps / pending_steps
 ├── tool_calls / tool_results
 ├── verification_results: List[VerificationOutcome]
 ├── artifacts: List[ArtifactRecord] (Disk path, size, hash, parsed status)
 ├── applications: List[ApplicationRecord] (PID, window title, multi-level status)
 ├── memory_updates / questions / approvals / recovery_actions
 ├── final_status: TaskStatus (Authoritatively stamped by TaskCompletionGate)
 └── completion_evidence: str
```

---

## 2. Canonical Task Status State Machine

| Status | Code | Description | Invariant |
| :--- | :--- | :--- | :--- |
| **CREATED** | `CREATED` | Task initialized with raw user prompt | No actions executed |
| **UNDERSTANDING** | `UNDERSTANDING` | Intent classification & parameter extraction | Synthesizes discrete criteria $C_1 \dots C_n$ |
| **PLANNING** | `PLANNING` | DAG step generation & tool selection | Capability bounds checked |
| **PREFLIGHT** | `PREFLIGHT` | Environment & dependency validation | Resolves virtualenv & imports |
| **RUNNING** | `RUNNING` | Active tool execution in sandbox | Captures stdout/stderr/exitcode |
| **RECOVERING** | `RECOVERING` | Self-repair or replanning in progress | Governed by `RepairPolicy` |
| **WAITING_FOR_USER** | `WAITING_FOR_USER` | Interactive clarification requested | Pauses execution timer |
| **WAITING_FOR_APPROVAL** | `WAITING_FOR_APPROVAL` | Destructive action approval gate | Fail-closed security check |
| **PARTIAL_SUCCESS** | `PARTIAL_SUCCESS` | Non-critical step or side-effect unverified | **Never reported as Complete** |
| **SUCCESS_VERIFIED** | `SUCCESS_VERIFIED` | All required criteria physically verified | **Only gate can stamp this** |
| **FAILED** | `FAILED` | Critical step failed or artifact missing | Blocks task completion |
| **CANCELLED** | `CANCELLED` | User or timeout cancellation | Cleans up child processes |

---

## 3. Requirement-Based Completion Criteria ($C_1 \dots C_n$)

Every task decomposes into explicit criteria:
- $C_1$: Deliverable generated on disk (Path exists, size $> 0$).
- $C_2$: Deliverable format structurally verified (PDF header, DOCX XML, JSON schema).
- $C_3$: Host export completed (SHA-256 hash matches, accessible in host workspace).
- $C_4$: Application viewer launched and verified (Active window title matches document name).

**Rule**: A task is `SUCCESS_VERIFIED` if and only if $\forall i \in \{1 \dots n\} : C_i.\text{required} \implies C_i.\text{status} = \text{VERIFIED}$.
If any required $C_i$ is unverified (e.g. $C_4$ viewer window not found), final status degrades to `PARTIAL_SUCCESS`.
