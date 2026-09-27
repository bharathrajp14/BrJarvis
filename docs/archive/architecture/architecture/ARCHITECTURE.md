# 🏗️ Core System Topology & Architecture Graph

> **System**: BR JARVIS (MK38.2.0)  
> **Target Scope**: End-to-end component graph, event flow, and data pipelines.

---

## 1. High-Level Subsystem Topology

```mermaid
graph LR
    subgraph CoreEngine["Core Engine & Event Bus"]
        Bootstrap[Bootstrap / DI Container<br/>core/bootstrap.py]
        EventBus[Async EventBus<br/>events/event_bus.py]
        IntentEngine[0-Token Intent Engine<br/>core/intent_engine.py]
    end

    subgraph CognitiveLayer["Cognitive Layer"]
        MetaCognition[MetaCognitionEngine<br/>reasoning/meta_cognition.py]
        SpeculativeEngine[SpeculativeExecutionEngine<br/>reasoning/speculative.py]
        StepPlanner[Conscious Step Planner<br/>agent/step_planner.py]
        CognitiveLoop[Closed Cognitive Loop<br/>reasoning/cognitive_loop.py]
        CriticAgent[Critic & Verifier<br/>agent/critic_agent.py]
        Orchestrator[ReAct Orchestrator Coordinator<br/>orchestrator.py]
        Router[Multi-Objective Router<br/>router.py]
    end

    subgraph WorldModelLayer["World Model & Memory"]
        ExperienceReplay[ExperienceReplayStore<br/>memory/experience_replay.py]
        TemporalKG[TemporalKnowledgeGraph<br/>memory/temporal_kg.py]
        WorkspaceCodeGraph[WorkspaceCodeGraph<br/>workspace/code_graph.py]
        KnowledgeGraph[NetworkX Knowledge Graph<br/>memory/knowledge_graph.py]
        MemoryDecay[Ebbinghaus Memory Decay<br/>memory/decay.py]
        TaskDAGStore[Persistent Task DAG Store<br/>workflow/task_dag.py]
    end

    subgraph PerceptionLayer["Perception Layer"]
        SileroVAD[Silero VAD ONNX<br/>voice/silero_vad.py]
        VoiceRefiner[VoicePromptRefiner<br/>voice/prompt_refiner.py]
        EventWatchers[Event-Driven Watchers<br/>watchers/]
        HybridVision[7-Tier Hybrid Vision<br/>vision/hybrid_pipeline.py]
        Accessibility[Windows Accessibility API<br/>vision/accessibility.py]
        DOMBridge[CDP Browser DOM Bridge<br/>vision/dom_bridge.py]
    end

    subgraph ExecutionLayer["Execution Layer"]
        SwarmCollab[Multi-Agent Swarm<br/>multi_agent/swarm.py]
        ComputerOp[Computer Operator<br/>computer/operator.py]
        Scratchpad[Antigravity Scratchpad<br/>agent/scratchpad.py]
        Tools[Tool Registry (98 Tools)<br/>tools/registry.py]
        Clipboard[5-Tier Clipboard Utility<br/>actions/clipboard_utils.py]
    end

    VoiceRefiner --> IntentEngine
    IntentEngine --> |Fast Path| ExecutionLayer
    IntentEngine --> |LLM Path| StepPlanner
    StepPlanner --> Orchestrator
    Orchestrator --> Router
    Orchestrator --> Reasoning
    Orchestrator --> EventBus
    Orchestrator --> ExecutionLayer
    ExecutionLayer --> HybridVision
    HybridVision --> Accessibility
    HybridVision --> DOMBridge
```

---

## 2. ReAct Execution Flow & Data Pipeline

1. **Input Interception**: Spoken audio or text input is refined by `VoicePromptRefiner` (stripping vocal fillers) and evaluated against `DeterministicIntentEngine`.
2. **Step Decomposition**: Complex requests are decomposed into conscious steps by `StepPlanner` (`agent/step_planner.py`).
3. **Context Reference Resolution**: `orchestrator._resolve_context_references()` resolves URLs, file paths, and browser targets against short-term working memory.
4. **Adaptive Execution Loop**: `JarvisOrchestrator` runs the ReAct loop within an `AdaptiveStepBudget` (dynamic 5–35 steps + progress velocity extensions up to 60 ceiling).
5. **Tool Execution & Grounding**: Tool calls execute via `tools/registry.py` or isolated `./scratch/` scripts (`scratchpad_eval`). Visual action traces are recorded to `BR_WORKSPACE/Logs/live_os/`.
6. **Trajectory Transcript Logging**: Every step, tool call, and thought is appended to JSON Lines transcripts (`transcript.jsonl`).
