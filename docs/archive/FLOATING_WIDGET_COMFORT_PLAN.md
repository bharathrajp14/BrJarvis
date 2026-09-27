# BR JARVIS Floating Widget — Comfort-First Rework Plan

## User perspective

If I were using BR JARVIS while studying, I would want the widget to stay present without covering my notes, let me speak without guessing whether it is still listening, show readable text without visual noise, and explain connection problems in plain language. I would not want raw Python/HTTP exceptions, oversized controls, a panel that occupies half the screen, or a microphone that appears stuck.

The comfort target is therefore **quiet presence, readable action, bounded space, and reversible interaction**.

## Experience goals

| User need | Design response |
|---|---|
| Keep study material visible | Use a bounded rectangle no wider than 42% of the available screen and no taller than 30%; on ordinary screens target approximately 500 × 220 px. |
| Read quickly | Use one typography scale: 13 px body, 12 px state, 11 px metadata, with generous line spacing and no raw stack traces. |
| Know what is happening | Show one clear state: Ready, Listening, Transcribing, Processing, Speaking, or Needs attention. |
| Stop listening safely | Change MIC to STOP during capture. A second click stops capture; a hard timeout ends listening and explains how to retry. |
| Recover from backend problems | Convert connection-pool/connection-refused errors into “BR JARVIS backend is not reachable. Start the backend or retry.” Keep technical detail in logs only. |
| Avoid accidental actions | Voice transcription fills the input but never auto-submits. Speaker playback is explicit and reversible. Workspace handoff reports success/failure instead of silently opening a broken page. |
| Reduce visual stimulation | No idle waveform, no continuous fake-thinking animation, restrained cyan/amber/red semantics, and stable layout while state changes. |

## Layout plan

The expanded surface is a compact horizontal rectangle with three layers:

```text
┌────────────────────────────────────────────────────────────┐
│  ● BR JARVIS       Listening                  Online · local │
│                                                            │
│  Listening…  or  latest response summary                   │
│                                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Ask JARVIS…                         MIC  SPEAK   SEND  │ │
│  └────────────────────────────────────────────────────────┘ │
│  Task       Open workspace                         Esc     │
└────────────────────────────────────────────────────────────┘
```

The panel has a minimum size of 420 × 200 px, a preferred size of approximately 500 × 220 px, and a hard maximum of 560 × 250 px. At runtime it also clamps itself to the current screen’s available geometry and never exceeds 42% of screen width or 30% of screen height.

## Listening lifecycle

1. The user clicks **MIC**.
2. The control becomes **STOP**, the state becomes **Listening**, and the activity line says “Listening… speak naturally.”
3. The user can click **STOP** at any point. The capture source is closed, transcription is cancelled, and the state returns to Ready.
4. If no speech arrives before the capture timeout, the widget says “Listening timed out. Click MIC to try again.”
5. During transcription the control becomes disabled and the state says **Transcribing**.
6. The transcript is inserted into the command field for review. It is never submitted automatically.

## Error policy

User-visible errors are short, actionable, and safe. Raw exception text never appears in the activity line.

| Technical condition | User-facing message |
|---|---|
| Connection pool retries / refused backend | “BR JARVIS backend is not reachable. Start the backend or retry.” |
| Workspace handoff expired | “Workspace handoff expired. Click Open workspace to try again.” |
| No microphone | “No microphone is available. Check the Windows input device and retry.” |
| Listening timeout | “Listening timed out. Click MIC to try again.” |
| TTS failure | “Speaker is unavailable. Check the audio output device and retry.” |

## Verification plan

The implementation is accepted only after checking geometry at multiple screen sizes, font readability, state transition screenshots, stop-before-timeout, timeout, connection errors, workspace handoff failure, and the protected web/voice/CLI regression suites. The screenshot review must confirm that the rectangle stays comfortably bounded and that no raw `HTTPConnectionPool`, URL, or stack trace is visible to the user.


## Implementation checkpoint

The comfort rework now uses a preferred 500 × 220 px rectangle, a responsive minimum of 320 × 200 px, a hard maximum of 560 × 250 px, and a screen-aware bound of no more than 42% width and 30% height. The voice and speaker actions have stable widths so the command field remains the dominant control.

The MIC control now changes to **STOP** while recording and **…** while transcribing. A second click stops capture, the microphone source is closed when possible, and the phrase limit is 12 seconds. Timeout and microphone errors are translated into short recovery instructions.

Backend connection-pool failures are no longer shown as raw `HTTPConnectionPool` text. They become “BR JARVIS backend is not reachable. Start the backend or retry.”

The focused comfort suite passes with 34 tests. The earlier full protected suite passed with 91 tests before the final responsive-width-only correction; the focused suite includes the changed UI/runtime paths and workspace handoff tests.
