# ARTIFACT 04: BR JARVIS PRODUCTION TARGET ARCHITECTURE
**System**: BR JARVIS Autonomous AI Operating System  
**Architecture Classification**: Local-First Autonomous AI Control Plane  
**Target Design Standard**: Mission-Critical, Sandboxed, Deterministic Policy, Crash-Resilient, Multi-Modal

---

## 1. Primary Architectural Principles

1. **Non-LLM Authority on Security**: The LLM is an untrusted planner/reasoner. It is never the final authority for permissions, file access, authentication, or network boundaries.
2. **Deterministic Policy Enforcement**: Every consequential action undergoes deterministic 6-tuple policy evaluation `(User, Device, Application, Resource, Action, Risk) -> (ALLOW, DENY, CONFIRM)`.
3. **Durable Event-Sourced Task Control Plane**: Task execution state transitions are flushed to a write-ahead SQLite log before invoking tool side effects. Unplanned process restarts seamlessly resume or safely recover pending tasks.
4. **True Process Sandboxing**: Host system code execution is isolated using OS-level process tokens, CPU/memory quotas, and network/filesystem path jails.
5. **Strawberry-Class Browser & Semantic Accessibility**: Computer and browser automation prioritize DOM, Accessibility Trees, and UI Automation (UIA) over brittle raw pixel coordinates.
6. **Zero-Trust Mobile Security**: Android companion pairing uses cryptographic public key tokens and explicit lock-state gating (`WAITING_FOR_USER_AUTHENTICATION`), never attempting to bypass locks or biometrics.

---

## 2. End-to-End Control Plane Flow

```
                      +------------------------------------------+
                      |         User / Ingestion Layer           |
                      |  (Web Dashboard, Voice, CLI, Webhooks)   |
                      +--------------------+---------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |           API Gateway & Auth             |
                      |  (FastAPI, JWT/API-Key, Correlation ID)  |
                      +--------------------+---------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |       Deterministic Policy Engine        |
                      | (6-Tuple Rule Matrix & Human Interlock)  |
                      +--------------------+---------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |            Task Control Plane            |
                      |   (State Machine, Event WAL, Recovery)   |
                      +--------------------+---------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |           Agent Orchestrator             |
                      |  (DAG Step Planner & Capability Router)  |
                      +--------------------+---------------------+
                                           |
                                           v
  +----------------------------------------------------------------------------------+
  |                             Capability Execution Layer                           |
  |  +--------------------+  +--------------------+  +----------------------------+  |
  |  |  Sandboxed Tools   |  | Strawberry Browser |  | Android Companion Gateway  |  |
  |  |  (Job Object Jail) |  |  (DOM + UIA Tree)  |  | (Authenticated WebSocket)  |  |
  |  +--------------------+  +--------------------+  +----------------------------+  |
  +----------------------------------------+-----------------------------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |         Post-Action Verification         |
                      |  (State Diff, DOM Check, File Hash Diff) |
                      +--------------------+---------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |      Persistence, Memory & Audit         |
                      |  (Canonical WAL DB, Vector Store, Logs)  |
                      +------------------------------------------+
```

---

## 3. Subsystem Architectural Blueprints

### 3.1. API & Gateway Layer (`api/`)
Modular FastAPI structure replacing the monolithic `server.py`:
- `api/server.py`: Clean application factory with lifespan management, CORS middleware, and error handlers.
- `api/routes/auth.py`: API key, session tokens, and pairing PIN verification.
- `api/routes/tasks.py`: Autonomous task creation, step inspection, cancellation, and approval resolution.
- `api/routes/devices.py`: Device discovery, pairing tokens, hardware telemetry, and Android status.
- `api/routes/routines.py`: Scheduled, event-driven, and webhook background automation management.
- `api/routes/skills.py`: Declarative versioned skill listing, validation, execution, and rollback.
- `api/routes/connectors.py`: Third-party app connectors status, credentials configuration, and tool calls.
- `api/routes/memory.py`: Canonical knowledge retrieval, contact management, and vCard/document ingestion.
- `api/routes/websocket.py`: High-throughput bidirectional real-time log, audio streaming, and mobile control channels.

### 3.2. Task Control Plane & Execution Engine (`agent/`)
- **Task Lifecycle States**:
  `CREATED -> PLANNING -> WAITING_FOR_APPROVAL -> RUNNING -> WAITING_FOR_DEVICE -> WAITING_FOR_AUTH -> WAITING_FOR_USER -> PAUSED -> RECOVERING -> VERIFYING -> COMPLETED / PARTIAL / FAILED / CANCELLED`.
- **Durable TaskStateManager**: Flushes every state transition to `.jarvis/jarvis_canonical.db` with WAL mode.
- **Crash Recovery Watchdog**: Upon initialization, identifies incomplete tasks, runs self-healing inspection, and restarts execution from the last validated checkpoint.
- **Step Planner**: Translates natural language goals into a structured `GoalGraph` specifying `capability`, `parameters`, `dependencies`, `risk_level`, `verification_method`, and `retry_policy`.

### 3.3. Capability Execution & Tool System (`tools/` & `connectors/`)
- **Strongly-Typed Tool Definitions**: Every tool implements a `ToolDefinition` dataclass specifying:
  - `name`: Unique capability identifier.
  - `description`: LLM-facing purpose.
  - `input_schema`: Strict Pydantic model.
  - `output_schema`: Typed structured output model.
  - `risk_level`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
  - `permissions_required`: Required permission scopes.
  - `side_effects`: Declared filesystem/network/process mutations.
  - `idempotent`: Boolean flag indicating safe retry behavior.
  - `timeout`: Maximum execution duration in seconds.
  - `verification_strategy`: Automated post-execution check (`file_exists`, `dom_element_present`, `http_status_200`, `exit_code_zero`).

### 3.4. Browser Automation (`tools/browser_agent_v2.py`)
- **Observation Stack**:
  1. DOM Accessibility Tree & Semantic Selectors (ARIA roles, IDs, stable text).
  2. Viewport Screenshot (Multimodal vision context).
  3. Interactive Element Registry (Integer-indexed elements mapped to CSS/XPath selectors).
  4. Raw Pixel Coordinates (Strict fallback only when no accessibility selector is exposed).
- **Automated Dialog & Challenge Handling**:
  - Automatically dismisses cookie banners, popups, and modal dialogs.
  - Detects CAPTCHA / Cloudflare challenges -> Pauses task and triggers `WAITING_FOR_USER` state with screenshot notification.

### 3.5. Mobile Subsystem (`mobile/`)
- **Architecture**:
  ```
  mobile/
  ├── gateway.py          # Device pairing, cryptographic auth tokens, trusted state
  ├── session.py          # WebSocket connection manager, ping/pong heartbeat, frame buffering
  ├── protocol.py         # Strongly-typed MobileMessage schemas (JSON & Binary)
  ├── device_controller.py# High-level actions: open_app, click, type, inspect_screen
  ├── screen_understanding.py # Accessibility hierarchy parser & semantic summarizer
  └── security.py         # Lock state detection, biometric prompt integration, permission gates
  ```
- **Lock-Screen Policy**: If `is_locked == True`, the system transitions to `WAITING_FOR_AUTH` and notifies the user. Zero lock-bypass exploits.

### 3.6. Memory & State Persistence (`memory/`)
- **Canonical Storage**: Unified SQLite database (`.jarvis/jarvis_canonical.db`) with distinct tables for `memories`, `contacts`, `tasks`, `task_steps`, `routines`, `devices`, `skills`, and `audit_events`.
- **Vector Index**: ChromaDB vector store for semantic similarity search over documents, notes, and past tasks (derived read-only index updated via change-data-capture triggers).
- **Working Memory**: In-memory ring buffer for active conversation turns, pruned dynamically before LLM submission.
- **Selective Memory Retrieval**: Uses keyword + semantic ranking to pull only relevant context into prompt windows, preventing token bloat.

### 3.7. Observability, Telemetry & Audit (`history/` & `core/`)
- **Structured JSON Logging**: Standardized log format with timestamp, level, logger, correlation ID, task ID, and user ID.
- **Action Audit Trail**: Immutable write-only audit log recording every tool invocation, arguments (with secrets masked), caller, risk level, policy decision, execution duration, and result status.
- **Model Telemetry**: Real-time tracking of token counts, latency, estimated cost, and provider failure rates.
