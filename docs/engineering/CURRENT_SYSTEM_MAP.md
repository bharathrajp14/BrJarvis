# BRJARVIS // CURRENT SYSTEM MAP
**Audit Date:** 2026-09-27  
**Scope:** Full repository comprehensive architecture and inventory  
**Status:** Live Ground Truth Verified  

---

## 1. Executive System Summary

BRJARVIS is a local-first, multimodal, persistent personal AI operating system. The codebase is currently structured in a **strangler migration** architecture:
- `src/brjarvis/`: The operational production runtime containing 200 tools, FastAPI web services, live OS and desktop automation, voice pipelines, and Career OS.
- `src/jarvis/`: The clean canonical target package implementing strict protocols, Pydantic v2 domain schemas, SQLite WAL storage with serialized locking, and a provider-neutral model gateway.
- `frontend/`: React 19 + TypeScript + Vite control plane interface compiled to `src/brjarvis/web/static/dist/`.
- `tests/`: 89 test files with 402 passing automated tests across unit, integration, smoke, e2e, and adversarial suites.

---

## 2. Codebase Topology & File Distribution

| Top-Level Directory | File Count | Lines of Code | Description |
| :--- | :--- | :--- | :--- |
| `src/` | 1,204 | 293,007 | Production Python runtime (`brjarvis` and `jarvis`) |
| `docs/` | 295 | 807,871 | Architecture specifications, decision log, archived records |
| `runtime/` | 2,128 | 452,229 | Runtime telemetry, logs, state files, captures |
| `workspace/` | 34 | 73,191 | User projects, documents, resumes, and career profiles |
| `audit/` | 56 | 57,906 | Forensic audit logs, baseline outputs, slice verification logs |
| `.jarvis/` | 279 | 12,533 | Local configuration, credentials, scheduled tasks, keys |
| `tests/` | 89 | 8,793 | Pytest test suites (Unit, Integration, E2E, Smoke, Adversarial) |
| `config/` | 24 | 4,283 | Gateway, model brain, app path manifests, and release policies |
| `scripts/` | 33 | 3,540 | Audit tooling, model benchmark probes, reachability analysis |
| `frontend/` | 21 | 3,249 | Modern React 19 control plane source code |
| `apps/` | 10 | 891 | Web application server launch shims |

---

## 3. Subsystem Breakdown (`src/brjarvis/` & `src/jarvis/`)

### 3.1 `src/brjarvis` (Operational Runtime)
- **`skills/` (382 files, 86,310 LOC):** Massive repository of specialized `SKILL.md` workflows covering research, document generation, coding, automation, and system diagnostics.
- **`workspace/` (272 files, 78,068 LOC):** Internal workspace file processors, timeline manager, and document renderers.
- **`tools/` (69 files, 15,648 LOC):** 200 registered tools implementing filesystem operations, Office/PDF document creation, web search, system telemetry, and contact management.
- **`actions/` (52 files, 15,137 LOC):** Specialized execution engines, including `LiveOSController` for screen capture, visual grid overlays, mouse/keyboard manipulation, and code execution.
- **`core/` (41 files, 14,719 LOC):** `ApplicationRuntime` composition root, `Container` dependency injection, `ProcessSupervisor`, `HealthMonitor`, and `LifecycleManager`.
- **`career/` (63 files, 12,315 LOC):** Career OS with canonical profile model, ATS scoring, resume generator, and job search adapters.
- **`web/` (40 files, 10,398 LOC):** FastAPI application with REST endpoints (`/api/v1/auth`, `/api/v1/tasks`, `/api/v1/memory`, `/api/v1/workspace`, `/api/v1/artifacts`, `/health`) and WebSocket real-time event streaming (`/api/v1/ws`).
- **`memory/` (30 files, 8,515 LOC):** `UnifiedMemoryManager`, `CanonicalMemoryStore`, `VectorMemory` (ChromaDB / text similarity fallback), and SQLite storage.
- **`agent/` (21 files, 7,829 LOC):** `AgentLoop` iterative ReAct turn coordinator, transcript loggers, and turn result synthesizers.
- **`voice/` (17 files, 5,315 LOC):** `VoiceStateMachine`, Edge-TTS speech generation, Google Speech Recognition listener, and optional PySide6 voice HUD.
- **`ui/` (7 files, 4,562 LOC):** Desktop floating widget and HUD interface.
- **`connectors/` (17 files, 4,210 LOC):** Integration hub for Gmail, Telegram, WhatsApp, Slack, Notion, and GitHub.
- **`gateway/` (10 files, 2,880 LOC):** Client proxy connector, benchmark probes, and multi-tier model dispatcher.
- **`integrations/` (18 files, 2,446 LOC):** Backend adapters for Google Gemini, OpenAI-compatible servers, and Ollama.
- **`guardian/` (14 files, 1,091 LOC):** Security perimeter, prompt injection shield, kill switch, and file integrity validation.

### 3.2 `src/jarvis` (Canonical Clean Package)
- **`core/` (9 files, 518 LOC):** Clean `AssistantRuntime`, path layout, logging, and startup doctor.
- **`gateway/` (13 files, 862 LOC):** Provider-neutral `ModelGateway` with protocol adapters: `ClaudeAdapter`, `GeminiAdapter`, `OpenAIAdapter`, `OllamaAdapter`.
- **`tools/` (8 files, 604 LOC):** Strict `ToolRegistry`, typed `ToolContract`, and `ToolResult` structures.
- **`memory/` (5 files, 492 LOC):** SQLite WAL `Database` with serial write lock, `TaskRepository`, `SessionRepository`, and `TemporalMemory`.
- **`agent/` (8 files, 744 LOC):** Bounded `AgentLoop`, `TaskState` machine (14 validated states), `ExecutionLedger`, and `TaskVerifier`.
- **`surfaces/` (10 files, 384 LOC):** Decoupled CLI, desktop voice surface, and web server routes.

---

## 4. Entry Points & Runtime Composition

| Entry Point | Target | Purpose | Status |
| :--- | :--- | :--- | :--- |
| `start.py` | CLI multi-dispatcher | Master launcher supporting `doctor`, `server`, `cli`, `voice`, `test` | Active |
| `server.py` | ASGI Uvicorn | Starts the FastAPI web control plane server on port 8000 | Active |
| `brjarvis.apps.cli` | `main()` | Interactive terminal REPL with command routing | Active |
| `brjarvis.apps.bootstrap`| `main()` | Interactive terminal menu and supervisor | Active |
| `brjarvis.apps.web` | `main()` | Web server application runner | Active |
| `brjarvis.ui.widgets` | PySide6 | Desktop floating widget and HUD | Optional Extra |
| `brjarvis.voice.assistant`| Background worker | Hands-free continuous voice assistant daemon | Optional Extra |

**Composition Root Wiring:**
1. `brjarvis.core.runtime.ApplicationRuntime` creates the central service locator.
2. Injects `JarvisConfig`, `EventBus`, `LifecycleManager`, `HealthMonitor`, and `ProcessSupervisor`.
3. Bridges to `jarvis.gateway.factory.build_configured_gateway()` for unified model access.
4. Lazy-initializes `JarvisOrchestrator`, `ToolRuntime`, `UnifiedMemoryManager`, and `GuardianCore`.

---

## 5. Model Gateway & Provider Tiering

The model gateway is configured via `config/ai_gateway.yaml` and `config/models.yaml`:
- **Tier 1 (Primary):** Local OmniRouter Proxy at `http://127.0.0.1:20128/v1` (serves `antigravity/gemini-3.7-flash-high`, `kr/claude-sonnet-4.5`, and auto-routing pools).
- **Tier 2 (Secondary):** OpenRouter API (`https://openrouter.ai/api/v1`) using verified free-tier models when Tier 1 is on cooldown.
- **Tier 3 (Local / Private):** Local Ollama runtime (`http://127.0.0.1:11434`) for 100% offline, privacy-critical queries.

---

## 6. Tool Registry Topology

- **Registration Pattern:** Global decorator-based registration with lazy-loaded plugin stages in `src/brjarvis/tools/registry.py`.
- **Tool Inventory:** 200 verified tools active with 0 import errors:
  - Filesystem & Batch (12 tools)
  - Documents & Office (Excel, Word, PDF, CSV, Presentations) (15 tools)
  - Browser Automation & Navigation (16 tools)
  - Desktop, OS, Window & Screen Control (28 tools)
  - System Telemetry & Process Supervision (14 tools)
  - Communication (Email, Gmail, Telegram, WhatsApp, Slack) (18 tools)
  - Research, RAG & Knowledge Ingestion (16 tools)
  - Career OS & Resume Generation (10 tools)
  - Memory & Recall (8 tools)
  - Native C Bridges (Audio meter, fast hash, proc telemetry) (4 tools)
  - Security, Prompt Auditing & Guardian Controls (8 tools)

---

## 7. Storage & Memory Architecture

1. **Relational Database (`SQLite in WAL mode`):**
   - Location: `runtime/jarvis.db` / `runtime/tasks.db`.
   - Serialized write mutex (`sqlite_lock.py` and `jarvis.memory.db.Database`) preventing `database is locked` errors.
2. **Vector Memory & Embeddings:**
   - Location: `runtime/vector_store` or `memory_db/`.
   - ChromaDB backend with automatic fallback to text similarity when native vector dependencies are unavailable.
3. **Session & Working Memory:**
   - Memory-resident `AgentSession` tracking correlation IDs, turns, observations, and active tasks.
4. **File-Based Vaults:**
   - `workspace/`: User documents, career versions, and delivery projects.

---

## 8. Security Boundaries

- **Prompt Injection Defense:** `GuardianCore` runs pre-execution regex and heuristics sweeps on model inputs.
- **Path Traversal Policy:** `path_policy.py` restricts file modifications strictly to the workspace directory.
- **Execution Approval Barrier:** High-risk actions (file deletion, external communications, process termination) require explicit operator confirmation.
- **Network Boundaries:** Same-origin WebSocket policy with localhost allow-list (`websocket_origin_allowed`). HttpOnly SameSite authentication cookies for REST API access.
- **Zero Raw Secrets:** Configuration files and probe scripts read keys exclusively from environment variables.
