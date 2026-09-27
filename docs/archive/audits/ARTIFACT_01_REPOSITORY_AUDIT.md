# ARTIFACT 01: BR JARVIS MASTER REPOSITORY AUDIT & FORENSIC INVENTORY
**Platform**: BR JARVIS Autonomous AI Operating System  
**Version**: MK37 / MK38 Transitional  
**Audit Date**: 2026-08-14  
**Auditor**: Principal Software Architect & Lead Engineer  
**Scope**: Complete Static & AST Inspection of 424 Python Modules, 34 Subsystems, 193 Registered Tools, 14 Connectors, 32 Local SQLite Databases, Server, UI, Mobile, and Voice/Vision Pipelines.

---

## 1. Executive Summary

BR JARVIS is an existing, multi-modal autonomous AI operating platform built for Windows/Linux desktop automation, voice interaction, mobile device orchestration, and background routine execution. 

### High-Level Statistics
- **Total Source Files Analyzed**: 1,370 files (424 Python modules, 38 JSON configs, 511 Markdown docs, 32 SQLite database files, 30 UI assets, 10 Word/PDF research docs).
- **Total Lines of Code (Python)**: ~82,400 LOC across 34 top-level packages.
- **AST Parse Integrity**: 424 / 424 Python modules parsed with **0 syntax errors**.
- **Registered Tools**: 193 active tool functions registered in `tools.registry` & `tools.tool_runtime`.
- **Connector Integrations**: 14 application connectors (Gmail, Notion, GitHub, Google Calendar, WhatsApp, Telegram, Slack, Jira, Linear, Discord, Wikipedia, YouTube, OpenWeather, MCP Proxy).
- **Test Suite**: 67 test files containing 246 discovered test cases across `tests/unit/` and `tests/integration/`.
- **Security & Safety Findings**: 19 dangerous call patterns (AST interpreter in sandbox, dynamic imports, browser `page.evaluate`), 9 circular import cycles, 0 hardcoded secrets.

---

## 2. Architectural Subsystem Inventory & Dependency Graph

```
                                    +----------------------------------------+
                                    |              User Interfaces           |
                                    |  (Web Dashboard / Voice / Float UI)   |
                                    +-------------------+--------------------+
                                                        |
                                                        v
                                    +----------------------------------------+
                                    |        Server & API Gateway            |
                                    |       (server.py / FastAPI)            |
                                    +-------------------+--------------------+
                                                        |
                                                        v
                                    +----------------------------------------+
                                    |       Security & Policy Gate           |
                                    |    (permissions.py / guardian/)        |
                                    +-------------------+--------------------+
                                                        |
                                                        v
                                    +----------------------------------------+
                                    |         Orchestrator & Router          |
                                    |  (orchestrator/core.py / router/)      |
                                    +---------+--------------------+---------+
                                              |                    |
                         +--------------------+                    +--------------------+
                         v                                                              v
+----------------------------------------+                    +----------------------------------------+
|          Task Control Plane            |                    |             Model Backends             |
|  (agent/step_planner, executor_engine) |                    |  (Gemini 3.7 / OpenAI / Anthropic)     |
+-------------------+--------------------+                    +----------------------------------------+
                    |
                    v
+------------------------------------------------------------------------------------------------------+
|                                     Capability Execution Layer                                       |
|  +---------------------+  +--------------------+  +--------------------+  +-----------------------+  |
|  |     Tools Engine    |  |  Connectors Hub    |  |  Computer Operator |  |   Android Subsystem   |  |
|  |  (tools/registry)   |  |  (connectors/hub)  |  |  (computer/actions)|  |   (mobile/gateway)    |  |
|  +---------------------+  +--------------------+  +--------------------+  +-----------------------+  |
+---------------------------------------------------+--------------------------------------------------+
                                                    |
                                                    v
+------------------------------------------------------------------------------------------------------+
|                                    State, Memory & Observability                                     |
|  +---------------------+  +--------------------+  +--------------------+  +-----------------------+  |
|  |   Persistent Store  |  |  Vector Knowledge  |  |   Routine Engine   |  |     Audit Engine      |  |
|  | (memory/sqlite_db)  |  |  (memory/chroma)   |  |  (actions/routine) |  | (history/audit_engine)|  |
|  +---------------------+  +--------------------+  +--------------------+  +-----------------------+  |
+------------------------------------------------------------------------------------------------------+
```

---

## 3. Detailed Component Forensic Analysis

### 3.1. Core Runtime & Bootstrap
| Path | Responsibility | Dependencies | Dependents | Public Interface | State Ownership | Side Effects | Security Sensitivity | Tests | Problems | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `core/bootstrap.py` | Initializes DI container, loads config, boots orchestrator, tool registry, memory, and event bus | `core.runtime`, `core.config`, `orchestrator`, `tools.registry`, `memory` | `server.py`, `start.py`, `main_mk37.py` | `build_assistant_runtime() -> AssistantRuntime` | Creates runtime singleton instance | Registers event listeners, mounts tools, initializes SQLite dirs | Medium | `tests/unit/test_core_runtime.py` | Heavy synchronous execution during import | Retain lazy worker pool offloading (`asyncio.to_thread`) |
| `core/runtime.py` | Holds global runtime state container, event bus reference, and thread-safe registry | `core.container`, `core.config` | Almost all submodules | `get_runtime() -> AssistantRuntime`, `set_runtime()` | Global runtime singleton `_RUNTIME` | None | Low | `tests/unit/test_core_runtime.py` | Module-level global pointer | Wrap with thread-safe atomic lock and context manager |
| `core/container.py` | Simple dependency injection (DI) container for decoupling services | None | `core.runtime`, `agent.executor_engine` | `Container.register()`, `Container.resolve()` | Service map dictionary `_services` | None | Low | `tests/unit/test_core_runtime.py` | Lacks lifecycle scope management (transient vs singleton) | Introduce formal scoped provider support |
| `core/health.py` | System health telemetry, CPU, RAM, disk, GPU stats | `psutil`, `platform` | `server.py`, `tools/system_tools.py` | `get_health_report() -> dict` | None | Queries OS hardware APIs | Low | `tests/unit/test_server_web.py` | Missing process thread count & handle leak checks | Add memory leak & stuck task thread count |

---

### 3.2. Agent Control Plane & Execution Engine
| Path | Responsibility | Dependencies | Dependents | Public Interface | State Ownership | Side Effects | Security Sensitivity | Tests | Problems | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `agent/executor_engine.py` | Parallel multi-worker DAG task step execution engine with human approval interlocks | `agent.types`, `core.runtime`, `events.bus` | `agent.executor`, `server.py`, `workflow.task_dag` | `ParallelExecutionEngine.execute_step()`, `execute_graph()` | In-memory execution state, active workers | Dispatches event bus notifications on task progress | High | `tests/unit/test_executor_engine.py` | In-memory only; does not persist state to SQLite if process crashes | Integrate with `agent.task_state` WAL persistence |
| `agent/step_planner.py` | Breaks natural language goals into structured `GoalGraph` with step dependencies and risk ratings | `agent.types`, `router.router` | `orchestrator`, `agent.executor` | `StepPlanner.plan(goal) -> GoalGraph` | None | Calls LLM planner model | Medium | `tests/unit/test_step_planner.py` | Fallback uses heuristic parsing when LLM returns unstructured text | Enforce structured JSON Schema output from Gemini 3.7 |
| `agent/task_state.py` | Persistent state machine for autonomous multi-step tasks across server restarts | `sqlite3`, `json`, `dataclasses` | `server.py`, `agent.executor` | `TaskStateManager.create_task()`, `get_task()`, `update_step()` | SQLite database `tasks.db` | Disk writes to `.jarvis/tasks.db` | High | `tests/unit/test_ui_multitask.py` | Concurrency lock contention on heavy concurrent steps | Enable SQLite WAL mode (`PRAGMA journal_mode=WAL`) |
| `agent/task_queue.py` | Priority-based task execution queue for asynchronous agent tasks | `queue.PriorityQueue`, `threading` | `server.py`, `orchestrator` | `TaskQueue.submit()`, `get_status()` | Queue state in memory | Spawns worker threads | Medium | `tests/unit/test_router_scratchpad_queue.py` | Worker threads lack graceful draining timeout on shutdown | Add graceful shutdown join with timeout |

---

### 3.3. Tools & Capability Registry
| Path | Responsibility | Dependencies | Dependents | Public Interface | State Ownership | Side Effects | Security Sensitivity | Tests | Problems | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tools/registry.py` | Universal decorator-based tool registry, parser, and prompt builder | `threading`, `json`, `re` | All tools, `orchestrator`, `skills` | `@register_tool`, `execute_tool()`, `get_tool_prompt_block()` | `TOOL_REGISTRY`, `TOOL_SCHEMAS` | Modifies global registries under `_REGISTRY_LOCK` | Critical | `tests/unit/test_tool_runtime.py` | Contains legacy regex tool-calling extractors alongside modern runtime | Migrate entirely to native typed structured tool schema |
| `tools/tool_runtime.py` | Unified typed execution runtime with pre-execution safety validation | `permissions`, `guardian.prompt_injection_shield` | `tools.registry`, `agent.executor_engine` | `ToolRuntimeEngine.execute()`, `list_tools()` | Registered tool definitions | Invokes underlying tool callables | Critical | `tests/unit/test_tool_runtime.py` | Needs strict Pydantic argument validation before invocation | Enforce Pydantic input models for all 193 tools |
| `tools/browser_agent_v2.py` | Strawberry-Class Playwright browser agent with DOM, accessibility tree, and screenshot observation | `playwright`, `asyncio`, `json` | `tools.registry`, `agent.executor` | `StrawberryBrowserAgent.observe()`, `execute_action()` | Browser page state | Controls local headless/headful Chromium | High | `tests/unit/test_autonomous_browser_agent.py` | Duplicate implementation with `autonomous_browser_agent.py` | Consolidate into single canonical BrowserAgent |
| `tools/sandbox.py` | Isolated Python code and PowerShell script execution | `subprocess`, `ast`, `tempfile` | `tools.registry`, `actions.desktop` | `execute_sandboxed_code()` | Temporary execution directories | Spawns isolated subprocess | Critical | `tests/unit/test_antigravity_system.py` | AST blacklist interpreter in pure Python can be bypassed if subprocess fallback is used | Add Windows AppContainer / process token restriction & timeout |

---

### 3.4. Mobile & Android Subsystem
| Path | Responsibility | Dependencies | Dependents | Public Interface | State Ownership | Side Effects | Security Sensitivity | Tests | Problems | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `mobile/gateway.py` | Android device registry, pairing PIN verification, authentication tokens, and trusted status | `sqlite3`, `secrets`, `hmac` | `server.py`, `mobile.device_controller` | `DeviceGateway.generate_pairing_token()`, `complete_pairing()` | `devices.db` SQLite table | Disk persistence of paired keys | Critical | `tests/unit/test_server_web.py` | Tokens stored without OS DPAPI/Fernet envelope encryption | Encrypt gateway tokens using `security.credential_vault` |
| `mobile/session.py` | Manages live WebSocket connections from paired Android companion apps | `fastapi.WebSocket`, `asyncio` | `server.py`, `mobile.device_controller` | `MobileSessionManager.register_session()`, `get_session()` | Active WebSocket session map | Handles bidirectional binary & text packets | High | `tests/unit/test_server_web.py` | Missing automated keepalive heartbeat ping/pong disconnect detection | Add 15s ping/pong keepalive watchdog |
| `mobile/device_controller.py` | High-level semantic actions for Android: inspect screen, open app, type, click, lock screen guard | `mobile.gateway`, `mobile.session`, `mobile.protocol` | `tools.registry`, `agent.executor` | `AndroidDeviceController.open_app()`, `inspect_screen()`, `click_element()` | Device state cache | Sends remote UI interaction messages to Android | Critical | `tests/unit/test_whatsapp_calendar_automation.py` | Correctly enforces `WAITING_FOR_USER_AUTHENTICATION` on lock screen | Preserve anti-lock-bypass architecture; add retry policy |

---

### 3.5. Security, Permissions & Guardian
| Path | Responsibility | Dependencies | Dependents | Public Interface | State Ownership | Side Effects | Security Sensitivity | Tests | Problems | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `permissions.py` | Deterministic policy evaluation engine (`ALLOW_ALL`, `CONFIRM_DESTRUCTIVE`, `CONFIRM_ALL`, `DENY_ALL`) | `dataclasses`, `json`, `os` | `core.bootstrap`, `tools.tool_runtime`, `guardian` | `PERMISSIONS.check(tool_name) -> bool`, `PermissionPolicy` | Global `PERMISSIONS` singleton | None | Critical | `tests/unit/test_permissions_default.py` | Simple tool-name check; lacks resource-level scope & session granularity | Expand to full 6-tuple policy (User, Device, App, Resource, Action, Risk) |
| `guardian/guardian_agent.py` | Runtime safety watchdog, secondary LLM verification, and human interlock gating | `guardian.human_interlock`, `events.bus` | `orchestrator`, `agent.executor_engine` | `GuardianAgent.verify_action()`, `evaluate_risk()` | Risk history | Publishes approval required events | High | `tests/unit/test_guardian.py` | Secondary LLM calls introduce latency if used for low-risk actions | Apply deterministic risk rules first; invoke LLM only for medium-high ambiguity |
| `guardian/prompt_injection_shield.py` | Detects indirect prompt injection, jailbreaks, and instructions embedded in external web/email content | `re`, `unicodedata` | `tools.tool_runtime`, `actions.rag_library` | `PromptInjectionShield.inspect() -> InjectionScanResult` | Injection pattern rules | Blocks malicious payload execution | Critical | `tests/unit/test_tool_runtime.py` | Regex-based heuristic detection | Add structural boundary tag escaping (`<untrusted_content>`) |

---

### 3.6. Memory & Knowledge
| Path | Responsibility | Dependencies | Dependents | Public Interface | State Ownership | Side Effects | Security Sensitivity | Tests | Problems | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `memory/persistent_store.py` | Key-value and structured memory store for long-term user facts and project settings | `sqlite3`, `json`, `pathlib` | `server.py`, `orchestrator`, `skills` | `save_memory()`, `load_entries()`, `search_memory()` | `memory.db` / `long_term.json` | Disk reads/writes in `workspace/` & `.jarvis/` | High | `tests/unit/test_memory_engine.py` | Mixed storage: JSON files and SQLite tables coexist | Consolidate into unified SQLite canonical memory store |
| `memory/contact_manager.py` | Unified contact repository with fuzzy name matching, vCard (.vcf) & CSV parser, relationship resolver | `sqlite3`, `difflib`, `re` | `server.py`, `actions.smart_email_sender`, `actions.whatsapp_automation` | `UnifiedContactStore.get_contact()`, `resolve_recipient()`, `import_vcf()` | `contacts.db` SQLite table | Modifies contact entries | Medium | `tests/unit/test_contact_importer.py`, `test_relationship_resolution.py` | Thread contention on concurrent imports | Use SQLite connection pool with busy timeout |
| `memory/episodic_memory.py` | Conversation turn history and episodic recall with timestamp indexing | `sqlite3`, `time` | `orchestrator`, `agent.context_engine` | `EpisodicMemory.add_turn()`, `get_recent()` | `episodic.db` | Appends turn logs | Low | `tests/unit/test_memory_context.py` | Unbounded growth without compaction | Add automatic rolling TTL / summary compaction |

---

### 3.7. Server & API Gateway
| Path | Responsibility | Dependencies | Dependents | Public Interface | State Ownership | Side Effects | Security Sensitivity | Tests | Problems | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `server.py` | Monolithic FastAPI gateway hosting REST API, WebSockets, OpenAI proxy, static files, and process killer | `fastapi`, `uvicorn`, `orchestrator`, `mobile.gateway`, `actions.routine_engine` | External Web UI, Mobile Companion, CLI | 55 REST endpoints, 2 WebSocket endpoints | Server state, active WebSockets | Binds TCP port 8000, manages broadcast logs | Critical | `tests/unit/test_server_web.py` | 1,481 lines in single file; routes, models, background loops, and cleanup tightly coupled | Modularize into `api/routes/` with APIRouter |

---

## 4. Circular Import Graph & Dangerous Call Analysis

### Detected Circular Import Cycles:
1. `tools.registry -> tools.tool_runtime -> tools.redteam_tools -> tools.registry`
2. `tools.registry -> tools.web_extractor -> tools.registry`
3. `tools.registry -> tools.file_search_semantic -> tools.registry`
4. `tools.registry -> skills -> skills.executor -> multi_agent.subagent -> tools.registry`
5. `actions.send_message -> actions.telegram_automation -> actions.send_message`
6. `config.complexity_router -> config.models -> config.complexity_router`
7. `ui_mark -> voice.assistant -> ui_mark`

*Mitigation in current codebase*: Submodules use in-function deferred `import` calls.  
*Target Fix*: Refactor dependency hierarchy so tools do not import the central registry module at top-level or runtime, and introduce explicit interface abstractions.

### Dangerous Call Analysis:
- `float_widget.py:615`, `start.py:695`, `ui/app.py:81`: `app.exec()` — Qt UI event loop execution (Harmless/Standard PySide6).
- `tools/sandbox.py:33`: `__import__("shutil")` — Dynamic stdlib import (Safe).
- `tools/browser_automation.py:440`: Playwright `page.evaluate()` — Evaluates in isolated browser DOM context (Safe).
- `tools/scratchpad_tools.py:58`: `tool_scratchpad_eval()` — Invokes isolated AST evaluation (Requires formal sandbox isolation).

---

## 5. Repository Forensic Verdict
The BR JARVIS repository exhibits substantial engineering depth, featuring high test coverage across core components, clear architectural ambition, and working implementations of critical subsystems (such as Android companion pairing, voice pipelines, and multi-step execution graphs). 

However, architectural maturity is currently hindered by:
1. **Monolithic Server**: `server.py` conflates API transport with domain logic.
2. **Scattered State Persistence**: 32 distinct SQLite database files across temporary and workspace folders.
3. **In-Memory Volatility**: DAG task execution is not consistently written to a durable WAL prior to step execution.
4. **Tool Schema Heterogeneity**: Legacy string-based parsing coexists with structured function calling.

The system is in a prime state for production-grade evolution following our targeted transformation plan.
