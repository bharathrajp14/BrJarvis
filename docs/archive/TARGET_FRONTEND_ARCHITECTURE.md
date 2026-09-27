# BRJARVIS Target Frontend Architecture

**Status:** Initial target architecture  
**Date:** 2026-08-19  
**Author:** Manus AI

## Architectural intent

BRJARVIS should become one product with multiple specialized surfaces. The web command center, Personal Assistant, desktop HUD, floating widget, voice mode, vision mode, Career OS, and CLI should not become identical applications. They should become **different projections of the same capability, command, state, event, and design foundations**.

The architecture must preserve the existing Python runtime and FastAPI/WebSocket boundaries while introducing a frontend platform layer that translates runtime complexity into clear user-facing concepts.

> Internal runtime complexity should be translated into user-facing outcomes. `ParallelDAGExecutor` becomes “3 tasks running in parallel”; `ActionVerifier` becomes “Verified successfully”; a provider circuit-breaker event becomes “Gemini temporarily unavailable — switched to Claude.”

## Target architecture overview

```text
                                  BRJARVIS Runtime
       ┌────────────────────────────────────────────────────────────┐
       │ Orchestrator · Agents · Tasks · Tools · Models · Memory   │
       │ Workflows · Security · Verification · Voice · Vision      │
       └──────────────────────────────┬─────────────────────────────┘
                                      │
                    API / WebSocket / EventBus Compatibility Layer
                                      │
       ┌──────────────────────────────┴─────────────────────────────┐
       │                 Frontend Platform Core                     │
       │                                                             │
       │  Typed API clients     Event normalizer     Command registry│
       │  Capability registry   Domain projections  Error mapper    │
       └───────────────┬─────────────────┬─────────────────────────┘
                       │                 │
          ┌────────────┴───────┐   ┌─────┴──────────────────────────┐
          │ Shared State Model  │   │ Shared Design & Interaction    │
          │ server state        │   │ tokens, components, motion,   │
          │ realtime state      │   │ accessibility, shortcuts,     │
          │ UI state            │   │ approvals, responsive rules   │
          └────────────┬─────────┘   └──────────────┬─────────────────┘
                       │                            │
     ┌─────────────────┼────────────────────────────┼─────────────────┐
     │                 │                            │                 │
 Web Command      Personal Assistant       Desktop/HUD + Widget      CLI
 Center           + Task Workspace         Voice + Vision             TUI
     │                 │                            │                 │
     └─────────────────┴────────────────────────────┴─────────────────┘
                                      │
                             Career OS projection
```

## Layer responsibilities

| Layer | Owns | Must not own |
|---|---|---|
| Runtime compatibility | Existing HTTP, WebSocket, authentication, task, memory, Career OS, voice, vision, and artifact contracts | Visual layout or DOM/Qt rendering |
| Typed API clients | Request construction, response parsing, auth/session handling, retries, cancellation, and cache invalidation | Component-specific business decisions |
| Event normalizer | WebSocket/EventBus envelope parsing, deduplication, ordering, reconnect, and event-to-domain projection | Final visual treatment |
| Capability registry | Availability, health, permission, experimental state, and reason for unavailable capabilities | Secret credentials or raw provider keys |
| Command registry | Canonical command IDs, labels, shortcuts, arguments, availability, risk, and execution adapter | Surface-specific menu markup |
| Domain projections | Tasks, conversations, agents, tools, models, memory, workflows, artifacts, Career OS, and system health | Direct DOM or Qt manipulation |
| Realtime state | Streaming text, task progress, voice activity, vision processing, health transitions, and transport status | Long-term server persistence |
| UI state | Panels, modals, selection, layout, filters, active route, command palette, and local preferences | Backend records and runtime truth |
| Design system | Tokens, primitives, component behavior, accessibility, motion, and visual semantics | API calls or runtime orchestration |
| Surface applications | Composition and surface-specific workflows | Duplicated domain models, commands, events, or tokens |

## Domain model and frontend contracts

The frontend platform should define stable types around the existing backend payloads. The first contracts should be additive and adapter-based, so the current APIs remain usable.

### Capability status

```text
CapabilityStatus {
  id: string
  label: string
  availability: available | unavailable | degraded | loading | disconnected | denied | experimental
  reason?: string
  lastCheckedAt?: timestamp
  permissions?: PermissionSummary
  metadata?: Record<string, unknown>
}
```

A capability status must be explicit. The UI must never imply that a capability is working because a button exists. The same model should drive system status, model cards, voice controls, vision controls, connector badges, and command availability.

### Task projection

```text
TaskProjection {
  id: string
  goal: string
  status: created | planning | running | waiting | paused | cancelling | completed | failed | cancelled
  progress?: number
  currentStep?: string
  steps?: TaskStepProjection[]
  tools?: ToolActivitySummary[]
  artifacts?: ArtifactSummary[]
  approval?: ApprovalSummary
  verification?: VerificationSummary
  error?: UserFacingError
  startedAt?: timestamp
  updatedAt?: timestamp
}
```

The projection should support a compact task card for simple work and a timeline or DAG view for complex work. A DAG is a presentation mode selected by task complexity, not a default view for every command.

### User-facing error

```text
UserFacingError {
  code: string
  title: string
  message: string
  reason?: string
  suggestedActions?: ErrorAction[]
  diagnosticsRef?: string
  retryable: boolean
  severity: info | warning | error | critical
}
```

Raw stack traces remain diagnostics-only. Normal users should receive an understandable failure, a reason where known, and a safe next action.

### Approval summary

```text
ApprovalSummary {
  id: string
  action: string
  target?: string
  risk: low | medium | high | critical
  reason: string
  affectedResources?: ResourceSummary[]
  decisions: allow_once | deny | always_allow | require_more_context
  expiresAt?: timestamp
}
```

Approval presentation must be policy-driven. Harmless actions should not produce unnecessary prompts, and destructive or privacy-sensitive actions must not bypass the real security policy.

## State architecture

The frontend must not create one giant global store. State should be divided by source of truth and lifecycle.

| State | Examples | Owner | Persistence |
|---|---|---|---|
| Server state | Conversations, tasks, models, tools, memory, workflows, artifacts, Career OS data | Query/mutation clients and domain caches | Backend |
| Realtime state | Streaming deltas, task events, voice states, vision processing, health transitions, reconnect | Event adapter and surface runtime store | Ephemeral, with selected projections persisted by backend |
| UI state | Active route, open panels, filters, selection, modal, layout, command palette | Surface-local UI store or component state | Local preference only where useful |
| Session state | Authenticated session, WebSocket connection, workspace identity | Session adapter | Cookie/session mechanism; never expose secrets in ordinary UI |
| Capability state | Model/connector/device/voice/vision availability | Capability registry | Runtime-derived; refreshable |

Every state transition should be attributable to an API response, normalized event, command result, or user interaction. Animation must not be used as a substitute for state.

## Realtime event architecture

The current WebSocket envelope is a useful compatibility base: it already carries event identity, type, timestamp, optional conversation/task identifiers, and payload. The frontend should introduce a single normalizer with the following responsibilities:

1. Validate the envelope and reject malformed events without crashing the surface.
2. Deduplicate by `event_id`.
3. Track ordering and identify stale or late events.
4. Normalize aliases such as legacy message submission types and status spellings.
5. Convert runtime events into domain projections.
6. Batch high-frequency events for rendering without losing terminal lifecycle events.
7. Expose connection, reconnect, heartbeat, and authentication state.
8. Provide a diagnostics channel separate from the normal user activity view.

Canonical client event categories should be:

| Category | Examples |
|---|---|
| Conversation | `conversation.created`, `message.created`, `message.delta_start`, `message.delta`, `message.completed` |
| Task | `task.created`, `task.started`, `task.updated`, `task.waiting`, `task.completed`, `task.failed`, `task.cancelled` |
| Agent | `agent.planning`, `agent.executing`, `agent.waiting`, `agent.completed` |
| Tool | `tool.started`, `tool.completed`, `tool.failed` |
| Safety | `permission.requested`, `permission.resolved`, `verification.completed`, `verification.failed` |
| Artifact | `artifact.created`, `artifact.updated`, `artifact.failed` |
| Runtime | `model.connected`, `model.disconnected`, `system.health_changed`, `session.ready` |
| Voice/vision | `voice.listening`, `voice.speaking`, `voice.interrupted`, `vision.started`, `vision.completed`, `vision.failed` |
| Transport | `connection.open`, `connection.reconnecting`, `connection.closed`, `connection.error` |

Surface-specific adapters should subscribe to the normalized stream; they should not each subscribe to raw EventBus topics or independently interpret WebSocket payloads.

## Canonical command architecture

The command registry is the shared action model for the web command palette, Personal Assistant shortcuts, floating widget, desktop actions, and CLI slash commands.

```text
CommandDefinition {
  id: string
  label: string
  description: string
  group: assistant | tasks | automation | memory | career | system | navigation
  aliases: string[]
  shortcut?: string
  argumentSchema?: Schema
  availability: CapabilityRequirement[]
  risk: safe | confirm | destructive | privacy_sensitive
  execute: CommandAdapterReference
  surfaces: web | assistant | widget | desktop | cli
}
```

Examples include opening Assistant, opening Career OS, starting focus mode, running an automation, searching memory, analyzing the screen, switching models, showing status, and cancelling the active task. The registry must not contain direct DOM or Qt code. Each surface supplies an adapter.

## Surface architecture

### Unified application shell

The shell owns identity, grouped navigation, global status, notifications, command palette, global shortcuts, theme, responsive layout, and session state. It does not own page-specific data fetching.

Recommended navigation grouping:

| Group | Destinations |
|---|---|
| BRJARVIS | Home, Assistant, Tasks, Automations, Memory, Career OS, Files |
| Intelligence | Agents, Models, Tools |
| System | Activity, System, Settings |

The shell should support desktop and laptop layouts directly. Tablet and smaller-screen layouts should reorganize content into drawers, sheets, and focused workspaces rather than simply shrinking desktop columns.

### Personal Assistant workspace

The assistant surface combines conversation with task execution. Its default view contains context, transcript, composer, attachments, voice controls, model selection, and a compact execution summary. It can expand into task steps, tool activity, approvals, artifacts, verification, diagnostics, and recovery.

### Web command center

Home should prioritize current work, pending decisions, failures, follow-ups, recent memory, automation status, and system availability. It should not render a grid of unrelated metrics. Each page should be a domain projection over real API data with explicit empty, loading, unavailable, and error states.

### Desktop/HUD and floating widget

The desktop surfaces should share the same state and command contracts as the web client but can use native layouts and shortcuts. The floating widget is a compact projection optimized for speed: idle presence, listening/transcript, processing, executing, approval, completion, error, and quick command.

### CLI

The CLI remains terminal-native and should retain its existing prompt-toolkit, Rich, interactive TUI, mouse, history, approval, and interruption capabilities. Its command definitions and task projections should come from the canonical registry and shared contracts.

### Career OS

Career OS is a domain workspace within the shell. It should project existing profile, resume, ATS, jobs, applications, analytics, interview, email, and CRM data into Overview, Profile, Skills/Evidence, Job Intelligence, Application Pipeline, and Advisor views. Unsupported derived values must be marked unavailable rather than fabricated.

## Design-system boundary

Design tokens should be semantic and surface-neutral. The web system may use CSS variables, while Qt and terminal renderers use mapped token values. The token names should describe meaning rather than hardcoded appearance:

| Semantic token family | Examples |
|---|---|
| Surface | `surface.canvas`, `surface.panel`, `surface.elevated`, `surface.inverse` |
| Text | `text.primary`, `text.secondary`, `text.muted`, `text.onAccent` |
| Action | `action.primary`, `action.secondary`, `action.focus`, `action.disabled` |
| Status | `status.info`, `status.success`, `status.warning`, `status.error`, `status.critical` |
| Border | `border.subtle`, `border.default`, `border.strong`, `border.focus` |
| Motion | `motion.fast`, `motion.normal`, `motion.slow`, `motion.reduced` |

The system should be dark-first, calm, technical, and information-dense. Neon, gradients, glass effects, and animation should be used only when they communicate hierarchy or state.

## Security and privacy boundary

The frontend must never display API keys in ordinary settings views. Authentication should be handled through session or secure configuration flows. Screen, memory, artifact, file, and credential displays require privacy-aware redaction and permission checks. Approval dialogs must show the action, target, risk, reason, affected resources, and available decisions without exposing unrelated sensitive content.

## Migration boundary

The migration should follow a strangler pattern:

1. Keep existing routes and launchers working.
2. Add frontend platform contracts and adapters.
3. Mount the new shell beside the legacy static client.
4. Implement one end-to-end assistant/task vertical slice.
5. Move views behind feature flags or route-level cutovers.
6. Keep the compatibility adapter until the new surface passes functional and regression gates.
7. Remove legacy code only after usage and rollback evidence.

The architecture is complete only when a surface can consume real runtime state, handle transport and domain failures, expose safe recovery, meet accessibility requirements, and pass tests under streaming and reconnect conditions.

## References

[1]: ./FRONTEND_AUDIT.md "Repository-grounded frontend and runtime audit"
[2]: ../src/brjarvis/web/api/server.py "FastAPI application factory and route registration"
[3]: ../src/brjarvis/web/api/routes/websocket.py "WebSocket event envelope and chat/task protocol"
[4]: ../src/brjarvis/core/terminal/session.py "CLI session and EventBus integration"
[5]: ../src/brjarvis/career/api_routes.py "Career OS API capabilities"
[6]: ../src/brjarvis/ui/main_window.py "Desktop UI capabilities and Qt integration"


## Native desktop and launcher architecture

The repository contains several desktop entry wrappers, but they converge on one native UI stack. The root `ui_mark.py` delegates to `brjarvis.apps.desktop.main()` and forwards compatibility helpers to `brjarvis.desktop.ui_mark`. The root `ui.py` provides legacy package/import compatibility and also delegates to the canonical desktop entry point. Neither root file should own new UI, runtime, or design-system behavior.

The actual native launch sequence currently belongs to `src/brjarvis/desktop/ui_mark.py`. It selects a stable Python interpreter on affected Windows environments, configures Qt paths, detects PySide6/PyQt6, chooses `JarvisUI` or `HeadlessJarvisUI`, starts an embedded FastAPI/Uvicorn server thread, starts a `BRVoiceAssistant` worker thread, configures remote credentials, installs signal handlers, and blocks on the native or headless loop.

This launch behavior should be separated into explicit runtime services:

```text
DesktopLauncher
   ├── RuntimeLifecycleService
   │      ├── embedded/external backend ownership
   │      ├── port and health state
   │      ├── start/stop/reconnect
   │      └── shutdown coordination
   ├── VoiceRuntimeBridge
   │      ├── listening/speaking/interrupted/error
   │      ├── stop-speech command
   │      └── transcript/activity events
   ├── DesktopRuntimeBridge
   │      ├── task and agent projections
   │      ├── approval and verification
   │      ├── files and camera/vision state
   │      └── user command routing
   └── DesktopSurface
          ├── JarvisUI / MainWindow
          └── HeadlessJarvisUI
```

The `DesktopRuntimeBridge` is the native equivalent of the browser platform adapter. It should translate backend, EventBus, voice, vision, and task lifecycle events into typed native state and expose commands back to the runtime. Qt widgets should subscribe to that bridge rather than starting worker threads, calling APIs, or interpreting raw events individually.

### Embedded versus external backend state

Because the desktop launcher can reuse an existing JARVIS server or start an embedded server on a selected port, the UI must expose backend ownership explicitly:

| State | Meaning | User-facing presentation |
|---|---|---|
| `embedded_starting` | This desktop process is launching the backend | Starting runtime |
| `embedded_online` | The desktop process owns the backend | Runtime online · embedded |
| `external_online` | A compatible JARVIS backend is already running | Runtime online · external |
| `port_conflict` | Preferred port belongs to another service | Selecting safe fallback port |
| `unavailable` | Backend could not start or connect | Runtime unavailable with retry/diagnostics |
| `shutting_down` | Shutdown sequence is in progress | Stopping runtime |

This state must be shared with the floating widget and headless interface. It should not be inferred from whether the Qt window is visible.

### Native/headless capability parity

`HeadlessJarvisUI` is a compatibility implementation of the `JarvisUI` contract. It can accept text commands, expose speaking/mute/state properties, show content and alerts through logging, maintain agent task records, and run a stdin loop. Camera and visual display methods are currently no-ops in headless mode. That is acceptable only when the UI explicitly reports the capability as unavailable rather than silently presenting controls that cannot work.

The native bridge should therefore expose capability metadata for both modes:

```text
DesktopCapabilities {
  graphicalDisplay: available | unavailable
  voice: available | unavailable | degraded
  camera: available | unavailable | denied
  screenVision: available | unavailable | denied
  embeddedBackend: available | unavailable | not_owned
  taskControl: available | unavailable
}
```

## References

[7]: ../ui_mark.py "Root desktop launcher compatibility shim"
[8]: ../ui.py "Root UI package compatibility shim"
[9]: ../src/brjarvis/desktop/ui_mark.py "Full-stack native desktop/voice launcher"
[10]: ../src/brjarvis/ui/app.py "JarvisUI and HeadlessJarvisUI compatibility contract"
[11]: ../src/brjarvis/ui/__init__.py "Native UI package bootstrap and lazy exports"
[12]: ../src/brjarvis/apps/desktop.py "Canonical desktop launcher entry point"


## Floating widget architecture

The floating widget is a distinct native surface with compact, persistent interaction semantics. It should not own backend communication, authentication, connector polling, or task interpretation. Its future boundary is:

```text
FloatingSurface
   ├── Native presentation
   │      ├── status ring
   │      ├── waveform
   │      ├── bounded activity log
   │      ├── command input
   │      └── tray/minimize controls
   └── FloatingRuntimeAdapter
          ├── authenticated API client
          ├── normalized event subscription
          ├── voice control
          ├── connector health
          ├── task/approval projection
          └── capability/error mapping
```

The adapter should expose a single immutable projection to Qt and a matching headless projection. Direct `requests` calls, API-key lookup, server-port discovery, and orchestration branching currently inside `src/brjarvis/desktop/float_widget.py` should move below this boundary.

The floating surface should consume the shared command registry and normalized event envelope. It must support explicit `visible`, `hidden`, and `minimized` states, plus assistant/runtime states such as `idle`, `listening`, `processing`, `speaking`, `executing`, `waiting`, `reconnecting`, and `error`. A status ring or waveform is an indicator only; the state label and accessible announcement remain authoritative.

The widget’s always-on-top and system-tray behavior also requires a lifecycle contract. Hiding the window, minimizing to the tray bubble, closing the surface, and quitting the process must be distinct commands with documented effects. The widget must not terminate the embedded backend or voice worker unless the runtime lifecycle service explicitly owns that shutdown.
