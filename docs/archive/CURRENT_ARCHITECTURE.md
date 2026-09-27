# BR JARVIS — CURRENT ARCHITECTURE SPECIFICATION

## 1. Executive Summary
BR JARVIS is an autonomous personal AI operating runtime and multimodal desktop assistant built for Windows (with Linux compatibility). It provides low-latency voice interaction, deep desktop automation, multi-provider LLM routing, and structured DAG workflow execution.

---

## 2. Current Subsystem Topology
```mermaid
graph TD
    subgraph Client & Presentation Layer
        CLI[Unified CLI: brjarvis.py]
        GUI[PySide6 HUD: ui_mark.py / ui/main_window.py]
        FloatHUD[Floating Widget: float_widget.py]
        WebDash[Web Dashboard: dashboard/server.py]
        API[FastAPI Gateway: server.py / api/]
    end

    subgraph Control Plane & Lifecycle
        Bootstrap[Bootstrap: core/bootstrap.py / start.py]
        Container[DI Container: core/di.py]
        Intent[Deterministic Intent Engine: core/intent_engine.py]
        Orchestrator[Central Orchestrator: orchestrator/core.py]
    end

    subgraph Reasoning & Model Routing
        Router[Router Engine: router/core.py & router/smart_router.py]
        Gateway[Model Gateway: gateway/model_gateway.py]
        Backends[Adapters: Gemini / Claude / DeepSeek / Ollama / Mistral]
    end

    subgraph Execution & Security Plane
        AgentExecutor[Agent Task Executor: agent/executor.py]
        DAGExecutor[Parallel DAG Scheduler: workflow/task_dag.py]
        PolicyEngine[6-Tuple Policy Engine: security/policy_engine.py]
        PathPolicy[Tiered Path Policy: security/path_policy.py]
        ToolsRegistry[Tool Schemas: tools/ & actions/ & connectors/]
    end

    subgraph Memory & State Persistence
        UnifiedMem[Unified Memory: memory/unified_memory.py]
        VectorDB[ChromaDB / SQLite: memory/vector_store.py]
        ContactDB[Encrypted Contacts: memory/contact_manager.py]
        SessionStore[Session DB: history/session_store.py]
    end

    subgraph Multimodal Peripherals
        VoiceAssistant[Voice Loop: voice/assistant.py / Silero VAD / Faster-Whisper / Edge-TTS]
        VisionPipeline[Vision Loop: vision/screen_analyst.py / OCR / Win32 Accessibility / CDP]
        ComputerOp[OS Automation: computer/operator.py / PyAutoGUI]
    end

    CLI --> Bootstrap
    GUI --> Bootstrap
    API --> Bootstrap
    Bootstrap --> Container
    Container --> Orchestrator
    
    Orchestrator --> Intent
    Orchestrator --> Router
    Router --> Gateway
    Gateway --> Backends
    
    Orchestrator --> AgentExecutor
    AgentExecutor --> DAGExecutor
    AgentExecutor --> PolicyEngine
    PolicyEngine --> PathPolicy
    PolicyEngine --> ToolsRegistry
    
    Orchestrator --> UnifiedMem
    UnifiedMem --> VectorDB
    UnifiedMem --> ContactDB
    UnifiedMem --> SessionStore
    
    Orchestrator --> VoiceAssistant
    Orchestrator --> VisionPipeline
    AgentExecutor --> ComputerOp
```

---

## 3. Discovered Architectural Flaws & Inconsistencies
1. **Triplicate Model Execution Paths**: Coexistence of `backends/`, `gateway/`, and `router/smart_router.py`.
2. **Duplicated Tool & Action Systems**: 58 procedural scripts in `actions/` run in parallel with 63 schema tools in `tools/`.
3. **Fragmented Storage State**: 8 independent SQLite and JSON stores across `.jarvis/`, `memory_db/`, and `memory/`.
4. **Monolithic Intent Engine**: `core/intent_engine.py` is 1,811 lines with hardcoded application mappings.
