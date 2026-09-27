# BR JARVIS Floating Widget — Reliable Rework Contract

## Product principle

The widget is a **single-command control**, not a dashboard. Every visible control must have one clear runtime owner, one terminal outcome, and one cancellation path. The UI must never imply success while a worker is still pending.

## Explicit interaction state

| State | Primary label | Enabled actions | Terminal outcomes |
|---|---|---|---|
| Ready | Ask JARVIS | Send, Mic, Speak, Tasks, Workspace | Processing, Listening, Speaking, Task history, Workspace ready/error |
| Listening | Stop listening | Stop only, plus safe window hide | Transcribing, Cancelled, Timed out, Microphone error |
| Transcribing | Transcribing | No voice action | Transcript ready, Error |
| Processing | Working | Stop/cancel only when backend supports it; otherwise no false cancel | Completed, Failed |
| Speaking | Speaking | Stop speaker | Ready, Speaker error |
| Task history | Previous tasks | Select a task, Close | Editable goal loaded or load error |
| Workspace connecting | Connecting | Close, Retry after failure | Ready or actionable error |
| Error | Needs attention | Retry, Open workspace, Close | Ready or same error |

## Invariants

1. Only the current operation may publish state. Cancelled and superseded workers are ignored.
2. A command submission always stops listening and speaker playback before starting.
3. Voice transcription fills the command field but never submits by itself.
4. A previous task is loaded as editable text; it is never silently resumed or duplicated.
5. Minimized mode is a circular status/stop control. It expands only when idle.
6. Raw exceptions, URLs, API keys, and stack traces never appear in user-visible text.
7. A control is disabled while its underlying capability is unavailable or in a non-interruptible phase.
8. Closing the surface while an operation is active cancels local capture/playback and leaves backend-owned work unchanged.

## Visual rules

The expanded surface uses one translucent rectangle with a preferred size of 500 × 220 px and a responsive bound of 42% of screen width and 30% of screen height. The layout has one status header, one activity sentence, one command row, and one secondary action row. Minimized mode is a 74 px circular orb with only state color and an accessible action label.

## Acceptance tests

The rework is not complete until deterministic tests verify every state transition, including stop-before-timeout, timeout-after-no-speech, send-while-listening, stale worker suppression, speaker stop, task-history loading, failed handoff, retry, minimize/listening orb behavior, and safe exit.


## Implementation outcome

The runtime now guards command operations with a generation counter, ignores stale microphone callbacks, stops voice and speaker playback before a new command, normalizes injected voice-controller capabilities, and converts recent tasks into an explicit editable continuation flow. The Qt surface removes the dead approval button, prevents context-action accumulation, and keeps the minimized orb as an audio-aware control.

The reworked validation suite passed with **98 tests**. This includes the newly added stale-command, send-while-listening, injected voice-controller, previous-task, task-history, context-refresh, circular-orb, voice, runtime, workspace, WebSocket, CLI, and Career OS checks. Python compilation, JavaScript syntax validation, and diff checks also passed.
