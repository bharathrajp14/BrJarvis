# 📂 Codebase Directory Mapping & Module Responsibilities

> **System**: BR JARVIS (MK37.31.0)  
> **Scale**: ~180 Python files across 30 top-level packages.

---

## 1. Directory Tree & Module Mapping

```
Br-Jarvis/
├── actions/                   # OS automation (browser, desktop, apps, games, file ops)
│   ├── clipboard_utils.py     # 5-tier prioritized clipboard fallback engine
│   ├── live_os_control.py     # LLM screenshot action execution & visual trace overlays
│   └── ...                    # 34 action modules
├── agent/                     # Autonomous planning & execution pipeline
│   ├── artifacts.py           # GFM Artifact Engine (implementation_plan.md, walkthrough.md)
│   ├── critic_agent.py        # Autonomous Critic & Verifier Sub-Agent
│   ├── executor.py            # GoalGraph worker execution pool
│   ├── planner.py             # Plan DAG generator & complexity evaluation
│   ├── planning_mode.py       # Autonomous Planning Mode logic (`warrants_plan`)
│   ├── scratchpad.py          # Antigravity Scratchpad workspace evaluator (`./scratch/`)
│   ├── step_planner.py        # Conscious Step Planner & AdaptiveStepBudget controller
│   ├── task_scheduler.py      # Async Task DAG scheduler & worker dispatcher
│   └── transcript_logger.py   # Trajectory JSON Lines transcript logger (`transcript.jsonl`)
├── backends/                  # AI Provider Adapters (Gemini, Claude, GPT, Ollama, DeepSeek, NVIDIA, Mistral)
├── br_architecture/            # Persistent Engineering Knowledge Base index & specifications
├── computer/                  # Desktop operator & OS window management
│   ├── operator.py            # PyAutoGUI desktop operator & win32 handle manager
│   ├── recovery.py            # Self-healing popup recovery engine
│   ├── semantic_operator.py   # UI node dynamic finder
│   └── types.py               # Action, coordinate, and target models
├── config/                    # Configuration settings, key maps, vocabulary.json
├── context/                   # Context assembly, sliding windows, reference resolution
├── core/                      # Core runtime, DI container, retry, intent engine, error middleware
│   └── intent_engine.py       # 50+ zero-token instant deterministic intent matchers
├── events/                    # Asynchronous Pub/Sub EventBus & event models
├── evolution/                 # Self-upgrade sandbox, classifier, proposer, deployer
├── guardian/                  # PathPolicy bounds check, kill-switch, snapshot, rollback
├── history/                   # Session store, replay engine, transcript writer
├── memory/                    # 8-tier memory subsystem (Working, SQLite, Vector RAG, Lessons, Cache, KnowledgeGraph, ExperienceReplay, TemporalKG)
│   ├── decay.py               # Ebbinghaus memory retention decay & pruner
│   ├── experience_replay.py   # Trajectory Experience Replay SQLite WAL database
│   ├── knowledge_graph.py     # Relational NetworkX world model entity graph
│   └── temporal_kg.py         # Time-stamped Temporal Knowledge Graph 2.0
├── multi_agent/               # Sub-agent spawning framework (12 subagent definitions & hierarchical swarm)
│   └── swarm.py               # Hierarchical multi-agent collaboration engine
├── reasoning/                 # Meta-cognition, speculative drafting & cognitive loops
│   ├── cognitive_loop.py      # Closed Observe-Think-Critic-Improve-Retry loop
│   ├── meta_cognition.py      # MetaCognitionEngine pre-execution risk evaluator
│   └── speculative.py         # SpeculativeExecutionEngine parallel step validator
├── workspace/                 # Workspace AST code intelligence graph
│   └── code_graph.py          # WorkspaceCodeGraph zero-token symbol definition indexer
├── native/                    # Win32 C native bridge (`jarvis_native.c`)
├── plugins/                   # Plugin platform & isolation manager
├── reasoning/                 # Chain-of-Thought engine, plan graph DAG, cognitive loop
│   └── cognitive_loop.py      # Observe -> Think -> Critic -> Improve -> Retry cognitive loop
├── redteam/                   # Recon scanner, security auditor, scope manager
├── screen_server/             # Real-time WebSocket screen share server
├── skills/                    # Skill loader & builtins (RAG, Auditor, Writer, Excel)
├── tools/                     # Tool registry & 34 tool modules (scratchpad_tools, browser_tools, etc.)
├── vision/                    # 7-tier hybrid vision engine (Accessibility API, CDP DOM bridge, OCR)
│   └── dom_bridge.py          # CDP Chrome/Edge DevTools Protocol browser DOM bridge
├── voice/                     # Voice system (Silero VAD, Whisper ASR, Neural TTS, prompt refiner, wake word)
│   ├── silero_vad.py          # Fast ONNX Silero Voice Activity Detector (<10ms)
│   ├── whisper_local.py       # In-memory zero-disk Whisper byte streaming & RMS silence gate
│   └── prompt_refiner.py      # VoicePromptRefiner vocal filler cleaner & vocabulary mapper
├── watchers/                  # Event-driven background watchers (file_watcher, system_watcher)
├── web/                       # Glassmorphic PWA Web UI dashboard (HTML/CSS/JS)
├── workflow/                  # Durable workflow DAG engine & persistent Task DAG store
│   └── task_dag.py            # SQLite WAL atomic step checkpointing & crash resume
├── floating_voice_ui.py       # Gemini Live floating overlay UI
├── main_mk37.py               # Rich TUI CLI launcher
├── orchestrator.py            # Core ReAct reasoning & execution loop
├── permissions.py             # Security policy & permission matrix
├── router.py                  # Dynamic multi-backend AI model router
├── server.py                  # FastAPI REST & WebSocket server
├── start.py                   # System entry point launcher
└── ui.py                      # Tkinter Maximum Control Center HUD (72KB monolith)
```
