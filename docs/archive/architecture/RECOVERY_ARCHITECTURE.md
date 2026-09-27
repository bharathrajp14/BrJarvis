# RECOVERY ARCHITECTURE — BR JARVIS MK40.2

## 1. Autonomous Self-Repair & Recovery Pipeline

Execution failures are analyzed systematically by `RecoveryManager` and `agent/recovery_engine.py` using automated categorization:

```text
[EXECUTION FAILURE OCCURS]
            │
            ▼
[Failure Categorization]
 ├── MISSING_DEPENDENCY   ──> Resolve PyPI package name -> pip install into .venv
 ├── ENVIRONMENT_ERROR    ──> Fallback to Tier 3/4 runtime executable
 ├── PERMISSION_DENIED    ──> Escalate to ApprovalRequest (WAITING_FOR_APPROVAL)
 ├── TIMEOUT              ──> Kill subprocess group, retry with exponential backoff
 ├── OUTPUT_CONTRACT_ERR  ──> Replan with corrected prompt parameters
 └── WINDOW_NOT_DETECTED  ──> Downgrade status to PARTIAL_SUCCESS (No false success)
```

---

## 2. Replan Governance & Bounded Loops

1. **Replan Limits**: Maximum of 2 replan attempts per task to prevent non-terminating retry loops.
2. **Checkpointing**: Every stage checkpoint is saved in SQLite WAL before replanning, allowing resumption from the last verified step without repeating successful heavy computation.
3. **Fail-Closed Escalation**: If self-repair fails or retries are exhausted, the task transitions to `FAILED` with a full actionable diagnosis.
