# BR JARVIS FULL-SYSTEM ARCHITECTURAL MAP & DEPENDENCY GRAPH

## 1. Canonical End-to-End Control Plane Flow

```mermaid
flowchart TD
    subgraph Clients["Presentation Layers / Client Interfaces"]
        WUI["Web Dashboard (Vanilla JS + Modern CSS)"]
        CLI["CLI REPL (Rich TUI + Profiles)"]
        DUI["Desktop GUI (HUD / Float Widget)"]
        VCE["Voice Pipeline (Silero VAD + STT/TTS)"]
        EXT["REST API / Mobile Gateway"]
    end

    subgraph API_GW["API & Session Boundary (FastAPI)"]
        SEC_AUTH["Auth Middleware / Token / Ticket Session Engine"]
        REST_ROUTES["Versioned API (/api/v1/*, /health, /tasks, /files)"]
        WS_HANDLER["WebSocket Hub (Typed JSON Schema / Heartbeat / PubSub)"]
    end

    subgraph Runtime["Application Runtime (Canonical Core Singleton)"]
        CFG["JarvisConfig (Pydantic v2 + Precedence Authority)"]
        LIFE["LifecycleManager (Supervision & Startup/Shutdown Hooks)"]
        EVBUS["EventBus (Telemetry, State Machine & Task Events)"]
        DI["DI Container (Service Locator & Singletons)"]
        HEALTH["Health Monitor (/live, /ready, /components)"]
    end

    subgraph Orchestration["Cognitive Engine & Planning"]
        ORCH["JarvisOrchestrator (Cognitive Coordinator)"]
        FAST_PATH["Deterministic Intent Engine (Fast-Path Actions)"]
        SMART_ROUTER["Smart Model Router (Capability / Profile Selection)"]
        STEP_PLAN["Step Planner & Stage Decomposer"]
        TASK_SM["Task State Machine (SQLite WAL Checkpointing)"]
    end

    subgraph Gateway["Model Gateway Layer"]
        MOD_GW["Unified Model Gateway (Circuit Breaker, Fallbacks, Accounting)"]
        ADAPT["Provider Adapters (Gemini, Claude, GPT, Ollama, Mistral)"]
    end

    subgraph Security["Security & Policy Gate"]
        GUARD["Guardian Core & Prompt Injection Shield"]
        POL_ENG["Deterministic 6-Tuple Policy Engine (Fail-Closed)"]
        CAP_AUTH["Capability & Path Isolation Manager"]
    end

    subgraph Tools["Tool Runtime & Registry"]
        TOOL_REG["Canonical Tool Registry (Typed Schemas & Metadata)"]
        TOOL_RUN["Tool Runtime Engine (Timeout, Sandbox, Metrics)"]
        SUB_PROC["Sandboxed Process / OS Bridge"]
    end

    subgraph Execution["Side Effect Boundaries"]
        OS_SYS["OS Control (Processes, Settings, Windows/Linux/Mac)"]
        BROWSER["Playwright / Browser Automation Service"]
        CONN["Connector Hub (Filesystem, Notion, Slack, GitHub, etc.)"]
        ARTIFACTS["Artifact Management Subsystem (Isolated Sandbox)"]
    end

    subgraph Verification["Physical Verification Layer"]
        VERIFIER["Action Verifier (Process Window, URL State, File Format, Output)"]
    end

    subgraph Persistence["Unified Persistence & Memory"]
        CAN_DB["Canonical SQLite DB (WAL Mode, Tasks, Audit, Sessions)"]
        VEC_MEM["Vector Memory (Semantic Recall)"]
        KG_MEM["Knowledge Graph & Lessons Learned"]
    end

    %% Flow Connections
    WUI -->|"HTTP / WSS"| SEC_AUTH
    CLI -->|"Direct In-Process API"| Runtime
    DUI -->|"Direct / Local IPC"| Runtime
    VCE -->|"Audio Signal -> Intent"| Runtime
    EXT -->|"Bearer / Key"| SEC_AUTH

    SEC_AUTH --> REST_ROUTES
    SEC_AUTH --> WS_HANDLER

    REST_ROUTES --> Runtime
    WS_HANDLER --> Runtime

    Runtime --> ORCH
    ORCH --> FAST_PATH
    ORCH --> SMART_ROUTER
    ORCH --> STEP_PLAN
    STEP_PLAN --> TASK_SM

    SMART_ROUTER --> MOD_GW
    MOD_GW --> ADAPT

    ORCH --> GUARD
    GUARD --> POL_ENG
    POL_ENG --> CAP_AUTH
    CAP_AUTH --> TOOL_REG
    TOOL_REG --> TOOL_RUN
    TOOL_RUN --> SUB_PROC

    SUB_PROC --> OS_SYS
    SUB_PROC --> BROWSER
    SUB_PROC --> CONN
    SUB_PROC --> ARTIFACTS

    OS_SYS --> VERIFIER
    BROWSER --> VERIFIER
    CONN --> VERIFIER
    ARTIFACTS --> VERIFIER

    VERIFIER -->|"Verified Observation"| TASK_SM
    TASK_SM -->|"Task State Update"| EVBUS
    TASK_SM -->|"Write State"| CAN_DB
    ORCH -->|"Store Turns & Context"| VEC_MEM
    ORCH -->|"Record Knowledge"| KG_MEM

    EVBUS -->|"Stream Events"| WS_HANDLER
    EVBUS -->|"Stream Events"| CLI
    EVBUS -->|"Telemetry"| HEALTH
```

---

## 2. Forensic Audit: Existing Alternate & Competing Paths

| Component Area | Canonical Implementation | Alternate / Competing Paths Discovered | Resolution & Unification Strategy |
| :--- | :--- | :--- | :--- |
| **Runtime & Boot** | `core/runtime.py` (`ApplicationRuntime`) & `core/bootstrap.py` | `start.py`, `server.py`, `dashboard/server.py`, `brjarvis.py` | Unify all launchers to delegate to `CoreBootstrapper.initialize_runtime()` and `create_app()`. Eliminate duplicated bootstrap scripts. |
| **Dashboard / Web Server** | `api/server.py` (`create_app()`) | `dashboard/server.py` (legacy 41KB script with custom AES over HTTP) | Deprecate `dashboard/server.py`. Make `api/server.py` the sole authoritative HTTP/WS server hosting `/` and `/web`. |
| **Authentication** | `api/routes/auth.py` (session tokens, short-lived WS tickets, Bearer auth) | Raw query parameter tokens (`/ws?token=...`), custom AES-256 in browser JS | Standardize on secure session exchange: REST session login / ticket endpoint -> one-time single-use ticket for WebSocket handshake. |
| **Configuration** | `core/config.py` (`JarvisConfig` via Pydantic v2) | Direct `os.environ.get()` calls scattered in `start.py`, `actions/`, `tools/`, `config/api_keys.json` | Centralize precedence: Defaults → `config/models.json` / `api_keys.json` → `.env` → `os.environ` → Runtime overrides in `JarvisConfig`. |
| **Tool Registry & Execution** | `tools/registry.py` & `tools/tool_runtime.py` | Ad-hoc tool callers in `agent/executor.py`, raw string error returns | Bind `tools/registry.py` and `tools/tool_runtime.py` to always return standardized `ToolResult` contracts with status, verification, and timing. |
| **Task State & Engine** | `agent/task_state.py` (`TaskStateManager` + SQLite WAL) | Ad-hoc dictionaries in `orchestrator/core.py`, in-memory lists in `agent/executor.py` | Centralize all task state in `TaskStateManager` and synchronize over `EventBus`. |
| **Model Gateway** | `gateway/model_gateway.py` (`ModelGateway`) & `router/smart_router.py` | Direct backend calls in `backends/gemini.py`, `backends/anthropic.py` | Ensure all LLM completions pass through `ModelGateway` with circuit breakers, timeouts, and usage accounting. |
| **Version Ownership** | Canonical version in `core/version.py` (`40.2.0`) | Hardcoded `"38.5.0"` in `pyproject.toml`, `api/server.py`, `web/app.js`, `setup.py` | Create single source of truth in `core/version.py` and propagate to package, API, UI, CLI, and health checks. |

---

## 3. Subsystem Layers & Contracts

### 3.1 Presentation Layers
- **Web UI (`web/`)**: Vanilla JS client consuming `/api/v1/*` and `/ws`. Renders real-time verified task progress, tool execution status, artifacts, and logs without executing client-side business logic.
- **CLI (`core/cli.py`)**: Rich TUI interface with typed mode profiles (`/mode general|coder|analyst|recon|exploit|report`), streaming output, cancellation support, and direct runtime binding.
- **Desktop HUD (`ui_mark.py`, `float_widget.py`)**: Glassmorphic GUI subscribing to system telemetry and audio/vision pipelines.

### 3.2 Security & Policy Boundaries
- **Prompt Injection Defense**: `guardian/prompt_injection_shield.py` inspects incoming prompts, web pages, and tool outputs before they reach the model.
- **Policy Gate**: `security/policy_engine.py` evaluates 6-tuple `(User, Session, Device, Resource, Capability, Risk)` with fail-closed semantics (`ActionDecision.DENY`).
- **Path & Shell Hardening**: `security/path_policy.py` restricts file operations to isolated workspace bounds. Shell tools disallow unsanitized model interpolation.

### 3.3 Verification & Observability
- **Action Verifier (`agent/verifier.py`)**: Evaluates real physical world consequences (e.g. process existence, window title, HTTP status, file readability).
- **Structured Logging (`core/logging.py`)**: Formats JSON logs with correlation IDs (`request_id`, `task_id`, `execution_id`) and redacts credentials automatically.
- **Event Bus (`events/bus.py`)**: Distributes typed system, task, and tool telemetry to all subscribed clients.
