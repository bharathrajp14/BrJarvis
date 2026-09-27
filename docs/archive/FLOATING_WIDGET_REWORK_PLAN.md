# BRJARVIS Floating Widget — Proper Rework Plan

**Status:** Plan before implementation  
**Date:** 2026-08-19  
**Author:** Manus AI

## 1. Why the previous rework is being rejected

The previous version was technically more structured, but it still behaved like a compressed collection of controls rather than a deliberately designed product surface. The visual audit shows a narrow panel with too many equally weighted elements, weak grouping, insufficient readable hierarchy, and little distinction between the assistant’s primary action and secondary status information.

The current implementation also makes the surface responsible for too many concerns at once: Qt drawing, runtime state translation, connector refresh, voice availability, command submission, tray lifecycle, and workspace launch. The next rework must separate **product experience**, **native presentation**, and **runtime integration**.

> The redesigned widget should be a calm, glanceable assistant companion—not a miniature dashboard and not a decorative cyberpunk panel.

## 2. Product concept: the Assistant Orb + Command Rail

The new floating widget has one primary job: provide an immediate path from **presence → intent → feedback → recovery**.

It consists of two coordinated surfaces:

| Surface | Role | Default behavior |
|---|---|---|
| **Orb** | Persistent presence and state | Always visible as a small status orb when minimized; expands on click/hotkey. |
| **Command Rail** | Focused interaction | Opens as a clean horizontal/vertical dock with one command input and one current-activity card. |

The user should not see connectors, telemetry, task graphs, or multiple action rows by default. Those appear only when relevant or explicitly opened.

### Primary user question

At a glance, the user should be able to answer:

1. **Is JARVIS connected?**
2. **What is JARVIS doing now?**
3. **What can I do next?**
4. **Is there anything that needs my approval?**

## 3. Surface modes

### Mode A — Orb

The orb is a 56–64 px circular native window with a soft semantic halo. It displays one state indicator and a short accessible label. It supports click-to-expand, Alt+Space, and a context menu. No continuous decorative animation is permitted when idle.

| Orb state | Visual | Action |
|---|---|---|
| Offline | Muted neutral ring | Expand to retry/open diagnostics |
| Online/idle | Calm cyan point | Expand command rail |
| Listening | Cyan ring with restrained pulse | Stop/cancel listening if supported |
| Processing | Amber ring, no fake waveform | Expand to current activity |
| Speaking | Green ring/audio indicator | Interrupt speech when supported |
| Approval | Amber badge or split ring | Expand directly to approval details |
| Error | Red edge, static | Expand to recovery message |

### Mode B — Command Rail

The command rail is the primary expanded surface. It should be approximately 420–480 px wide and 170–220 px high at default scale.

```text
┌─────────────────────────────────────────────────────────────┐
│  ●  BR JARVIS                         Online · external   − × │
│     Ready                                                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Ask JARVIS…                                      MIC  → │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  Ready for a command          Open workspace  •  Task  •  ⋯  │
└─────────────────────────────────────────────────────────────┘
```

The command rail has only four persistent elements: identity/runtime, state/activity, command input, and a small secondary action strip. The task card, connector status, approval prompt, and error recovery card replace the activity area only when relevant.

### Mode C — Context card

The context card is an expanded state, not another permanent panel. It is used for:

- Active task with real progress/current step.
- Approval request with risk and decision actions.
- Error with retry/switch/open-diagnostics actions.
- Voice transcript and interruption state.
- Connector failure or stale health.

Context cards should be vertically stacked and dismissible. They must not create an unbounded log inside the widget.

## 4. Visual direction

The visual language is **quiet technical utility**:

| Area | Decision |
|---|---|
| Color | Near-black blue-gray background, warm white text, cyan primary accent, semantic amber/green/red only for status. |
| Surface | One clean panel with a thin border and restrained shadow; no heavy glass gradients. |
| Identity | Small “BR JARVIS” wordmark with a clear state dot; avoid oversized cyberpunk labels. |
| Typography | Use robust system fonts first: Segoe UI, Inter, Arial, sans-serif. Use monospace only for status metadata. |
| Hierarchy | Title → state → activity/input → secondary actions. Never make all controls look equally important. |
| Shape | 14–18 px panel radius, 8–10 px controls, 999 px status pills only where they clarify state. |
| Motion | State transition only; no random idle pulse or fake thinking animation. |
| Density | Minimum 11–12 px body text at normal scale; compact does not mean unreadable. |

The visual implementation must be tested with system fonts available on Windows and in Qt offscreen mode. It must not depend on a missing downloaded font directory.

## 5. Interaction rules

### Command input

The input is the only primary action. Enter submits once. The input remains visible during processing but becomes disabled with a clear “Processing…” label. On failure, the draft is restored and the user receives Retry and Open workspace actions.

### Voice

The mic action is enabled only when a real voice callback/runtime is connected. When unavailable it must be visibly disabled and labelled “Voice unavailable”; it must not silently change the state to Listening.

### Task

The widget shows only a compact current-task summary. A Stop action appears only when the backend exposes a real task-control capability. Approval requests are always explicit and take precedence over generic activity.

### Tray and window behavior

- **Orb click:** expand command rail.
- **Minimize:** collapse to orb while keeping runtime alive.
- **Hide:** remove the surface but keep it available through tray/hotkey.
- **Close button:** hide, not quit.
- **Quit tray action:** explicit process quit path.
- **Alt+Space:** toggle orb/rail visibility.
- **Escape:** collapse context/rail; do not silently cancel work.

## 6. Runtime architecture

```text
FloatingRuntimeAdapter
   ├── RuntimeHealthProjection
   ├── AssistantStateProjection
   ├── CommandController
   ├── VoiceController
   ├── Task/ApprovalProjection
   ├── ConnectorHealthProjection
   └── LifecycleController

FloatingSurfaceController
   ├── OrbSurface
   ├── CommandRailSurface
   ├── ContextCardSurface
   └── TrayController
```

The runtime adapter owns authenticated HTTP/event access, capability detection, worker execution, lifecycle ownership, and normalized state. The surface controller owns geometry, painting, controls, focus, keyboard, and visual transitions. Neither the surface nor the root launcher shim owns credentials, backend threads, or raw API calls.

## 7. State contract

The state model should be explicit and testable:

```text
FloatingViewState {
  mode: orb | rail | context
  runtime: starting | embedded_online | external_online | reconnecting | offline | error
  assistant: idle | listening | processing | speaking | executing | waiting | error
  activity: text
  task: none | running | approval | completed | failed | unavailable
  voice: available | unavailable | recording | speaking | interrupted
  input: enabled | submitting | failed
  context_kind: none | task | approval | error | voice | connector
  context_payload: redacted structured data
}
```

Every state transition must be observable without relying on color or animation alone.

## 8. Implementation phases

### Phase 1 — Freeze and measure

Preserve the existing branch and capture the current implementation screenshot, dimensions, Qt availability, font behavior, and test baseline. Do not add more UI controls during this phase.

### Phase 2 — Build pure state and runtime contracts

Create immutable state projections, capability mapping, command submission, connector health, voice availability, task/approval projection, and lifecycle ownership. Add tests before connecting new widgets.

### Phase 3 — Build the orb

Implement the minimized orb as a separate native component with accessible labels, stable geometry, semantic states, click/keyboard expansion, and no idle animation.

### Phase 4 — Build the command rail

Implement the compact expanded rail with robust system fonts, clear hierarchy, single primary input, one state line, and a restrained secondary action row.

### Phase 5 — Build context cards

Implement task, approval, error, voice, and connector cards as replaceable state views. Add only actions backed by actual runtime capabilities.

### Phase 6 — Integrate tray and lifecycle

Validate show/hide/minimize/restore/quit ownership, external versus embedded runtime, shutdown, hotkeys, and headless behavior.

### Phase 7 — Visual and behavioral validation

Run offscreen screenshot checks, Qt tests, headless tests, mocked HTTP/auth tests, voice availability tests, task/approval tests, lifecycle tests, and all protected application regressions.

## 9. Definition of done

The rework is accepted only when:

| Dimension | Acceptance evidence |
|---|---|
| Product clarity | Orb, rail, and context modes have distinct purposes and no redundant permanent controls. |
| Visual quality | Screenshot review shows readable hierarchy, stable spacing, system-font rendering, and restrained decoration. |
| Runtime integrity | Commands, voice, connectors, tasks, approvals, and errors reflect real capability state. |
| Safety | No secret leakage, fake activity, fake microphone state, or unsupported Stop action. |
| Accessibility | Focus, keyboard, labels, state announcements, and reduced motion are covered. |
| Lifecycle | Tray, hide, minimize, restore, close, quit, embedded/external runtime, and headless paths are tested. |
| Regression | Existing protected suites remain green. |
| Documentation | This plan, state contract, limitations, and migration notes are current. |


## Screenshot audit checkpoint

The new Orb, Command Rail, and Context Card surfaces were captured in an offscreen Qt session. The composition is directionally closer to the intended product: the orb is a minimal presence state, the rail has one dominant command input, and the context card is reserved for relevant runtime information.

The offscreen environment reports a missing Qt font directory and renders glyphs as square placeholders. Therefore the screenshots are useful for geometry and hierarchy but not sufficient for final typography acceptance. The implementation must explicitly prefer system fonts and receive a real Windows desktop screenshot before final visual sign-off. The context card also needs a content-rich fixture screenshot with task/approval/error data rather than an empty-state capture.


## Implementation checkpoint

The first-principles rework is implemented through three explicit layers:

| Layer | File | Responsibility |
|---|---|---|
| Runtime | `src/brjarvis/desktop/floating_runtime.py` | Authenticated command/connector calls, capability state, worker execution, and immutable runtime projection |
| Presentation | `src/brjarvis/desktop/floating_surface.py` | Orb, command rail, context card, Qt geometry, styling, focus, tray, and hotkeys |
| Compatibility entry point | `src/brjarvis/desktop/float_widget.py` | Historical exports, headless projection, factory, and direct launcher |

The root `float_widget.py` launcher was also corrected so direct execution invokes the floating-widget entry point instead of the full desktop launcher.

The final validation run completed with:

```text
72 passed, 1 existing Pytest configuration warning
```

The passing set includes the redesigned offscreen Qt surface tests, runtime/auth/connector/voice tests, headless projection tests, protected web and WebSocket tests, CLI tests, and Career OS integration tests. Python compilation and diff checks passed as well.


## Performance and safe-exit update

The floating dock now appears before expensive assistant-runtime construction completes. The standalone launcher creates the visual surface immediately, marks the runtime as `starting`, and bootstraps the orchestrator in a daemon worker. A successful attachment changes the runtime to `embedded_online`; a failure becomes a visible recoverable runtime error rather than blocking the initial window.

Connector polling is now demand-aware: it is stopped while the widget is minimized to the orb, started when the command rail is shown, delayed until the surface is initialized, and guarded against overlapping requests. Runtime state delivery crosses a Qt signal boundary so worker callbacks do not mutate widgets directly.

Safe exit is explicit. The tray Quit action and `Ctrl+D` open a confirmation dialog, stop connector polling, mark the runtime as `stopping`, hide the tray/window, and request `QApplication.quit()`. `Ctrl+D` is ignored when the command field contains draft text, preventing accidental exit while the user is composing a command. `Escape` remains a view-collapse shortcut and does not silently quit the process.

Validation after these changes:

```text
75 passed, 1 existing Pytest configuration warning
```

The passing coverage includes safe-exit confirmation, draft protection, connector timer behavior, asynchronous runtime bootstrap boundaries, Qt surface states, headless behavior, runtime mocks, and protected application regressions.
