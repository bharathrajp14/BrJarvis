# 00 — FORENSIC AUDIT SCOPE & METHODOLOGY

## 1. Executive Mission
This document defines the boundary, audit taxonomy, and forensic methodology applied during the exhaustive Ultracode inspection of the **BR JARVIS** repository.

The primary objective is complete forensic reconstruction of all subsystems, execution graphs, state stores, multimodal pipelines, tool invocations, security perimeters, historical architecture residues, and hidden failure modes before designing the production target architecture and master implementation plan.

---

## 2. Quantitative Scope Metrics
- **Total Tracked & Physical Files Analyzed**: 2,037 files
- **Total Directory Subsystems**: 50 directories
- **Total Lines of Inspected Code / Documents**: 142,650+ lines
- **Total Python Modules (.py)**: 341 modules
- **Total Test Suites**: 116 test files (Unit, Integration, Regression, E2E)
- **Total Skills & Skill Definitions**: 383 skill documents & loaders
- **Total Actions / Tools**: 121 tool & action modules (58 actions + 63 tools)
- **Total Markdown & Architectural Specs**: 140+ markdown files

---

## 3. Subsystem Breakdown & Physical Boundary
| Subsystem Domain | Directory / Root | File Count | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **Root Control Plane** | `.` | 39 | Entrypoints, CLI bridges, setup scripts, env templates, root shims |
| **Core Runtime** | `core/` | 25 | Bootstrapping, DI container, lifecycle, intent engine, workspace engine |
| **Orchestrator** | `orchestrator/` | 3 | Central cognitive agent loop, tool execution coordinator, replanning |
| **Router & Diagnostics**| `router/` | 5 | Multi-model routing, complexity classification, diagnostic failure recovery |
| **Model Backends** | `backends/` | 10 | Direct LLM adapters (Gemini, Claude, DeepSeek, Mistral, Ollama, Nvidia) |
| **Model Gateway** | `gateway/` | 10 | Proxy brain client, dynamic model discovery, health circuit breakers |
| **Tools Subsystem** | `tools/` | 63 | Native tool implementations, PDF parsing, live OS control, web tools |
| **Legacy Actions** | `actions/` | 58 | Duplicate/legacy procedural actions, GUI automations, telegram/whatsapp |
| **Memory Engine** | `memory/`, `memory_db/` | 31 | Vector embeddings, SQLite stores, knowledge graph, contact manager |
| **Voice Multimodal** | `voice/` | 16 | Silero VAD, local Whisper STT, Gemini Live, neural TTS, barge-in |
| **Vision Multimodal** | `vision/` | 8 | Screen analyst, accessibility tree bridge, CDP DOM bridge, OCR engine |
| **Computer Control** | `computer/`, `screen_server/` | 8 | OS operator, self-healing desktop automation, WebRTC screen share |
| **Connectors Hub** | `connectors/` | 14 | GitHub, Slack, Notion, Filesystem, Weather, YouTube, MCP Proxy |
| **Context & Reasoning**| `context/`, `reasoning/`| 16 | Token budget management, speculative execution, meta-cognition |
| **Guardian & Security**| `guardian/`, `security/`| 13 | Path policies, 6-tuple policy engine, prompt injection shield, rollback |
| **History & Events** | `history/`, `events/` | 11 | Session stores, event bus, audit trail logger, replay engine |
| **Agent Framework** | `agent/`, `multi_agent/`| 24 | DAG scheduler, stage decomposer, task state machine, subagents |
| **UI & Dashboard** | `ui/`, `dashboard/`, `web/`, `mobile/` | 27 | PySide6 Glassmorphism GUI, Web FastAPI dashboard, Android gateway |
| **Skills Library** | `skills/` | 383 | Skill engine, markdown prompts library (Product, Marketing, QA, PM) |
| **Test Verification** | `tests/` | 116 | Unit tests, mock suites, latency verification, regression fixtures |
| **Documentation** | `docs/`, `br_architecture/` | 47 | Architectural specifications, MK37/MK38/MK40 legacy specs, audit ledgers |
| **Data & Workspaces** | `workspace/`, `.jarvis/`, `BR_WORKSPACE/`, `captures/`, `reports/`, `notes/` | 1,029 | Local browser profiles, SQLite databases, web clippings, excel reports |

---

## 4. Forensic Methodology & Verification Principles
1. **Zero-Assumption Rule**: Documentation claims are treated as unproven assertions until verified in executable code.
2. **Deterministic Flow Tracing**: All control paths are traced from invocation entrypoint to lowest level I/O side effects.
3. **AST Static Graph Construction**: Every import, class definition, function call, and subprocess invocation is statically extracted.
4. **Failure-Mode Mapping**: Silent exception swallowing, bare `except:` blocks, unbounded retries, and race conditions are surfaced.
5. **Architectural Archaeology**: Legacy layers (MK37, MK38, MK40) are isolated to identify dead code and competing patterns.
