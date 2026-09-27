# BR JARVIS — PRODUCTION TARGET ARCHITECTURE

## 1. Architectural Philosophy & Design Principles
The Target Architecture optimizes for a single-developer personal operating runtime:
1. **Zero Redundancy**: Exactly one canonical way to invoke models, execute tools, store memories, and bootstrap the runtime.
2. **Deterministic Security Boundary**: Untrusted input → Model Proposal → 6-Tuple Policy → Sandboxed Execution.
3. **Multimodal First**: Native real-time voice (VAD + Whisper + Streaming TTS) and instant screen perception.
4. **Single-Store Persistence**: All relational, episodic, contact, and preference state unified into `.jarvis/jarvis_core.db`.
5. **High Maintainability**: Modular components under 500 lines with clear interfaces and zero circular imports.

---

## 2. Target Layer Architecture

```mermaid
graph TD
    subgraph 1. Presentation Layer
        CLI[Unified CLI: brjarvis.py]
        GUI[PySide6 Cyberpunk GUI: ui/main_window.py]
        FloatWidget[Floating HUD: float_widget.py]
        APIServer[FastAPI Server: server.py -> api/routes/]
    end

    subgraph 2. Core Control Plane
        Bootstrapper[Canonical Bootstrapper: core/bootstrap.py]
        DIContainer[Lightweight DI Container: core/di.py]
        Orchestrator[Cognitive Brain: orchestrator/core.py]
        FastIntent[Fast-Path Intent Matcher: core/intent_engine.py]
    end

    subgraph 3. Model Gateway Plane
        ModelGateway[Unified Model Gateway: gateway/model_gateway.py]
        CircuitBreaker[Health & Rate-Limit Breaker: gateway/health.py]
        Providers[Adapters: Gemini 2.5 / Claude 3.7 / DeepSeek R1 / Local Ollama]
    end

    subgraph 4. Tool & Execution Plane
        ToolRuntime[Unified Tool Registry: tools/registry.py]
        SecurityGate[6-Tuple Policy Engine: security/policy_engine.py]
        DAGExecutor[Parallel DAG Engine: workflow/task_dag.py]
        Connectors[External Hub: connectors/hub.py]
    end

    subgraph 5. Unified Memory Plane
        MemoryManager[Unified Memory: memory/unified_memory.py]
        CoreDB[(Unified Database: .jarvis/jarvis_core.db)]
        VectorIndex[ChromaDB / NumPy SQLite Vectors: memory/vector_store.py]
    end

    subgraph 6. Multimodal Peripherals
        VoicePipeline[Voice Loop: Silero VAD v5 + Faster-Whisper + Edge TTS]
        VisionPipeline[Vision Loop: DXGI Screen Capture + Win32 UIAutomation + OCR]
        OSOperator[OS Automation: computer/operator.py]
    end

    CLI --> Bootstrapper
    GUI --> Bootstrapper
    APIServer --> Bootstrapper
    FloatWidget --> Bootstrapper
    
    Bootstrapper --> DIContainer
    DIContainer --> Orchestrator
    
    Orchestrator --> FastIntent
    Orchestrator --> ModelGateway
    ModelGateway --> CircuitBreaker
    CircuitBreaker --> Providers
    
    Orchestrator --> ToolRuntime
    ToolRuntime --> SecurityGate
    SecurityGate --> DAGExecutor
    SecurityGate --> Connectors
    SecurityGate --> OSOperator
    
    Orchestrator --> MemoryManager
    MemoryManager --> CoreDB
    MemoryManager --> VectorIndex
    
    Orchestrator --> VoicePipeline
    Orchestrator --> VisionPipeline
```

---

## 3. Key Upgrades Delivered in Target Architecture
- **Unified Gateway**: All LLM calls pass through `gateway/model_gateway.py` with automated multi-key rotation and zero-loss local fallback.
- **Action & Tool Consolidation**: `actions/` is refactored into declarative tools in `tools/` and external connectors in `connectors/`.
- **Database Unification**: All fragmented `.db` and `.json` state stores consolidated into `.jarvis/jarvis_core.db` with single-writer lock.
