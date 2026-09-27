# BR JARVIS MK40.2 — Real World Verification Scenarios

## Overview
The real-world verification suite executes 100 concrete, deterministic test cases covering 6 operational domains:

---

### Category 1: 20 Deterministic Intent & Routing Tasks
- **Objective**: Match natural language user requests to accurate tool/subsystem intents with zero hallucination.
- **Verification**: Exact intent classification, required parameter extraction, and correct tier assignment.

---

### Category 2: 20 Informational & System Inspection Tasks
- **Objective**: Query local system state (disk space, git branches, process lists, environment variables).
- **Verification**: Output contract parsing, schema conformity, non-empty verified observations.

---

### Category 3: 20 Multi-Step Workflows with Memory Context
- **Objective**: Chain actions across multiple steps where step $N+1$ depends on memory recalled from step $N$.
- **Verification**: Unified memory recall accuracy, file persistence, structural integrity validation.

---

### Category 4: 20 Coding, Diagnostics & Sandbox Tasks
- **Objective**: Execute code snippets, run diagnostic health checks, and catch errors in the isolated sandbox.
- **Verification**: Sandboxed process exit code 0, standard output matching expected computation, memory limit enforcement.

---

### Category 5: 10 Browser & OS Desktop Operations
- **Objective**: Plan browser interactions and desktop window inspections without executing destructive actions.
- **Verification**: Capability authorization check, security sandbox boundaries, non-destructive simulation.

---

### Category 6: 10 Ambiguity, Recovery & Adversarial Tasks
- **Objective**: Gracefully handle missing parameters, contradictory requirements, and malformed inputs.
- **Verification**: Auto-repair invocation, clarifying question generation, circuit breaker stability.
