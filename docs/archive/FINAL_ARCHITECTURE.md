# BR JARVIS — FINAL CANONICAL TARGET ARCHITECTURE (FROZEN)

## 1. Architectural Mission & The Personal-Project Principle
BR JARVIS is an autonomous, multimodal personal AI operating runtime for a single developer.

### Core Engineering Invariants:
1. **Single-Owner Subsystems**: Exactly ONE canonical implementation per responsibility (One Bootstrapper, One Model Gateway, One Tool Registry, One Memory Store, One Voice Loop, One Perception Router).
2. **Unified Cognitive Core**: Voice, Vision, Desktop GUI, Web Dashboard, and CLI feed the exact same central `JarvisOrchestrator`. There is no separate "voice brain" or "vision brain".
3. **Execution Truth Model**: Execution states are strictly decoupled: `REQUESTED → PLANNED → AUTHORIZED → EXECUTING → EXECUTED → OBSERVED → VERIFIED → RECOVERING → RESPONSE`. A successful tool return code is never assumed to be goal completion without post-condition verification.
4. **Deterministic Security Boundary**: Untrusted External Input → Injection Shield → Action Proposal → 6-Tuple Policy → Sandboxed Execution. The LLM cannot self-authorize.
5. **Single-Store Persistence**: All relational state, task steps, episodic turns, contacts, and procedural lessons live in `.jarvis/jarvis_core.db` operating in SQLite WAL mode with single-writer asynchronous locks.

---

## 2. Canonical Subsystem Hierarchy

```mermaid
graph TD
    subgraph Presentation & Client Layer
        CLI[CLI: brjarvis.py / core/cli.py]
        GUI[PySide6 Cyberpunk HUD: ui/main_window.py / ui_mark.py]
        FloatHUD[Floating HUD: float_widget.py]
        APIServer[FastAPI Server: server.py / api/]
    end

    subgraph Control Plane & Lifecycle
        Bootstrap[Unified Bootstrapper: core/bootstrap.py]
        DIContainer[Lightweight DI Container: core/di.py]
        Lifecycle[Lifecycle Manager: core/lifecycle.py]
        Orchestrator[Central Orchestrator: orchestrator/core.py]
        FastIntent[Deterministic Intent Matcher: core/intent_engine.py]
    end

    subgraph Model Gateway & Routing Plane
        ModelGateway[Unified Model Gateway: gateway/model_gateway.py]
        SmartRouter[Smart Router: router/smart_router.py]
        CircuitBreakers[Health & Quota Circuit Breakers: gateway/health.py]
        Adapters[Model Adapters: Gemini 2.5 / Claude 3.7 / DeepSeek / Ollama Local]
    end

    subgraph Tool & Workflow Execution Plane
        ToolRegistry[Universal Tool Registry: tools/registry.py]
        PolicyEngine[6-Tuple Policy Engine: security/policy_engine.py]
        PathPolicy[Path Tier Security: security/path_policy.py]
        DAGExecutor[Parallel DAG Engine: workflow/task_dag.py]
        ActionVerifier[Action Verifier: agent/verifier.py]
        Connectors[External Connectors: connectors/hub.py]
    end

    subgraph Unified Memory Plane
        MemoryManager[Unified Memory: memory/unified_memory.py]
        CoreDB[(Canonical DB: .jarvis/jarvis_core.db)]
        VectorStore[ChromaDB / SQLite Vectors: memory/vector_store.py]
    end

    subgraph Multimodal Peripherals
        VoiceLoop[Voice Engine: Silero VAD v5 + Faster-Whisper + Edge TTS]
        PerceptionRouter[Perception Router: Accessibility + CDP DOM + Win32 OCR + VLM]
        ComputerOp[OS Automation: computer/operator.py]
    end

    CLI --> Bootstrap
    GUI --> Bootstrap
    APIServer --> Bootstrap
    FloatHUD --> Bootstrap

    Bootstrap --> DIContainer
    DIContainer --> Orchestrator
    Lifecycle --> Orchestrator

    Orchestrator --> FastIntent
    Orchestrator --> SmartRouter
    SmartRouter --> ModelGateway
    ModelGateway --> CircuitBreakers
    CircuitBreakers --> Adapters

    Orchestrator --> ToolRegistry
    ToolRegistry --> PolicyEngine
    PolicyEngine --> PathPolicy
    PolicyEngine --> DAGExecutor
    DAGExecutor --> ActionVerifier
    DAGExecutor --> Connectors
    DAGExecutor --> ComputerOp

    Orchestrator --> MemoryManager
    MemoryManager --> CoreDB
    MemoryManager --> VectorStore

    Orchestrator --> VoiceLoop
    Orchestrator --> PerceptionRouter
```

---

## 3. Canonical Layer Responsibilities

| Layer / Subsystem | Canonical Path | Primary Invariant | Competing Systems Replaced / Deleted |
| :--- | :--- | :--- | :--- |
| **Bootstrapper** | `core/bootstrap.py` | Single thread-safe `AssistantRuntime` singleton | `core/bootstrapper.py`, `start.py` duplicate logic |
| **Model Gateway** | `gateway/model_gateway.py` | Multi-key rotation, error normalization, circuit breakers | Direct ad-hoc backend calling |
| **Model Router** | `router/smart_router.py` | Task-complexity, capability & health-aware ranking | Duplicate router branches |
| **Tool Registry** | `tools/registry.py` | Declarative schemas, 6-tuple policy validation | `actions/*` procedural scripts |
| **Memory Store** | `memory/canonical_db.py` | Unified SQLite WAL mode with `sqlite_lock.py` | 8 separate `.db`/`.json` storage files |
| **Voice Engine** | `voice/assistant.py` | Silero VAD v5 + local Whisper + streaming Edge TTS + barge-in | Multiple overlapping audio loops |
| **Vision Perception** | `vision/engine.py` | Cheapest-sufficient perception (A11y → CDP → OCR → VLM) | Standalone optical guessers |
| **Artifact Export** | `agent/artifacts.py` | Strict `sandbox_path != host_path` with SHA256 export | Direct unexported browser consumption |
| **Security Policy** | `security/policy_engine.py` | Deterministic 6-tuple: `(User, Device, App, Resource, Action, Risk)` | Ad-hoc regex sanitizers |
