# 🧠 BR JARVIS — Engineering Knowledge Base Index

Welcome to the **BR JARVIS (Project BR / JARVIS MK38)** Engineering Knowledge Base. This directory serves as the persistent architectural brain, technical documentation, and long-term design memory for the BR JARVIS AI Operating System (Version 38.0.0 / 227 unit tests 100% passing).

---

## 📁 Knowledge Base Hierarchy

```
br_architecture/
├── README.md                          # Root Knowledge Base index (This file)
├── fullproject.md                     # Master Full Project Specification & Architecture
├── PROJECT_VISION.md                  # Project BR vision, philosophy & objectives
├── ROADMAP.md                         # Multi-phase development roadmap & milestone status
├── CHANGELOG.md                       # Architectural execution changelog (v38.2.5 / v37.5.0)
├── full_repository_audit.md           # Deep engineering audit report & bug tracking (BUG-001 to BUG-018)
├── architecture/
│   ├── ARCHITECTURE.md                # System topology, data flow & component graph
│   └── PROJECT_STRUCTURE.md            # Codebase directory mapping (~180 Python files, 30+ packages)
├── planning/
│   ├── FEATURE_MATRIX.md              # Implemented capability status matrix (15 core subsystems)
│   ├── TECHNICAL_DEBT.md              # Refactoring targets & debt audit
│   └── TASKS.md                       # Active task backlog & fix priorities
├── ai/
│   ├── CONTEXT_ENGINE.md              # Context assembly, reference resolution & token compression
│   ├── MEMORY_ENGINE.md               # 5-tier memory architecture (Working, SQLite, Vector RAG, Lessons, Cache)
│   ├── MODEL_ROUTER.md                # Dynamic multi-backend router & failover strategies (7 AI backends)
│   └── TOKEN_OPTIMIZATION.md          # 50+ Zero-token intent engine & native FNV-1a caching
├── computer/
│   └── COMPUTER_OPERATOR.md           # OS computer operator, 5-tier clipboard & visual trace overlay
├── vision/
│   └── VISION_ENGINE.md               # 7-Tier Hybrid Vision Engine (Accessibility, CDP DOM, Tesseract OCR)
├── voice/
│   └── VOICE_ENGINE.md               # Hands-free voice assistant, Silero VAD, Whisper ASR & Neural TTS
├── plugins/
│   └── PLUGIN_SYSTEM.md               # Plugin platform, Antigravity Scratchpad (`./scratch/`) & tool registry
├── core/
│   └── EVENT_SYSTEM.md                # Pub/Sub EventBus, Conscious Step Planner & Telemetry Store
├── security/
│   └── SECURITY.md                    # Guardian Core, PathPolicy bounds checking, redteam audit & secret scan
├── ui_img/
│   ├── AI_OS_REDESIGN_MASTER_SPEC.md  # Maximum Control Center, Multi-Tasks tab & Task Cards spec
│   ├── UI_UX_DESIGN.md                # Tkinter HUD & glassmorphic Web UI specifications
│   └── redesign.md                    # Interface modernization roadmap & UI specs
├── upgrademd/
│   ├── BR_JARVIS_Master_Fix_Prompt.md  # Master system prompt & architecture directives
│   ├── BR_JARVIS_Master_Fix_Prompt_v2.md # Version 2 master system prompt & fix specs
│   ├── BR_JARVIS_UNIFIED_MASTER_PROMPT.md # Unified master prompt specification
│   ├── computervision.md               # Deep computer vision technical report
│   ├── deep-research-report.md         # Autonomous AI OS architecture research report (Part 1)
│   └── deep-research-report (1).md     # Autonomous AI OS architecture research report (Part 2)
└── performance/
    └── BENCHMARKS.md                  # Latency budgets, hardware metrics & test suite benchmarks
```

---

## 🚀 Key Architectural Innovations in MK38 (v38.2.5)

1. **Thread-Safe Runtime Singleton (`core/bootstrap.py`)**:
   - Thread-safe double-checked locking mechanism (`threading.Lock`) ensuring GUI, CLI, and Web Server share a unified working memory, router, and event bus.
2. **Permission System & Enforced Policy (`permissions.py` & `tools/registry.py`)**:
   - Implemented `CONFIRM_DESTRUCTIVE` permission mode with `DESTRUCTIVE_TOOLS` filter set and direct pre-execution checking in `execute_tool()`.
3. **Web Server Security Hardening (`server.py`)**:
   - Default localhost binding (`127.0.0.1`), explicit CORS origin whitelist, lifespan-deferred WebSocket log broadcasting, and `_CHAT_LOCK` thread serialization for API requests.
4. **Chat Stream Safety & Duplicate-Call Guard (`orchestrator/core.py`)**:
   - StepPlanner step budgeting, 4-call duplicate tool call detection/interception, and 4KB output truncation in streaming mode.
5. **PyAutoGUI Failsafe Protection (`actions/live_os_control.py` & `actions/game_updater.py`)**:
   - Default screen corner failsafe protection enabled by default, configurable via `JARVIS_DISABLE_FAILSAFE=true`.
6. **Input Sanitization & URL Scheme Protection (`core/intent_engine.py`)**:
   - Replaced `os.system()` with shell-free `subprocess.Popen()` and enforced URL scheme whitelisting (blocking `javascript:`, `file:`, `data:`, `vbscript:` schemes).
7. **Dynamic App Connector Telemetry (`server.py`)**:
   - Real-time status lookup against `TOOL_REGISTRY` returning `CONNECTED` or `NOT_CONFIGURED` based on registered tool functions.
8. **Centralized API Key Resolution (`config/__init__.py`)**:
   - Single authoritative `get_gemini_api_key()` utility consumed by backends, memory, and actions.
9. **Meta-Cognition Engine & Pre-Execution Risk Assessment (`reasoning/meta_cognition.py`)**:
   - Evaluates goal confidence ($0.0 \text{ to } 1.0$), CoT step depth, missing context, and risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with destructive action interception.
10. **Speculative Drafting & Execution Engine (`reasoning/speculative.py`, `orchestrator/speculative.py`)**:
   - Generates speculative draft tool calls using fast deterministic rules and parallel validation, accelerating tool execution loops by up to 60%.
11. **Trajectory Experience Replay Database (`memory/experience_replay.py`)**:
   - SQLite WAL database persisting execution trajectories (`trajectory_id`, `goal_query`, `success_status`, `step_count`, `tool_sequence`, `failure_reason`) and similarity pattern retrieval (`get_similar_failures()`).
12. **Temporal Knowledge Graph 2.0 (`memory/temporal_kg.py`)**:
   - Time-stamped relational edge world model $(e_1, r, e_2, t_{\text{start}}, t_{\text{end}})$ supporting point-in-time snapshot queries (`query_as_of`).

---

## 🌟 Essential Reading Order for AI Agents & Developers

1. [fullproject.md](fullproject.md) — Master Full Project Architecture Specification
2. [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) — Core system topology & data flow
3. [architecture/PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md) — Directory mapping & module index
4. [full_repository_audit.md](full_repository_audit.md) — Deep engineering audit report & bug tracking
5. [voice/VOICE_ENGINE.md](voice/VOICE_ENGINE.md) — VoicePromptRefiner, ASR & Neural TTS
6. [ai/MEMORY_ENGINE.md](ai/MEMORY_ENGINE.md) — 5-Tier Memory Subsystem
7. [computer/COMPUTER_OPERATOR.md](computer/COMPUTER_OPERATOR.md) — OS Desktop Operator & Clipboard Utility
