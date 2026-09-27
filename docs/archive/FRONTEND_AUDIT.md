# BRJARVIS Frontend Audit

**Status:** Initial repository-grounded audit  
**Date:** 2026-08-19  
**Scope:** Web, desktop, floating widget, voice, vision, CLI, Career OS, APIs, realtime events, and frontend test boundaries

## Executive summary

BRJARVIS is not currently a single frontend application. It is a Python-first platform with several user-facing surfaces: a FastAPI-served browser client, a Qt desktop application, a separate floating widget/HUD, a terminal-native CLI/TUI, voice and camera interactions, and Career OS routes layered into the web API. The redesign must therefore be treated as a **multi-surface frontend architecture migration**, not as a page-level restyling exercise.

The existing runtime already contains substantial capabilities for orchestration, agents, tasks, tools, memory, model routing, permissions, verification, voice, vision, Career OS, and event delivery. The principal frontend problem is not the absence of capability. It is the absence of a sufficiently unified presentation, state, command, and event layer across the surfaces.

The repository working tree also contains widespread existing modifications and untracked test work. Those changes must remain untouched unless they are explicitly reconciled. The redesign should proceed in an isolated branch or worktree and should add compatibility layers rather than replacing runtime behavior.

## Baseline and safety conditions

The current branch is the repository’s active development branch, and the working tree is not clean. The modified-file scope includes core runtime, agent, gateway, guardian, memory, router, security, tool, web route, startup, and test files. This is a material safety constraint: a broad frontend rewrite or automated formatter could obscure unrelated work or destroy changes that are not part of the redesign.

The baseline policy is therefore:

| Rule | Decision |
|---|---|
| Existing modifications | Preserve them; do not reset, stash, or overwrite automatically. |
| New redesign work | Use a dedicated branch or isolated worktree. |
| Backend compatibility | Preserve current routes and event behavior initially. |
| API migration | Add adapters or versioned clients before changing contracts. |
| Legacy removal | Defer deletion until usage, test, and rollback evidence exists. |
| Documentation | Record every discovered surface and dependency before implementation. |

## Frontend entry-point inventory

### Browser and web command center

| Entry point | Current implementation | Runtime dependency | Current assessment | Migration priority |
|---|---|---|---|---:|
| `/`, `/index.html` | FastAPI `FileResponse` serving `src/brjarvis/web/static/index.html` | `src/brjarvis/web/api/server.py` and `WEB_DIR` | Primary browser entry point; legacy static application shell | P0 |
| `/web`, `/web/`, `/web/index.html` | Same static client under the `/web` namespace | FastAPI route plus `StaticFiles` mount | Duplicate access path that must remain compatible during migration | P0 |
| `/web/app.js` | `src/brjarvis/web/static/app.js` | DOM event bindings, `apiFetch`, WebSocket client, REST routes | Large global-script client with ad-hoc state and view switching | P0 |
| `/web/style.css` | `src/brjarvis/web/static/style.css` | Static HTML/JS class names | Existing visual language; must be tokenized rather than copied blindly | P0 |
| `/galaxy`, `/galaxy.html`, `/3d` | `src/brjarvis/web/static/galaxy.html` | Static route in the FastAPI server | Separate visualization surface; needs a decision on whether it becomes a command-center workspace or remains an advanced view | P1 |
| Service worker/offline | `offline.html`, `sw.js`, `manifest.json` | Browser cache and offline fallback | Important operational boundary; stale-cache behavior is explicitly handled by the server | P1 |
| Bundled distribution | `src/brjarvis/web/static/dist/app.js` and source map | Static asset delivery | Generated or legacy build artifact; ownership and build process must be verified before replacing | P1 |

The browser client currently performs theme selection, authentication handling, modal control, global workspace state, view switching, telemetry polling, conversation CRUD, transcript rendering, streaming response handling, project/artifact interactions, and WebSocket reconnect/heartbeat behavior from one global script. This makes it the most important migration anchor but also the highest-risk file to rewrite without an adapter boundary.

### Desktop application and HUD

| Entry point | Current implementation | Runtime dependency | Current assessment | Migration priority |
|---|---|---|---|---:|
| Desktop launcher | `src/brjarvis/apps/desktop.py` | `brjarvis.ui.app.run_voice_ui` | Canonical desktop launch wrapper | P1 |
| UI wrapper | `src/brjarvis/ui/app.py` | PyQt/PySide abstraction, `MainWindow`, headless fallback | Provides `JarvisUI` and `HeadlessJarvisUI`; useful compatibility seam | P0 |
| Main desktop window | `src/brjarvis/ui/main_window.py` | Qt widgets, timers, signals, overlays, camera stream, EventBus | Large monolithic desktop composition containing layout, rendering, process actions, and integration logic | P0 |
| Desktop primitives | `src/brjarvis/ui/_qt.py`, `colors.py`, `widgets.py`, `overlays.py` | Qt runtime and shared palette helpers | Existing component and palette fragments; not yet a cross-surface design system | P1 |
| Voice/HUD wrapper | `src/brjarvis/desktop/ui_mark.py` | Desktop UI runtime | Separate voice-oriented surface that must share state semantics with the main window | P1 |
| Root compatibility shims | `float_widget.py`, `ui_mark.py` | Existing launch scripts | Preserve until callers are mapped | P1 |

The desktop window already supports a number of real interactions: state changes, mute and interruption shortcuts, content display, task updates, file drop/ingestion, camera preview and live camera streaming, system metrics, a quick drawer, remote control helpers, setup/configuration overlays, and EventBus-driven task activity. These capabilities should be exposed through an interaction model rather than reimplemented as decorative widgets.

### Floating JARVIS

| Entry point | Current implementation | Current assessment | Migration priority |
|---|---|---|---:|
| Floating widget | `src/brjarvis/desktop/float_widget.py` | Always-on-top PySide6 mini HUD with state ring, waveform, logs, connector badges, input/mic controls, tray behavior, and state colors | P0 |
| Root shim | Root-level `float_widget.py` | Compatibility launcher/forwarder | P1 |

The floating widget is already a distinct surface, not merely a visual component inside the desktop window. It has its own state rendering and control behavior. The redesign must define a shared state contract for `IDLE`, `LISTENING`, `THINKING`/processing, `SPEAKING`, `EXECUTING`, `ERROR`, approval, and disconnected states, then let the widget render that contract.

### CLI and terminal-native interface

| Entry point | Current implementation | Runtime dependency | Current assessment | Migration priority |
|---|---|---|---|---:|
| CLI launcher | `src/brjarvis/apps/cli.py` | `brjarvis.core.cli.main` | Canonical CLI entry point | P1 |
| Session controller | `src/brjarvis/core/terminal/session.py` | `ApplicationRuntime`, `AgentLoop`, `TerminalRenderer`, `SlashCommandHandler`, prompt-toolkit, Rich | Already a first-class interactive surface with task, approval, interruption, and event behavior | P0 |
| Command registry | `src/brjarvis/core/terminal/commands.py` | CLI session and terminal renderer | Canonical for CLI today, but separate from browser command-palette definitions | P0 |
| Terminal renderer | `src/brjarvis/core/terminal/renderer.py` and related components | Rich and terminal theme/components | Reusable presentation layer within CLI; should become an adapter over shared command/task semantics | P1 |
| Interactive TUI | `src/brjarvis/core/terminal/interactive_tui.py` and related modules | Terminal input/mouse/selection support | Must be preserved while renderer and command registry are migrated | P1 |

The CLI already supports command history/autocomplete, slash commands, prompt context states, task execution, plan/approval flow, interrupt handling, Rich rendering, and EventBus subscriptions. The correct redesign is not to create a second command system; it is to extract a canonical command registry and retain the terminal as one presentation adapter.

### Voice and vision

| Surface | Current implementation | Existing evidence | Migration priority |
|---|---|---|---:|
| Voice launcher | `src/brjarvis/apps/voice.py` and `src/brjarvis/ui/app.py` | Voice UI wrapper and state methods such as `start_speaking`, `stop_speaking`, `set_state`, and interrupt callbacks | P0 |
| Voice API | `src/brjarvis/web/api/routes/voice.py` | Web route registered in the FastAPI application | P0 |
| Desktop camera preview | `src/brjarvis/ui/main_window.py` | Camera frame signal, live stream stack, OpenCV capture loop, preview overlay | P1 |
| Screen/device intelligence | `src/brjarvis/screen_server`, `src/brjarvis/integrations/mobile`, and device routes | Screen server and mobile/device integration modules | P1 |

The audit must distinguish microphone/voice state, camera state, screen capture state, and model processing state. These states should not be inferred from animation. They must be driven by real runtime events and explicit capability/privacy status.

### Career OS

Career OS is exposed through `src/brjarvis/career/api_routes.py`, mounted by the FastAPI server under `/api/career` and also included through the versioned `/api/v1` route registration. Existing capabilities include profile and onboarding, resume templates and generation, resume tailoring, ATS scoring, job search and matching, application preparation and tracking, analytics, interview preparation, email intelligence, CRM events, interviews, offers, and file downloads.

The redesign should use these existing capability families as the source of truth. It should not introduce unsupported career scores, skill gaps, or recommendations merely because the target visual brief requests them. Any overview metric must be derived from an existing backend capability or explicitly shown as unavailable.

## Web API inventory

The FastAPI application is assembled in `src/brjarvis/web/api/server.py`. It includes both unprefixed routers and versioned `/api/v1` registrations. The route modules currently include:

| Domain | Route module | Frontend use to verify |
|---|---|---|
| Authentication | `auth.py` | Session establishment, auth expiry, protected actions |
| Health | `health.py` | Runtime/system status and telemetry |
| Tasks | `tasks.py` | Task listing, state, control, and recovery |
| Conversations | `conversations.py` | Conversation history and branching |
| Projects | `projects.py` | Workspace/project context |
| Artifacts | `artifacts.py` | Generated files and previews |
| Search | `search.py` | Global search and command palette support |
| Notifications | `notifications.py` | User-facing alerts and activity |
| Automations | `automations.py` | Workflow definitions and execution history |
| Devices | `devices.py` | Connected device and screen capabilities |
| Routines | `routines.py` | Scheduled/recurring behavior |
| Skills | `skills.py` | Skill discovery and activation |
| Connectors | `connectors.py` | External integration status |
| Memory | `memory.py` | Memory exploration and controls |
| Chat | `chat.py` | Conversation/task invocation support |
| Voice | `voice.py` | Voice interaction boundary |
| WebSocket | `websocket.py` | Bidirectional realtime events and commands |
| Career OS | `career/api_routes.py` | Career intelligence and lifecycle operations |

The server also applies authentication, CORS, security headers, static-file fallback, and a global exception handler. The redesign should keep these server responsibilities outside presentation components and should use a typed client/adaptor layer for all API access.

## Realtime event inventory

The current WebSocket bridge standardizes an envelope with `event_id`, `type`, optional `conversation_id`, optional `task_id`, `timestamp`, and `payload`. It accepts one-time tickets or a session cookie and supports heartbeats. The bridge subscribes to EventBus patterns including:

| Event family | Current evidence | Target UI responsibility |
|---|---|---|
| `agent.*` | WebSocket EventBus forwarding | Planning, execution, waiting, and completion summaries |
| `tool.*` | WebSocket EventBus forwarding | Tool activity and result summaries |
| `permission.*` | WebSocket EventBus forwarding | Approval/risk interface |
| `verification.*` | WebSocket EventBus forwarding | Verification result and recovery guidance |
| `artifact.*` | WebSocket EventBus forwarding | Artifact availability and preview state |
| `task.*` | WebSocket EventBus forwarding plus explicit task lifecycle messages | Task cards, timelines, progress, cancellation, retry |
| `session.*` | WebSocket EventBus forwarding | Session connection and context state |
| `message.*` | Explicit WebSocket chat flow | Streaming transcript and completed response |
| `conversation.created` | Explicit WebSocket chat flow | Conversation selection and history refresh |
| `ServerReady` | WebSocket handshake | Runtime availability and version status |
| `Heartbeat` / `error` | WebSocket protocol | Connection health and recoverable transport errors |

The current bridge also accepts multiple aliases for chat submission, including `chat_prompt`, `command`, `chat`, `clientcommand`, and `message.send`. This compatibility is useful during migration but should be normalized behind one typed client command method rather than exposed to every UI component.

## State architecture audit

The current system contains several state owners:

| State category | Existing owners/evidence | Redesign direction |
|---|---|---|
| Server state | REST route modules, workspace store, task state manager, Career OS services | Query/mutation clients with normalized domain models and cache policy |
| Realtime state | WebSocket route, EventBus, desktop Qt signals, CLI EventBus subscriptions | One normalized event adapter with surface-specific renderers |
| UI state | Browser globals/localStorage/DOM classes, Qt widget state, CLI prompt states | Keep local UI state local; introduce a small surface-level store rather than one global store |
| Runtime capability state | Health routes, model gateway, connectors, devices, voice, vision | Capability registry with availability, permission, health, and reason fields |
| Session/auth state | Browser API wrapper, auth routes, WebSocket ticket/session checks, desktop config | Shared auth/session abstraction per surface with redaction and expiry handling |

The browser currently stores significant state in globals and DOM nodes, including active conversation, branch, project, generation status, stream elements, socket state, and server API key/session behavior. The desktop uses Qt object state, signals, timers, and callbacks. The CLI uses a `TerminalSession` object, prompt state, runtime references, and EventBus listeners. These are all valid local mechanisms, but their domain concepts and lifecycle states are not yet represented by one shared contract.

## Duplication and legacy register

| Duplication/legacy concern | Evidence | Required action |
|---|---|---|
| Multiple browser access paths | Root routes, `/web` routes, static fallback, and special `/galaxy` paths | Preserve paths, route them to a new shell through compatibility redirects or a stable mount. |
| Monolithic browser script | `src/brjarvis/web/static/app.js` owns auth, view switching, polling, WebSocket, conversations, artifacts, and DOM rendering | Extract typed clients, event adapter, domain stores, and components incrementally. |
| Separate browser and CLI command systems | Browser command-palette functions and `core/terminal/commands.py` | Create one canonical command registry with adapters. |
| Separate desktop and browser visual systems | Qt palette/colors/widgets versus CSS/static classes | Define semantic tokens and map both systems to them; do not force identical layouts. |
| Multiple task update paths | WebSocket task events, EventBus forwarding, desktop Qt task signals, CLI EventBus callbacks | Normalize task lifecycle events and define ownership for projections. |
| API aliases and duplicate route registration | Unprefixed and `/api/v1` routers, multiple chat message type aliases | Keep compatibility at the client boundary and document canonical methods. |
| Large desktop composition | `main_window.py` combines layout, metrics, camera, overlays, task panel, shortcuts, and actions | Decompose by capability after the shared contract exists. |
| Generated/static distribution ambiguity | `static/dist/app.js` alongside source static files | Identify the authoritative build pipeline before replacing or deleting artifacts. |

## Capability-to-surface map

| Capability | Web | Desktop/HUD | Floating widget | CLI | Career OS |
|---|---:|---:|---:|---:|---:|
| Conversational assistant | Yes | Yes | Yes | Yes | Advisor integration required |
| Streaming response | WebSocket | Callback/EventBus path to verify | Widget activity path to verify | Live renderer | Not primary |
| Task execution | API/WebSocket | Task panel/EventBus | Compact execution state | Session/task renderer | Application/resume jobs where supported |
| Tool activity | WebSocket events | Logs/activity path | Connector/log badges | Event listeners/renderer | Backend-specific |
| Approvals | WebSocket permission events and route checks | Overlay/callback path to verify | Compact approval state required | Permission prompt | Application/offer actions may require confirmation |
| Memory | Memory routes | Runtime integration to verify | Quick command target | `/memory` command | Career profile/CRM data boundary |
| Models | Backend gateway and settings route discovery required | Config-driven | Status/badge | `/models` command | Indirect |
| Automation | Automation/routine routes | Quick drawer/remote actions to verify | Quick command target | `/automation` command target | Calendar and follow-up workflows |
| Voice | Voice route | Voice UI | Mic/listening state | Input fallback | Advisor interaction |
| Vision/screen | Device/screen integrations | Camera/screen capabilities | Trigger/quick action | Command-driven | Evidence from files/screens only when permitted |
| Artifacts/files | Artifacts/projects/files routes | Drop zone/content panel | Notification only | Result paths/diagnostics | Resume and career exports |

## Audit findings and decisions

The first implementation should focus on **contract extraction**, not page construction. The browser assistant is the best vertical-slice host because it already exercises authentication, conversation persistence, WebSocket connection, streaming, task lifecycle, and artifacts. The desktop and CLI should then consume the same normalized task and command contracts rather than being redesigned independently.

The target architecture should also distinguish a **capability unavailable** state from an **empty data** state. For example, an unavailable vision provider is not the same as a user with no screen selection; a disconnected model is not the same as a model with no recent activity; and an empty memory category is not a failed memory request.

## Remaining verification work before implementation

The following items remain explicit audit tasks rather than assumptions:

1. Parse the complete `index.html` and `style.css` to enumerate every browser view, modal, nav item, and responsive breakpoint.
2. Complete the API endpoint table from all route decorators, including request/response schemas and authentication requirements.
3. Trace every EventBus topic producer to its contract class and determine whether its payload is stable enough for a public frontend event envelope.
4. Verify the current desktop EventBus subscriptions and the floating widget’s external callbacks.
5. Identify the authoritative static build process for `static/dist/app.js`.
6. Run the relevant existing web, WebSocket, CLI, Career OS, and smoke tests without modifying the working tree; record failures separately from redesign work.
7. Confirm the current browser and desktop startup paths on the supported Windows environment.

## References

[1]: ../src/brjarvis/web/api/server.py "FastAPI application factory, route registration, authentication, static serving, and security middleware"
[2]: ../src/brjarvis/web/api/routes/websocket.py "WebSocket authentication, event envelope, chat protocol, task lifecycle, and streaming"
[3]: ../src/brjarvis/web/static/app.js "Legacy browser client state, views, REST calls, WebSocket handling, and DOM rendering"
[4]: ../src/brjarvis/ui/app.py "Desktop UI wrapper and headless compatibility interface"
[5]: ../src/brjarvis/ui/main_window.py "Qt desktop main window, HUD, task panel, camera, overlays, and controls"
[6]: ../src/brjarvis/desktop/float_widget.py "Floating JARVIS widget implementation"
[7]: ../src/brjarvis/core/terminal/session.py "Interactive CLI/TUI session controller and runtime/event integration"
[8]: ../src/brjarvis/core/terminal/commands.py "CLI slash-command registry and dispatcher"
[9]: ../src/brjarvis/career/api_routes.py "Career OS profile, resume, job, application, analytics, CRM, interview, and offer APIs"
[10]: ../pyproject.toml "Python dependencies and project configuration"
[11]: ../tests/integration/test_fastapi_web_routes.py "FastAPI route integration coverage"
[12]: ../tests/integration/test_websocket_hub.py "WebSocket/event integration coverage"
[13]: ../tests/unit/test_cli_repl.py "CLI session coverage"
[14]: ../tests/integration/test_career_os_integration.py "Career OS integration coverage"

## Baseline record

The repository was inspected without resetting or stashing the working tree. The active branch contains widespread tracked modifications and untracked test work across runtime, security, memory, agent, gateway, web routes, startup, and tests. Relevant redesign documents were added under `docs/`; no existing application source was rewritten during the audit. A full baseline test run remains pending because the current working tree contains unrelated changes that must be reported separately from redesign failures.


## Baseline test result

On 2026-08-19, the following existing suites were run without modifying application source:

```text
python -m pytest -q tests/integration/test_fastapi_web_routes.py tests/integration/test_websocket_hub.py tests/unit/test_cli_repl.py tests/integration/test_career_os_integration.py --maxfail=20

57 passed, 1 warning in 29.46s
```

The warning is a Pytest configuration warning for an unknown `timeout` option in the current Windows test environment. The passing result provides a useful regression boundary for the web routes, WebSocket hub, CLI REPL, and Career OS integration while the frontend platform is introduced.


## Focused audit: `ui_mark.py` and `ui.py`

### Executive finding

The root-level `ui_mark.py` and `ui.py` files are **not two independent user interfaces**. They are compatibility and startup shims that ultimately route into the same canonical desktop/voice UI stack. The actual desktop implementation lives under `src/brjarvis/desktop/ui_mark.py` and `src/brjarvis/ui/`, with `src/brjarvis/apps/desktop.py` and `src/brjarvis/apps/voice.py` acting as additional launch wrappers.

This is important for migration planning. Replacing or redesigning the two root files as though they were separate frontend surfaces would create unnecessary risk and would miss the real rendering and runtime boundaries.

### Root `ui_mark.py`

The root file performs project-path setup, imports `main` from `brjarvis.apps.desktop`, imports the implementation module `brjarvis.desktop.ui_mark` as `_um`, and forwards selected helper functions and unknown attributes to that implementation. Its explicitly exposed helpers include server liveness/port selection, available-port discovery, server-port resolution, and remote credential generation.

| Responsibility | Root `ui_mark.py` behavior | Classification |
|---|---|---|
| Import bootstrapping | Adds the repository `src` directory to `sys.path` | Compatibility/startup glue |
| Launching | Calls `brjarvis.apps.desktop.main()` when executed directly | Launcher wrapper |
| Runtime helper forwarding | Delegates `_is_jarvis_running`, `_port_free`, `_find_available_jarvis_port`, `_server_port`, and `_generate_remote_credentials` to `brjarvis.desktop.ui_mark` | Compatibility API |
| Attribute forwarding | `__getattr__` forwards unknown names to the implementation module | Legacy compatibility mechanism |
| Attribute assignment | `__setattr__` attempts to mirror assignments to the implementation module | Coupling risk |
| Rendering | None in the root file | Not a UI implementation |
| State ownership | None of its own beyond module-level forwarding behavior | Not a domain/state owner |

The root shim’s `__setattr__` forwarding is especially important to preserve carefully. It can make module-level monkey-patching or legacy integrations appear to work while obscuring the true owner of a value. New code should import the canonical implementation or application entry point directly rather than adding more behavior to this shim.

### `src/brjarvis/desktop/ui_mark.py`

The implementation module is a **full-stack desktop/voice launcher**, not just a visual HUD module. It performs Python-version routing on Windows, configures logging, detects PySide6/PyQt6, imports the canonical `JarvisUI` and `HeadlessJarvisUI`, selects a server port, starts an embedded FastAPI/Uvicorn backend in a daemon thread, starts `BRVoiceAssistant` in a second daemon thread, installs signal handlers, registers cleanup, and blocks on the Qt or headless event loop.

| Responsibility | Implementation evidence | Architectural implication |
|---|---|---|
| Python selection | Re-routes Python 3.14 alpha to an available stable interpreter on Windows | Startup policy should be isolated from UI composition. |
| Qt setup | Calls `setup_qt_paths()` and detects PySide6/PyQt6 | Native UI dependency boundary. |
| Logging | Configures stdout and `runtime/logs/ui_mark.log` | Observability is coupled to launcher startup. |
| Backend lifecycle | Starts FastAPI/Uvicorn in a daemon thread and detects existing/foreign port use | Desktop launcher owns backend orchestration; this should become an explicit application runtime service. |
| Voice lifecycle | Starts `BRVoiceAssistant` in a daemon thread and connects `ui.on_interrupt` to `assistant.stop_speech` | Voice interruption is a real callback path, not merely visual state. |
| Remote access | Generates local-network dashboard URLs and server credentials | Must remain behind security-aware pairing/permission UX. |
| GUI/headless selection | Chooses `JarvisUI` or `HeadlessJarvisUI` based on display availability | The same UI contract already has a headless fallback. |
| Shutdown | Installs signal handlers and an `atexit` cleanup callback | Lifecycle behavior should not be embedded in individual widgets. |
| Rendering | Delegates actual rendering to `brjarvis.ui.app`, `MainWindow`, widgets, overlays, and HUD modules | Not the correct file for visual redesign. |

The current implementation uses daemon threads for both the embedded server and voice worker. That is convenient for the launcher but creates lifecycle and observability concerns: the launcher, backend, voice engine, Qt event loop, and headless loop do not currently share one explicit lifecycle state model. The redesign should expose this as runtime health and connection state rather than adding more launcher-local flags.

### Root `ui.py`

The root `ui.py` is a **package compatibility shim**, not a UI implementation. It adds `src` and `src/brjarvis/ui` to `sys.path`, calls `ensure_canonical_python()`, sets `__path__` to the package directory, lazily forwards attributes to `brjarvis.ui`, and launches `brjarvis.apps.desktop.main()` when run directly.

| Responsibility | Root `ui.py` behavior | Classification |
|---|---|---|
| Import path setup | Adds `src` and the UI package directory to `sys.path` | Compatibility/bootstrap glue |
| Interpreter selection | Calls `ensure_canonical_python()` | Runtime bootstrap |
| Package emulation | Sets `__path__` to `src/brjarvis/ui` | Legacy import compatibility |
| API forwarding | Lazily delegates attributes to `brjarvis.ui` | Compatibility API |
| Direct launch | Calls the canonical desktop app entry point | Launcher wrapper |
| Rendering/state | None | Not a UI implementation |

The root file exists to preserve legacy invocations such as `python ui.py` and legacy import expectations. It should not become a place for new widgets, event handling, layout code, API calls, or design-system logic.

### `src/brjarvis/ui/__init__.py`

The actual UI package initializer configures Qt plugin paths, resolves the canonical project root, defines the Windows subprocess suppression flag, and lazily re-exports the public UI API. Its lazy exports include `JarvisUI`, `HeadlessJarvisUI`, `is_gui_available`, `MainWindow`, palette helpers, and shared widget classes.

This package initializer is the correct compatibility boundary for native UI consumers. It should remain small and focused on package/runtime setup. Visual composition belongs in `app.py`, `main_window.py`, `widgets.py`, `overlays.py`, and the future shared native design-system layer.

### Relationship between the files

```text
root ui_mark.py
      │ compatibility forwarding
      ▼
brjarvis.apps.desktop.main()
      │
      ▼
brjarvis.ui.app.run_voice_ui()
      │ compatibility delegation
      ▼
brjarvis.desktop.ui_mark.run_voice_ui()
      │
      ├── JarvisUI / HeadlessJarvisUI
      │       └── brjarvis.ui.main_window.MainWindow
      │
      ├── embedded FastAPI/Uvicorn server thread
      │
      └── BRVoiceAssistant worker thread

root ui.py
      │ package/interpreter compatibility
      ▼
brjarvis.ui package
      │ lazy exports
      ▼
brjarvis.ui.app / main_window / widgets / overlays / colors
```

The graph shows that `ui_mark.py` and `ui.py` converge on the same canonical runtime rather than representing separate desktop applications.

### Duplication and migration risks

| Risk | Severity | Finding | Recommendation |
|---|---:|---|---|
| Multiple launch wrappers | Medium | Root `ui_mark.py`, root `ui.py`, `apps.desktop.py`, `apps.voice.py`, and `ui.app.run_voice_ui()` all participate in launch behavior. | Keep wrappers stable, document one canonical launch path, and move new lifecycle logic into an application runtime service. |
| Full-stack launcher coupling | High | `src/brjarvis/desktop/ui_mark.py` owns Qt selection, embedded server, voice worker, port discovery, credentials, signals, and loop blocking. | Split startup orchestration from UI composition behind explicit lifecycle interfaces. |
| Module attribute mirroring | Medium | Root `ui_mark.py` forwards unknown reads and attempts to mirror writes. | Treat as legacy-only; add tests for required compatibility names before deprecation. |
| Package emulation | Medium | Root `ui.py` manipulates `sys.path` and `__path__`. | Preserve for legacy execution but prevent new imports from depending on it. |
| Voice state callback coupling | High | `ui.on_interrupt` is assigned directly to `assistant.stop_speech`. | Replace with a typed voice-control/event adapter shared by native, web, and floating surfaces. |
| Server ownership ambiguity | High | Desktop launch can start the embedded server, while the web app can also be started independently. | Define one runtime ownership/status contract and display whether the backend is embedded, external, unavailable, or already running. |
| Headless divergence | Medium | `HeadlessJarvisUI` has compatible methods but no native rendering and some camera methods are no-ops. | Treat headless as an explicit capability projection with unavailable states, not as a silent feature loss. |
| Platform version routing | Medium | Python-version rerouting is mixed into the desktop UI launcher. | Keep it in startup tooling and test it separately from UI behavior. |

### Migration decision

The root files should **not be redesigned visually**. They should be retained as thin, tested compatibility shims while the actual native surface is migrated through the canonical `JarvisUI`/`HeadlessJarvisUI` contract and the `MainWindow`/widget component layer.

The next native UI migration should introduce a `DesktopRuntimeBridge` or equivalent adapter responsible for:

1. Exposing connection, backend, voice, vision, task, and approval capability status.
2. Translating runtime events into typed native UI state.
3. Routing user commands and interruptions back to real runtime handlers.
4. Supporting both Qt and headless implementations.
5. Providing lifecycle start/stop/error/reconnect signals without making widgets own threads.

Until that bridge exists, changes to `src/brjarvis/desktop/ui_mark.py` should be limited to safe lifecycle fixes and observability. Changes to root `ui_mark.py` and `ui.py` should be limited to compatibility, deprecation notices, and tests.

### Recommended test coverage

The following tests should be added or confirmed before deprecating either shim:

| Test | Purpose |
|---|---|
| Root `ui_mark.py` import/forwarding test | Confirms helper forwarding and canonical `main` behavior. |
| Root `ui.py` import/package test | Confirms `__path__`, lazy exports, and direct-launch compatibility. |
| Headless launch test | Confirms the UI contract works without a display. |
| Embedded-server ownership test | Confirms reuse of an existing JARVIS server and safe fallback on a foreign port. |
| Voice interruption test | Confirms `on_interrupt` stops speech and updates visible state. |
| Shutdown test | Confirms daemon workers and Qt/headless loops exit through the intended lifecycle. |
| Remote-credential safety test | Confirms credential generation and dashboard pairing do not leak secrets. |

## Additional references

[15]: ../ui_mark.py "Root ui_mark.py compatibility launcher"
[16]: ../ui.py "Root ui.py package and interpreter compatibility shim"
[17]: ../src/brjarvis/desktop/ui_mark.py "Canonical full-stack desktop/voice launcher"
[18]: ../src/brjarvis/ui/__init__.py "Canonical native UI package initializer and lazy public API"
[19]: ../src/brjarvis/apps/desktop.py "Canonical desktop application entry point"
[20]: ../src/brjarvis/apps/voice.py "Canonical voice application entry point"
[21]: ../src/brjarvis/core/paths.py "Canonical interpreter and project-path bootstrap"


## Focused audit: `float_widget.py`

### Executive finding

The floating widget is a **native Qt micro-surface with its own runtime adapter behavior**, not merely a minimized copy of the main desktop window. The root `float_widget.py` is only an import/launch shim. The canonical implementation is `src/brjarvis/desktop/float_widget.py`, which defines the Qt widget, custom waveform and status-ring painting, tray behavior, hotkeys, connector polling, command submission, voice trigger behavior, and a headless fallback.

It is a high-value surface for the redesign because it compresses assistant interaction into a persistent, always-on-top control. It is also high-risk because it currently combines presentation, threading, HTTP calls, runtime discovery, system-tray lifecycle, and capability fallback inside one module.

### Root `float_widget.py` shim

The root file adds `src` to the import path, attempts a wildcard import from `brjarvis.desktop.float_widget`, suppresses import errors, and launches `brjarvis.apps.desktop.main()` when run directly. The direct-launch behavior does not call the floating widget’s own `main()` function; the canonical floating entry point is reached through `start.py floating|widget|float`, which imports `brjarvis.desktop.float_widget.main` directly.

This means the root shim should remain compatibility-only. Its broad `except Exception: pass` can conceal missing Qt or import failures, so new code should not rely on it for health reporting.

### Canonical widget structure

| Area | Current implementation | Migration implication |
|---|---|---|
| Window | Frameless, translucent, always-on-top Qt `QWidget` with fixed normal size `320x500` and minimized size `64x64` | Preserve the compact/persistent surface, but make size and placement responsive and accessibility-aware. |
| Visual shell | Custom `GlassPanel` paints a dark gradient, rounded border, and cyan highlight | Map to native design tokens rather than maintaining local hardcoded colors. |
| Status | `StatusRingWidget` maps `LISTENING`, `THINKING`, `SPEAKING`, `EXECUTING`, `ERROR`, and `IDLE` to colors and pulse animation | Use the shared semantic state model; color must be paired with text and accessible status. |
| Voice visualization | `WaveformWidget` animates five random-height bars on a 60 ms timer | Animation should reflect actual audio/activity state and honor reduced-motion preferences; do not simulate activity when idle. |
| Log | Keeps the last eight messages in a QLabel | Convert to a bounded activity projection with copyable/selectable text and explicit message severity. |
| Connectors | Polls `/api/connector/status` every 15 seconds on a daemon thread; displays up to six badges | Move polling into the runtime bridge and expose loading, disconnected, stale, and error states. |
| Input | `QLineEdit` sends text on Return; `MIC` triggers a voice-state message | Route through the canonical command/chat adapter and expose submission/loading/failure states. |
| Window controls | Minimize, hide, close/hide, drag anywhere, double-click, Escape, Alt+Space | Preserve discoverability and keyboard behavior; distinguish hide, minimize, and quit. |
| System tray | Uses `QSystemTrayIcon` with Show, Minimize, and Quit actions | Tray lifecycle belongs to the surface controller, with explicit runtime shutdown semantics. |
| Headless fallback | `HeadlessFloat` prints logs and state changes and retains speaking/muted flags | Treat as explicit capability projection, not a silent visual fallback. |

### State model currently present

The widget’s visible state is represented through `_state`, `_speaking`, `_muted`, `_minimized`, visibility, waveform activity, connector badge data, and a bounded log. The status state is a string protocol with six recognized values. The implementation does not currently expose a single immutable widget view model, so state transitions can be split across direct setters, Qt signals, timers, and callbacks.

The following normalized state should replace the local string/flag combination:

```text
FloatingWidgetState {
  visibility: visible | hidden | minimized
  runtime: starting | online | external | reconnecting | offline | error
  assistant: idle | listening | processing | speaking | executing | waiting | error
  audio: inactive | recording | playing | interrupted | muted | unavailable
  task: none | running | waiting_for_approval | completed | failed | unavailable
  connectors: loading | ready | stale | unavailable
  input: idle | submitting | disabled | error
  capabilities: { voice, taskControl, connectors, tray, graphicalDisplay }
}
```

The `LISTENING`, `THINKING`, `SPEAKING`, and `EXECUTING` states should remain semantically compatible with the existing voice/desktop contract, but `THINKING` should be presented as **processing** or **planning** in the user-facing model when the runtime can distinguish those states. `ERROR` must include a recoverable reason rather than only a red ring.

### Thread and runtime boundaries

The widget uses Qt timers and signals on the UI thread, but starts daemon threads for command submission and connector polling. The command path calls either `self._orchestrator.chat(text)` or a direct `requests.post` to `/api/chat`. The connector path independently resolves the server port and API key, optionally reading `config/api_keys.json`, then calls `/api/connector/status`.

This creates three separate ownership paths for backend communication:

| Path | Current owner | Risk |
|---|---|---|
| Orchestrated command | Optional injected orchestrator | Behavior differs depending on construction path. |
| Standalone command | Direct `requests.post` from widget | Duplicates API/auth/error handling and bypasses shared client contracts. |
| Connector refresh | Direct `requests.get` from widget | Duplicates port/key resolution and has no visible stale/error state. |

The migration should inject a `DesktopRuntimeBridge` or `FloatingRuntimeAdapter` that owns API calls, authentication, event subscriptions, task state, voice control, and connector health. The widget should only render projections and emit user intents.

### Safety and reliability findings

The current command submission truncates the displayed response to 120 characters and returns the widget to `LISTENING` after success. It does not expose task IDs, streaming, approval requests, cancellation, artifacts, verification, or a clear completed/failed distinction. It also sets `THINKING` before the background call, so a connection failure becomes a generic `ERROR` without structured recovery.

The standalone request uses a 30-second timeout and conditionally sends `X-API-Key` and `Authorization` headers. API-key lookup is duplicated between command and connector paths and may read a local JSON file. The redesign must centralize credential loading and ensure keys never enter logs, labels, tray notifications, or diagnostics by default.

`QApplication.setStyleSheet("* { font-family: ... }")` is applied globally by the widget entry path. This can unexpectedly affect other Qt surfaces when the widget is embedded in an existing application. The widget should use a scoped stylesheet or shared palette adapter instead.

### Migration recommendations

1. Keep root `float_widget.py` as a thin compatibility shim and add an import/health test for it.
2. Extract a `FloatingRuntimeAdapter` from `JarvisFloat` that consumes the canonical desktop runtime bridge.
3. Replace direct `requests` calls with the shared authenticated API/event client.
4. Replace local string states and independent flags with the normalized floating-widget state model.
5. Add visible loading, disconnected, stale connector, task waiting, approval, failed, and unavailable states.
6. Make waveform and status-ring animation event/audio-driven, bounded, interruptible, and reduced-motion aware.
7. Add accessible names and keyboard navigation for the input, mic, minimize, hide, tray, and state region.
8. Define whether close means hide, quit, or detach, and ensure the tray menu reflects the actual lifecycle.
9. Add headless tests for command, log, state, speaking, mute, and unavailable-capability behavior.
10. Integrate the widget with the shared command registry so it does not define a separate command vocabulary.

### Recommended floating-widget test matrix

| Test | Purpose |
|---|---|
| Qt construction | Confirms the widget can initialize with and without an existing `QApplication`. |
| Headless fallback | Confirms `HeadlessFloat` preserves the public state/log contract. |
| Command success/failure | Confirms loading, completion, timeout, authentication failure, and error recovery. |
| Connector polling | Confirms ready, empty, stale, unauthorized, timeout, and malformed responses. |
| State transitions | Confirms all normalized assistant/runtime/task states update text, ring, and waveform consistently. |
| Minimize/restore | Confirms the 64×64 state preserves accessibility and can be restored with mouse, Escape, tray, and hotkey. |
| Visibility/tray lifecycle | Confirms hide, show, quit, and application shutdown semantics. |
| Thread safety | Confirms worker results return through Qt signals and do not mutate widgets from background threads. |
| Credential redaction | Confirms API keys never appear in logs, labels, notifications, or exceptions. |
| Reduced motion | Confirms timers/animation are disabled or simplified when requested. |

## Additional references

[22]: ../float_widget.py "Root floating-widget compatibility shim"
[23]: ../src/brjarvis/desktop/float_widget.py "Canonical Qt floating widget and headless fallback"
[24]: ../start.py "Command-line startup path for the floating widget"
