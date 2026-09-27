# BRJARVIS Floating Widget Redesign

**Status:** Implementation specification  
**Date:** 2026-08-19  
**Author:** Manus AI

## Product idea

The floating widget becomes a **compact command dock for the current assistant moment**, not a miniature dashboard. It should answer four questions immediately:

> Is BRJARVIS available, what is it doing, what can I do next, and how do I recover if something failed?

The widget remains persistent and low-distraction. It is a small always-on-top surface for quick command entry, voice activation, current task awareness, and runtime health. Deeper planning, artifacts, memory, and settings open in the full desktop or web workspace rather than being forced into the float.

## Core interaction model

The widget has three presentation modes:

| Mode | Purpose | Contents |
|---|---|---|
| **Dock** | Default compact interaction | Runtime status, assistant state, one-line current activity, command input, mic action, expand action |
| **Task** | Active work visibility | Goal, current step, progress, approval state, stop/retry/open-workspace actions |
| **Tray bubble** | Minimal presence | Status ring, short state label, restore action; no hidden task execution |

The default dock should be approximately 360–420 px wide and 220–300 px high depending on platform scaling. It should avoid a permanent 500 px vertical panel unless the user opens task details. The widget should maintain a stable visual hierarchy:

```text
[status] BR JARVIS                         [−] [×]
Runtime online · Listening                  [expand]

Current activity
Ready for a command / Planning / Awaiting approval

[ Ask JARVIS…                         ] [MIC]

[Task] [Voice] [Connectors] [Open workspace]
```

## Visual direction

The design is **quiet cybernetic utility** rather than decorative cyberpunk. Use a deep neutral surface, one primary cyan action accent, semantic amber/green/red states, restrained glass treatment, and clear typography. The status ring and waveform are secondary indicators. Text labels are authoritative.

| Element | Direction |
|---|---|
| Surface | Dark translucent panel with a subtle border and one restrained elevation shadow |
| Header | Compact brand/status row, no oversized logo or constant glow |
| State | Label + icon/ring; never color alone |
| Activity | One concise current activity line plus optional expandable detail |
| Input | Dominant command field with clear submit and mic actions |
| Footer | Small capability/status actions; no decorative metrics that do not drive decisions |
| Motion | Only state-driven; reduced-motion mode removes pulse/wave transitions |
| Typography | Proportional readable UI font; monospace only for technical status values |

## State model

The presentation consumes `FloatingWidgetState` and must render every state explicitly.

| State family | Values | Required behavior |
|---|---|---|
| Visibility | `visible`, `hidden`, `minimized` | Distinguish hide, minimize, and quit. Restore must be discoverable through tray/hotkey. |
| Runtime | `starting`, `embedded_online`, `external_online`, `reconnecting`, `offline`, `error`, `stopping` | Show connection ownership and recovery action. |
| Assistant | `idle`, `listening`, `processing`, `speaking`, `executing`, `waiting`, `error` | Show a concise state label and current activity. |
| Input | `idle`, `submitting`, `disabled`, `error` | Disable duplicate submission; preserve user text on failure where possible. |
| Task | `none`, `running`, `waiting_for_approval`, `completed`, `failed`, `unavailable` | Open the task view for details; never imply cancellation if no endpoint exists. |
| Connectors | `loading`, `ready`, `stale`, `unavailable` | Show stale/unavailable meaningfully; do not silently omit connector status. |
| Audio | `inactive`, `recording`, `playing`, `interrupted`, `muted`, `unavailable` | Voice button label and visualization must follow real audio state. |

## User flows

### Quick command

The user opens or focuses the dock, types a command, submits once, sees `Processing`, receives a concise result, and can open the full transcript/task workspace. Failures retain the prompt and provide retry or open-diagnostics actions.

### Voice

The user presses the mic action, sees `Listening`, speaks, sees `Processing`, and receives `Speaking` or `Error`. The widget must show when speech is interrupted or unavailable. A mic click must not claim listening if no voice runtime is connected.

### Active task

When a real task event arrives, the dock changes its activity summary to the task goal and exposes a Task action. The expanded task view shows current step, progress if actually reported, approval state, result, and failure recovery. Stop is shown only when a real task-control capability exists.

### Runtime failure

A connection failure changes the runtime badge to `Reconnecting` or `Offline`, preserves the input draft, stops fake activity animation, and offers retry/open workspace. A connector failure does not mark the whole assistant offline.

### Tray

Minimize keeps the runtime alive and reduces the surface to a status bubble. Hide removes the surface but keeps it available through the tray. Quit explicitly requests process shutdown and must not be conflated with close/hide.

## Accessibility and safety contract

Every action has an accessible name, visible focus, keyboard activation, and tooltip/label where icon-only. State updates are announced through a live status region or headless equivalent. Reduced-motion preferences disable continuous pulse/wave animation. API keys and raw exception traces never appear in the widget log, tray notification, or state labels.

The widget must not expose private reasoning traces. It may show execution summaries, current step, tool name, approval request, result, verification, error, and diagnostics reference.

## Test contract

The redesign is accepted only when the following matrix is covered.

| Layer | Required tests |
|---|---|
| State model | Valid transitions, unknown state fallback, immutable snapshot, subscriber lifecycle |
| Command adapter | Orchestrator success, HTTP success, timeout, auth failure, malformed response, retryable error |
| Connector adapter | Loading, ready, stale, unauthorized, timeout, malformed payload, no secret leakage |
| Qt presentation | Construction, state rendering, input enable/disable, task expansion, reduced motion, focus/keyboard |
| Headless presentation | Same public state/command contract and explicit graphical capability unavailability |
| Tray/lifecycle | Show, hide, minimize, restore, quit, shutdown ownership, hotkey behavior |
| Thread safety | Worker callbacks reach UI only through queued signals; no background widget mutation |
| Regression | Existing desktop/web/voice launchers and protected backend suites continue to pass |
| Environment | PySide6 available path, no-Qt headless path, missing backend, external backend, port conflict |

## Implementation boundary

The Qt class should become a presentation controller. It may own widgets, painting, shortcuts, tray actions, and local view state. It should not own API-key discovery, direct `requests` calls, server-port logic, orchestrator branching, connector polling, or lifecycle shutdown policy. Those responsibilities belong to `FloatingRuntimeAdapter` and the shared desktop runtime bridge.


## Implementation status

The redesigned dock is implemented in `src/brjarvis/desktop/float_widget.py` and backed by `src/brjarvis/desktop/floating_runtime.py`.

The implementation now uses a compact command-dock composition with runtime ownership text, assistant state, current activity, task progress visibility, command input, truthful mic availability, connector status, task action, workspace action, minimize/hide controls, system tray, Alt+Space visibility toggle, Escape minimize/restore, reduced-motion controls, and a shared headless projection.

The Qt surface no longer owns direct HTTP calls, API-key lookup, connector worker threads, or orchestrator branching. Those responsibilities belong to `FloatingRuntimeAdapter`. State delivery crosses into Qt through signals so background workers do not mutate widgets directly.

The redesigned verification run covered:

```text
68 passed, 1 existing Pytest configuration warning
```

The 68 tests include offscreen Qt construction and state rendering, command success/failure, mocked HTTP/authentication, connector health, voice callback availability, headless parity, web routes, WebSocket behavior, CLI behavior, and Career OS integration.

The remaining known boundary is that the default standalone floating command does not claim voice availability unless a real `voice_trigger` callback is injected. This is intentional: the widget must not present a working microphone state when the voice runtime is not attached.
