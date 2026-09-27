# 📊 BR JARVIS — Feature Capability Matrix

> **Document Status**: Production Architecture Specification  
> **Scope**: Implementation Status across Core Subsystems  
> **Version**: MK38.2.0  

---

## Subsystem Capability Matrix

| Subsystem | Feature | Status | Module Path |
|---|---|---|---|
| **Meta-Cognition Engine** | Pre-Execution Risk Assessment & Confidence Evaluation | ✅ Production | `reasoning/meta_cognition.py` |
| **Speculative Execution** | Speculative Draft Generation & Parallel Validation | ✅ Production | `reasoning/speculative.py` & `orchestrator/speculative.py` |
| **Experience Replay DB** | SQLite WAL Goal Trajectory Recording & Similarity Search | ✅ Production | `memory/experience_replay.py` |
| **Temporal Knowledge Graph 2.0** | Time-Stamped Relational Edges & Point-in-Time Queries | ✅ Production | `memory/temporal_kg.py` |
| **Workspace Code Graph** | Zero-Token AST Code Symbol Definition & Reference Resolution | ✅ Production | `workspace/code_graph.py` |
| **Cognitive Loop** | Observe -> Think -> Critic -> Improve -> Retry Cycle | ✅ Production | `reasoning/cognitive_loop.py` |
| **Critic Sub-Agent** | Autonomous Quality & Security Reviewer | ✅ Production | `agent/critic_agent.py` |
| **Knowledge Graph** | Relational NetworkX World Model Entity Graph | ✅ Production | `memory/knowledge_graph.py` |
| **Task DAG Storage** | Persistent SQLite WAL Task Checkpointing & Resume | ✅ Production | `workflow/task_dag.py` |
| **Multi-Objective Router** | Utility Optimization (Quality, Cost, Latency) | ✅ Production | `router.py` |
| **Memory Decay Engine** | Ebbinghaus Retention Decay & Pruning | ✅ Production | `memory/decay.py` |
| **Task Scheduler** | Async Task DAG Scheduler & Worker Dispatcher | ✅ Production | `agent/task_scheduler.py` |
| **Event Watchers** | Workspace File & OS Telemetry Watchers | ✅ Production | `watchers/` |
| **Swarm Subsystem** | Hierarchical Multi-Agent Collaboration | ✅ Production | `multi_agent/swarm.py` |
| **Voice Subsystem** | ONNX Silero Voice Activity Detector (<10ms) | ✅ Production | `voice/silero_vad.py` |
| **Voice Subsystem** | Zero-Disk In-Memory Whisper Byte Streaming | ✅ Production | `voice/whisper_local.py` |
| **Vision Subsystem** | Tier 2 CDP Chrome/Edge Browser DOM Bridge | ✅ Production | `vision/dom_bridge.py` |
| **Core Runtime** | 50+ Zero-Token Intent Engine | ✅ Production | `core/intent_engine.py` |
| **Core Runtime** | Thread-safe DI Container | ✅ Production | `core/di_container.py` |
| **Core Runtime** | Native C FNV-1a Bridge | ✅ Production | `native/jarvis_native.c` |
| **Scratchpad Subsystem** | Isolated `./scratch/` Execution Workspace | ✅ Production | `agent/scratchpad.py` |
| **Scratchpad Tools** | 5 Scratchpad Tools (Write/Read/Eval/List/Clear) | ✅ Production | `tools/scratchpad_tools.py` |
| **Planning Mode** | Dynamic Complexity Classifier & Plan Generator | ✅ Production | `agent/planning_mode.py` |
| **Artifact Engine** | GFM Alerts, Mermaid Diagrams & file:/// Links | ✅ Production | `agent/artifacts.py` |
| **Transcripts Engine** | JSON Lines Trajectory Transcripts Logging | ✅ Production | `agent/transcript_logger.py` |
| **Voice Subsystem** | VoicePromptRefiner & Vocal Filler Cleaner | ✅ Production | `voice/prompt_refiner.py` |
| **Voice Subsystem** | Real-time Raw vs Refined Prompt UI Log | ✅ Production | `voice/prompt_refiner.py` |
| **Frontend UI** | Multi-Task Dashboard & Glossy Task Cards | ✅ Production | `ui.py` |
| **Frontend UI** | Canvas Multi-Task HUD Banner & Progress Bars | ✅ Production | `ui.py` |
| **Step Planner** | Conscious Sub-Step Decomposition | ✅ Production | `agent/step_planner.py` |
| **Step Planner** | AdaptiveStepBudget & Progress Velocity Extensions | ✅ Production | `agent/step_planner.py` |
| **Clipboard Engine** | Multi-Backend 5-Tier Fallback Clipboard | ✅ Production | `actions/clipboard_utils.py` |
| **Guardian Core** | KillSwitch & Pause Controller | ✅ Production | `guardian/kill_switch.py` |
| **Guardian Core** | SHA-256 Integrity Verification | ✅ Production | `guardian/integrity.py` |
| **Guardian Core** | Pre-Upgrade Snapshot Manager | ✅ Production | `guardian/snapshot.py` |
| **Guardian Core** | Automated Rollback Engine | ✅ Production | `guardian/rollback.py` |
| **Guardian Core** | PathPolicy Path Bounds Checking | ✅ Production | `guardian/path_policy.py` |
| **Reflection Engine** | Implicit & Explicit Correction Capture | ✅ Production | `memory/reflection.py` |
| **Lesson Store** | Priority 6 Context Integration | ✅ Production | `memory/lessons.py` |
| **Self-Upgrade Engine** | Blast-Radius ChangeClassifier | ✅ Production | `evolution/classifier.py` |
| **Self-Upgrade Engine** | PatchProposer & ChangeDigest | ✅ Production | `evolution/` |
| **Self-Upgrade Engine** | SandboxRunner Verification | ✅ Production | `evolution/sandbox.py` |
| **Self-Upgrade Engine** | AutoDeployer Pipeline | ✅ Production | `evolution/deployer.py` |
| **Reasoning & Planning** | ReAct CoT Plan Engine | ✅ Production | `reasoning/engine.py` |
| **Workflow Engine** | Durable SQLite DAG Scheduler | ✅ Production | `workflow/engine.py` |
| **Agent Executor** | Parallel Multi-Worker Execution | ✅ Production | `agent/executor.py` |
| **Multi-Agent Orchestra** | 12 Specialized SubAgents | ✅ Production | `multi_agent/subagent.py` |
| **Multi-LLM Router** | 7 Backends with Auto-Failover | ✅ Production | `router.py` |
| **Backends** | Gemini (3.6 Flash & Agent), Claude, GPT, Ollama, DeepSeek, NIM, Mistral | ✅ Production | `backends/` |
| **Context Engine** | Priority Windowing & Pronoun Resolution | ✅ Production | `context/` & `orchestrator.py` |
| **Memory Engine** | 6-Tier Volatile/SQLite/Vector/Lesson/KG/Decay Memory | ✅ Production | `memory/` |
| **Computer Control** | PyAutoGUI + Precise Coordinate Execution | ✅ Production | `computer/` |
| **Vision Engine** | 7-Tier Hybrid Pipeline (Accessibility, DOM, OCR) | ✅ Production | `vision/` |
| **Voice Subsystem** | Silero VAD + Zero-Disk Whisper + Neural TTS | ✅ Production | `voice/` |
| **Tool Ecosystem** | 34 Tool Modules & `@register_tool` | ✅ Production | `tools/` |
| **Context Resolver** | Anaphoric Pronoun & History Resolver | ✅ Production | `orchestrator._resolve_context_references` |
| **Live OS Control** | Visual Action Target Trace (Red Crosshair) | ✅ Production | `actions/live_os_control.py` |
| **Verification Suite** | 102-Test Automated Unit & Integration Suite | ✅ Production | `tests/` |
