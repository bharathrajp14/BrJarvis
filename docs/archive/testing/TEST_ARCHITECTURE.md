# BR JARVIS MK40.2 — Test Architecture Specification

## 1. Architectural Philosophy
The fundamental invariant of the BR JARVIS test architecture is:
$$\mathbf{Passing\ tests\ must\ correspond\ to\ actual\ working\ software.}$$

Testing is never treated as a count-maximization exercise or a mock-heavy verification of trivial booleans. The test system is architected to guarantee physical verification, contract conformance, fault-tolerance, and cross-task isolation.

---

## 2. The 9-Tier Truth Hierarchy
Lower truth levels NEVER imply higher truth levels:

```
Level 1: CODE_EXISTS
   ↓ (Module has valid syntax on disk)
Level 2: IMPORTS
   ↓ (Module imports cleanly without circular dependencies)
Level 3: INITIALIZES
   ↓ (Subsystems instantiate with valid configuration)
Level 4: CALLS
   ↓ (Method accepts parameters and returns structured schema)
Level 5: EXECUTES
   ↓ (Underlying OS/subprocess command ran)
Level 6: SIDE_EFFECT_OCCURRED
   ↓ (File written, process PID spawned, network packet transmitted)
Level 7: ARTIFACT_VALID
   ↓ (Non-zero bytes, valid magic headers, parses with native document engine)
Level 8: PHYSICAL_STATE_VERIFIED
   ↓ (Window active on screen, process responsive, database WAL durable)
Level 9: TASK_VERIFIED
     (TaskCompletionGate certifies full requirement satisfaction)
```

---

## 3. Test Pyramid & Marker Classification

| Marker | Scope | Execution Target | Mocking Policy | Isolation Level |
|---|---|---|---|---|
| `pytest -m unit` | Isolated components, algorithms, schemas, state machines | < 50ms per test | Mocks allowed for external cloud APIs only | Thread & Memory Isolated |
| `pytest -m smoke` | Bootstrap, doctor diagnostics, CLI/Web entrypoints | < 5s per test | Pure local-first execution | Production Environment |
| `pytest -m integration` | Multi-subsystem data pipelines, SQLite WAL, document export | < 500ms per test | Real local parsers & temp directories | Temporary Directory Sandbox |
| `pytest -m security` | Path traversal, prompt injection, policy engine fail-closed | < 100ms per test | Adversarial hostile payloads | Strict Jail Sandbox |
| `pytest -m reliability` | Concurrency scaling, DAG safety, soak slopes | Multi-threaded stress | Real SQLite & real memory models | Process Sandbox |
| `pytest -m e2e` | End-to-end user workflows (CLI to artifact to UI) | < 15s per test | Deterministic mocked external servers | Isolated Host Workspace |

---

## 4. Test Isolation & Data Cleanliness Rules
1. **Zero State Leakage**: Tests must never mutate `.env`, production `.jarvis/`, production databases, or host user files.
2. **Deterministic Temporary Workspaces**: All file creation tests use `tmp_path` fixtures with automatic cleanup.
3. **Hardware Independence**: Unit tests must never require physical audio input/output devices or live browser hardware.
4. **Order Independence**: Tests must pass individually, in file, in directory, and in full suite execution.
