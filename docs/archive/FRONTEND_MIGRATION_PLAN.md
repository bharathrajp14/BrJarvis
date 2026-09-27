# BRJARVIS Frontend Migration Plan

**Status:** Initial execution plan  
**Date:** 2026-08-19  
**Author:** Manus AI

## Migration objective

Move BRJARVIS from several partially independent user interfaces to one capability-backed frontend platform without breaking the existing Python runtime, API routes, WebSocket behavior, security controls, memory, voice, vision, workflows, Career OS, or CLI operation.

The migration uses an **audit-first strangler strategy**. New contracts and shared foundations are added beside existing surfaces. One real end-to-end vertical slice is validated before broad surface migration. Legacy routes and launchers remain available until replacement evidence supports removal.

## Non-negotiable constraints

| Constraint | Implementation rule |
|---|---|
| Preserve working runtime | Do not replace backend APIs or orchestration merely to simplify frontend work. |
| No fake functionality | A control must be backed by a real capability or show why it is unavailable. |
| No hidden chain-of-thought | Show execution summaries, steps, tools, results, approvals, verification, and diagnostics—not private reasoning traces. |
| One command architecture | GUI, floating widget, web, and CLI consume one canonical command registry. |
| One realtime model | Surfaces consume normalized events, not incompatible hand-built event handlers. |
| Safe changes | Work from an isolated branch/worktree because the current tree contains unrelated modifications. |
| Measured performance | Instrument event/render behavior before adding optimizations. |
| Complete features | UI, state, API/event connection, loading, error, safety, accessibility, testing, and documentation are all required. |

## Workstream sequence

```text
Baseline protection
      ↓
Complete audit and contract inventory
      ↓
Target architecture + design tokens
      ↓
Unified shell + command/event adapters
      ↓
Assistant vertical slice
      ↓
Assistant + task execution
      ├── Floating widget / voice / vision
      ├── Web command center
      ├── Career OS
      └── CLI adapter
      ↓
Performance, accessibility, security, migration, and deprecation
```

## Phase plan

### Phase 0 — Baseline protection

**Purpose:** prevent the redesign from overwriting unrelated development work.

**Actions:**

1. Record branch, commit, working-tree status, startup commands, supported environment, and current test commands.
2. Create a dedicated redesign branch or isolated worktree.
3. Preserve existing modifications and untracked files; do not run broad formatters or automated codemods.
4. Record current web, WebSocket, CLI, Career OS, and smoke-test status.

**Deliverables:** baseline report, isolated workspace, startup/test notes, and list of pre-existing failures.

**Gate:** the redesign workspace is isolated and current changes are recoverable.

### Phase 1 — Frontend audit

**Purpose:** eliminate uncertainty about existing UI entry points, dependencies, APIs, events, and duplication.

**Actions:**

1. Complete the inventory in `docs/FRONTEND_AUDIT.md`.
2. Parse the complete browser HTML/CSS to enumerate views, modals, navigation, responsive behavior, and data attributes.
3. Extract all REST route decorators, schemas, authentication conditions, and response shapes used by the browser.
4. Trace EventBus producers to event contracts and document payload stability.
5. Map desktop and floating-widget callbacks, timers, signals, and EventBus subscriptions.
6. Verify the static build/distribution pipeline and whether `static/dist` is authoritative.
7. Map existing tests to each surface and identify untested critical paths.

**Deliverables:** completed audit, route/event matrix, surface dependency map, duplication register, and priority map.

**Gate:** every user-facing surface and runtime dependency is accounted for.

### Phase 2 — Contract and target architecture

**Purpose:** create stable frontend boundaries without changing runtime behavior.

**Actions:**

1. Define typed domain projections for conversations, messages, tasks, agents, tools, models, memory, workflows, artifacts, approvals, verification, voice, vision, health, and Career OS.
2. Define the normalized realtime event envelope and client event adapter.
3. Define capability status and user-facing error contracts.
4. Define the canonical command registry with aliases, shortcuts, availability, risk, and surface adapters.
5. Define server-state, realtime-state, UI-state, session-state, and capability-state ownership.
6. Establish dependency direction: presentation → domain projections → adapters/clients → runtime contracts.

**Deliverables:** `docs/TARGET_FRONTEND_ARCHITECTURE.md`, contract schemas, adapter interfaces, and compatibility notes.

**Gate:** the first vertical slice can be implemented without duplicating API/event/command logic.

### Phase 3 — Design-system foundation

**Purpose:** establish one visual and interaction language across all surfaces.

**Actions:**

1. Implement semantic color, typography, spacing, radius, elevation, z-index, motion, focus, and responsive tokens.
2. Build cross-domain primitives and state components.
3. Map web tokens to CSS, desktop tokens to Qt palette/style helpers, and terminal tokens to Rich/theme values.
4. Implement keyboard, focus, semantic labels, reduced motion, contrast, loading, error, empty, unavailable, and disconnected states.
5. Add component tests and visual regression fixtures where the platform supports them.

**Deliverables:** `docs/DESIGN_SYSTEM.md`, token implementation, reusable primitives, accessibility utilities, and component fixtures.

**Gate:** the shell and assistant can be composed without ad-hoc visual primitives.

### Phase 4 — Unified shell and command/event platform

**Purpose:** create the shared application frame and platform services.

**Actions:**

1. Build grouped navigation and route composition.
2. Add session/auth handling through a typed client boundary.
3. Add normalized WebSocket connection, reconnect, heartbeat, ticket/session, and error handling.
4. Add domain projections for task, conversation, message, artifact, and health events.
5. Add command registry and command palette.
6. Add global status, notifications, shortcuts, theme, and responsive shell behavior.
7. Keep legacy root and `/web` access paths functional during rollout.

**Deliverables:** application shell, command palette, event adapter, domain stores/projections, and compatibility route.

**Gate:** the new shell can render real connection and health state and can invoke one safe canonical command.

### Phase 5 — Assistant vertical slice

**Purpose:** prove the architecture with a complete real workflow.

**Workflow:**

```text
Authenticate
  → connect WebSocket
  → submit prompt
  → receive task/message lifecycle
  → stream response
  → show task summary
  → show approval if required
  → complete/fail
  → display result/artifact
  → retry/cancel/recover
```

**Required states:** loading, streaming, waiting for approval, paused, cancelling, completed, failed, disconnected, reconnecting, provider unavailable, and session expired.

**Deliverables:** real assistant workspace, task card/timeline, streaming transcript, approval state, error/recovery state, and end-to-end tests.

**Gate:** one real task satisfies the complete definition of done.

### Phase 6 — Personal Assistant migration

**Purpose:** migrate the primary user experience onto the new platform.

**Scope:** conversation, streaming, task planning summary, progress, tool activity, artifacts, memory context, model selection, follow-up, cancellation, retry, recovery, voice launch, and vision launch.

**Migration control:** run the new assistant behind a route or feature flag while the legacy workspace remains available for rollback.

**Gate:** feature parity for supported existing flows, plus improved status/error/accessibility behavior.

### Phase 7 — Floating widget, voice, and vision

**Purpose:** make fast interaction and multimodal control consistent with the new platform.

**Scope:** idle, listening, processing, speaking, interrupted, executing, approval, completion, error, disconnected, transcript, audio activity, screen selection, privacy indicators, detected applications, analysis result, and permitted actions.

**Special requirements:** voice interruption must stop TTS and visibly transition to new-input processing. Vision must never silently disclose sensitive screen content.

**Gate:** widget, voice, and vision consume the canonical command and event contracts.

### Phase 8 — Web command center

**Purpose:** migrate operational views from dashboard-style presentation to decision-oriented command center.

**Scope:** Home, Assistant, Tasks, Agents, Automations, Memory, Models, Tools, Activity, Files, System, and Settings.

**Page acceptance rules:** every page must use real data, support loading/empty/unavailable/error states, enforce permissions, and provide a useful recovery action where possible. Home must prioritize current activity, approvals, failures, follow-ups, recent memory, and automation status.

**Gate:** no page consists only of decorative metric cards or dead actions.

### Phase 9 — Career OS

**Purpose:** make Career OS a real evidence-backed intelligence workspace.

**Scope:** profile, onboarding, resume versions/templates, tailoring, ATS, job search/matching, applications, analytics, interview preparation, email intelligence, CRM events, interviews, offers, and advisor projections.

**Safety rule:** unsupported career scores, skill gaps, or recommendations are not shown as facts. Use real backend data or an explicit unavailable state.

**Gate:** Career OS reads and writes existing data correctly and passes lifecycle integration tests.

### Phase 10 — CLI migration

**Purpose:** make the CLI a first-class projection of the shared platform.

**Scope:** canonical commands, history, autocomplete, suggestions, slash commands, streaming, structured task views, progress, tables, diagnostics, approval, interrupt, and keyboard/mouse behavior.

**Gate:** commands defined once are discoverable and semantically consistent across CLI, web, assistant, and widget.

### Phase 11 — Hardening and observability

**Purpose:** validate the new surfaces under realistic runtime conditions.

**Performance checks:** measure startup, first interaction, streaming latency, event-to-render latency, event burst behavior, memory usage, list growth, and task update cost.

**Accessibility checks:** keyboard traversal, focus restoration, screen-reader labels, contrast, reduced motion, scalable text, error announcements, and shortcut discoverability.

**Security checks:** auth expiry, WebSocket ticket/session handling, redaction, memory privacy, screen privacy, destructive approvals, credential handling, and diagnostics access.

**Gate:** no critical accessibility, privacy, approval, blocking-UI, or unbounded-rendering defects.

### Phase 12 — Cutover and deprecation

**Purpose:** remove duplication only after replacement evidence exists.

**Actions:**

1. Compare new and legacy route usage.
2. Confirm regression coverage and rollback procedure.
3. Deprecate legacy pages or components behind documented migration notices.
4. Remove obsolete code in small, reviewable commits.
5. Retain compatibility shims for external launchers and scripts until their callers are migrated.
6. Update architecture and operational documentation.

**Gate:** rollback remains possible until the new surface has been stable through an agreed observation period.

## Definition of done

A feature is complete only when the following table is satisfied.

| Dimension | Evidence required |
|---|---|
| UI | Shared components and intended interaction render correctly. |
| State | Server, realtime, UI, session, and capability ownership is explicit. |
| Integration | Real API, command, runtime, or event connection exists. |
| Loading | Initial, delayed, streaming, reconnect, and pending states are handled. |
| Errors | User-facing, actionable, redacted error state exists. |
| Safety | Permissions, privacy, risk, and approval behavior is enforced. |
| Accessibility | Keyboard, focus, semantics, labels, contrast, and reduced motion pass. |
| Performance | Behavior is measured under realistic event/task load. |
| Testing | Unit, integration, E2E, and regression coverage exists at the appropriate level. |
| Documentation | Contract, behavior, limitations, and migration notes are updated. |

## Test matrix

| Area | Required coverage |
|---|---|
| Web routes | Auth, health, conversations, tasks, artifacts, memory, automation, voice, Career OS, versioned routes |
| WebSocket | Ticket/session auth, origin checks, heartbeat, reconnect, malformed payloads, streaming, lifecycle events, event deduplication |
| Assistant | Submit, stream, plan-only, approval, cancel, retry, failure, artifact result, follow-up |
| Desktop | Startup, headless fallback, keyboard shortcuts, state callbacks, task updates, camera failure, overlay behavior |
| Floating widget | All runtime states, command invocation, mic interruption, hide/show, disconnected behavior |
| CLI | History, autocomplete, slash commands, task stream, approval, interruption, narrow terminal, mouse mode |
| Career OS | Profile lifecycle, resume creation/tailoring, ATS, jobs, applications, interviews, offers, CRM/email flows |
| Accessibility | Keyboard, focus, labels, contrast, reduced motion, responsive behavior |
| Performance | Streaming, event burst, long-running task, many tasks, large activity history, reconnect |
| Security | Auth expiry, redaction, permission denial, destructive actions, privacy-sensitive vision/memory/file views |

## Rollback strategy

Rollback must operate at the surface level. A failed new web shell should be switchable back to the legacy static client without changing runtime data. A failed desktop component should be replaceable through the existing `JarvisUI`/`HeadlessJarvisUI` compatibility seam. CLI command changes should preserve existing command aliases until the new registry is proven.

Every migration step should have a documented feature flag, route switch, or adapter removal point. Deleting old code before the replacement has passed its gate is prohibited.

## Immediate next implementation slice

The next coding slice should be the **frontend platform core plus assistant vertical slice**:

1. Add a typed compatibility client for the existing `/api` and `/api/v1` routes.
2. Add a normalized WebSocket event adapter over the existing envelope.
3. Add canonical task/message projections and user-facing error mapping.
4. Add a minimal semantic token layer and shell scaffold.
5. Implement one real prompt-to-stream-to-result flow with loading, reconnect, failure, cancellation, approval, and accessibility coverage.

Do not begin with Career OS, a full dashboard, or a visual-only rewrite. The vertical slice establishes whether the proposed architecture can safely reflect the existing runtime.

## References

[1]: ./FRONTEND_AUDIT.md "Repository-grounded frontend and runtime audit"
[2]: ./TARGET_FRONTEND_ARCHITECTURE.md "Target frontend architecture and shared contracts"
[3]: ./DESIGN_SYSTEM.md "Shared design-system specification"
[4]: ../src/brjarvis/web/api/routes/websocket.py "Existing WebSocket compatibility boundary"
[5]: ../src/brjarvis/web/api/server.py "Existing FastAPI route and static-serving boundary"
[6]: ../src/brjarvis/core/terminal/session.py "Existing CLI session behavior"
[7]: ../tests/integration/test_fastapi_web_routes.py "Existing web route integration tests"
[8]: ../tests/integration/test_websocket_hub.py "Existing WebSocket integration tests"


## First redesign slice completed

The initial compatibility slice was implemented without replacing the legacy browser client. The new platform foundation is loaded before the existing client and receives bridged lifecycle/messages from it.

| Implemented item | Location | Status |
|---|---|---|
| Normalized event, task, capability, risk, and error contracts | `src/brjarvis/web/static/platform/contracts.js` | Implemented |
| Realtime event adapter with deduplication and task/message projections | `src/brjarvis/web/static/platform/event-adapter.js` | Implemented |
| Typed compatibility API client and WebSocket ticket method | `src/brjarvis/web/static/platform/api-client.js` | Implemented |
| Canonical command registry with availability/risk checks | `src/brjarvis/web/static/platform/command-registry.js` | Implemented |
| Browser platform bootstrap | `src/brjarvis/web/static/platform/bootstrap.js` | Implemented |
| Unified shell connection status and navigation adapter | `src/brjarvis/web/static/platform/shell.js` | Implemented |
| Live assistant task projection | `src/brjarvis/web/static/platform/assistant.js` | Implemented |
| Canonical command palette integration | `src/brjarvis/web/static/platform/palette.js` | Implemented |
| Semantic tokens, focus, reduced motion, task projection, and command palette styles | `src/brjarvis/web/static/style.css` | Implemented |
| Legacy WebSocket lifecycle/message bridge | `src/brjarvis/web/static/app.js` | Compatibility change only |
| Platform bootstrap loading | `src/brjarvis/web/static/index.html` | Compatibility change only |

The current backend exposes task creation and approval routes but no task-cancellation endpoint. Cancellation is therefore represented as an explicit unavailable capability rather than a dead button or fake action. A real cancellation control should be enabled only after a backend endpoint and policy contract are added.

Validation completed after this slice:

```text
JavaScript syntax checks: passed
Git diff check for static assets: passed
Protected regression suites: 57 passed, 1 Pytest configuration warning
```

The next implementation stage is to add a real approval/task-control contract where backend support exists, then migrate the assistant workspace from the legacy global DOM controller onto the new projections incrementally. Full command-center, floating-widget, voice/vision, Career OS, CLI, performance, and accessibility migrations remain pending.


## Native desktop migration update

The focused `ui_mark.py`/`ui.py` audit changes the native migration sequence. The root files remain compatibility shims and should not receive new rendering or runtime logic. Native work should proceed through the canonical `JarvisUI`/`HeadlessJarvisUI` contract and the actual `src/brjarvis/ui` component layer.

Before redesigning the Qt HUD or floating widget, add a desktop runtime bridge with explicit lifecycle ownership:

| Bridge responsibility | Required behavior |
|---|---|
| Backend ownership | Distinguish embedded backend, external backend, port conflict, unavailable, and shutting-down states. |
| Voice control | Replace direct `ui.on_interrupt = assistant.stop_speech` coupling with typed interruption and speaking/listening events. |
| Task projections | Feed task, agent, tool, approval, verification, and artifact state into native widgets. |
| Vision/camera | Expose camera, screen, privacy, and processing capabilities explicitly. |
| Headless parity | Keep text-command, task, voice-state, and error behavior functional while reporting graphical features as unavailable. |
| Lifecycle | Coordinate backend, voice worker, Qt loop, headless loop, and shutdown without making widgets own daemon threads. |
| Remote pairing | Keep credential generation and dashboard pairing behind explicit security state and redaction. |

The updated native order is therefore:

```text
Preserve root shims
  → add launcher/runtime lifecycle contract
  → add DesktopRuntimeBridge
  → map JarvisUI and HeadlessJarvisUI states
  → migrate MainWindow/HUD widgets
  → migrate floating widget
  → unify voice/vision events
  → test embedded/external/headless lifecycle
```

This work is a prerequisite for claiming the desktop, floating, voice, or vision surfaces complete. A visual Qt redesign without lifecycle and capability integration would violate the project’s no-fake-functionality requirement.


## Floating-widget migration update

The floating widget should migrate after the desktop runtime bridge exists and before claiming voice/vision parity across surfaces. It currently combines visual presentation, direct HTTP calls, credential lookup, connector polling, worker threads, Qt timers, tray lifecycle, and headless fallback in one module.

The required sequence is:

```text
Preserve root float_widget.py shim
  → extract FloatingRuntimeAdapter
  → centralize authenticated API/event access
  → normalize assistant/audio/task/runtime state
  → migrate Qt projection and headless projection
  → add approval/error/disconnected/loading states
  → validate tray, hotkey, minimize, hide, quit, and shutdown semantics
```

The first implementation slice for the widget should not be a visual rewrite. It should introduce the runtime adapter and state projection while retaining the current glass panel, waveform, status ring, input, connector badges, and tray behavior. This provides rollback and makes it possible to test state correctness independently from styling.

A floating-widget feature is complete only when command submission, voice trigger, task progress, connector health, errors, credentials, accessibility, reduced motion, headless behavior, and lifecycle semantics are all covered. In particular, the widget must not show animated thinking or waveform activity unless an actual runtime/audio event supports that state.


## Floating-widget runtime upgrade completed

The first floating-widget upgrade slice is now implemented without replacing the existing Qt presentation or root launcher shim.

| Upgrade | Implementation |
|---|---|
| Explicit state projection | `src/brjarvis/desktop/floating_runtime.py` adds `FloatingWidgetState`. |
| Runtime boundary | `FloatingRuntimeAdapter` owns command execution, connector polling, auth headers, capability state, and worker threads. |
| Qt integration | `JarvisFloat` now consumes adapter snapshots through Qt signals and keeps widget mutation on the UI thread. |
| Headless parity | `HeadlessFloat` uses the same adapter and exposes command, voice, connector, state, speaking, and mute behavior. |
| Input state | The widget visibly disables input while a command is being submitted and restores it after completion/failure. |
| Error handling | Command and connector failures become bounded user-facing state instead of direct background-widget mutation. |
| Credential boundary | API-key lookup is centralized in the adapter and is not included in state/log output. |
| Tests | `tests/unit/test_floating_runtime.py` covers state subscriptions, command success/failure, and unavailable voice capability. |

Validation result after the upgrade:

```text
61 passed, 1 Pytest configuration warning
```

The remaining work is visual token migration, real streaming/task/approval integration, audio-driven waveform state, tray/lifecycle tests, and a full Qt environment test when PySide6 is available in the supported runtime.


## Full floating-widget redesign completed

The floating widget has been reworked as a compact assistant command dock rather than a miniature dashboard. The implementation specification is documented in `docs/FLOATING_WIDGET_REDESIGN.md`.

The redesign introduces three intentional modes: a default Dock for quick commands and runtime status, a Task view for active execution/approval context, and a Tray bubble for minimal presence. It preserves the existing always-on-top, drag, hotkey, tray, headless, connector, and command compatibility boundaries while replacing the presentation and state flow.

The implementation was corrected through actual failing tests rather than only syntax inspection. The discovered defects included minimized geometry not respecting the requested bubble size, asynchronous error assertions racing the worker, and capability defaults incorrectly disabling connectors when voice was absent. These were fixed and the focused suite now passes.

Final validation:

```text
68 passed, 1 existing Pytest configuration warning
```

The passing set includes offscreen Qt tests, headless projection tests, mocked authentication/HTTP, connector health, voice callback behavior, command success/failure, web routes, WebSocket behavior, CLI behavior, and Career OS integration.
