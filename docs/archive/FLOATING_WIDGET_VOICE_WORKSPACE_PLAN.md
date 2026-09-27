# Floating Widget Voice, Speaker, Workspace, and UI Rework Plan

## Objective

Turn the floating widget into a reliable assistant surface with four connected capabilities: **voice-to-text**, **short on-demand speaker playback**, **workspace handoff with a real browser session**, and a clearer visual interaction model.

## Current blockers

| Area | Current behavior | Required correction |
|---|---|---|
| Voice | The mic button only invokes an injected callback; standalone launch has no callback, so voice is unavailable. | Reuse `SounddeviceMicrophone` and the project Whisper/STT path in a background worker. Put the transcript into the command field for review before submission. |
| Speaker | There is no speaker action in the floating rail. | Add a speaker action that reads the latest assistant response only, with a short cleaned summary and interrupt/replay state. |
| Workspace | The widget opens `/web/` directly. The browser has no authenticated `jarvis_session` cookie, so API/WebSocket calls can fail. | Add a localhost session bootstrap endpoint that exchanges the desktop-held server key for an HTTP-only browser session, then open `/web/?handoff=...`. The browser consumes the one-time handoff and verifies auth before connecting. |
| Backend | Native widget requests use API-key headers while the browser workspace uses session/cookie auth and WS tickets. | Keep the native key private. Add a narrow handoff contract that returns no secret to the browser. |
| UI | The rail treats mic, task, workspace, and command actions as similar-weight controls. | Make command input primary; put voice and speaker beside it; make context/status cards replace the activity area only when needed. |

## Interaction model

### Command rail

The main rail has one command field with three direct actions:

| Control | Action |
|---|---|
| Mic | Capture one short phrase, transcribe it locally or through the existing STT fallback, and place the transcript in the command field. It does not auto-submit. |
| Send | Submit the command through the existing orchestrator/HTTP adapter. |
| Speaker | Speak a cleaned, short version of the latest response. While speaking, the same control becomes Stop. |

The transcript is shown as editable text so the user can correct recognition errors before sending. Recording has a hard maximum duration and always ends on silence, timeout, or a second mic click.

### Speaker behavior

The speaker action is intentionally short and deliberate. It uses `summarize_for_speech` and the existing `NeuralTTS` engine. It speaks the latest response, not the raw task log or code. Repeated clicks stop current playback; a new click replays the latest cleaned summary.

### Workspace behavior

Clicking **Open workspace** first requests a browser handoff from the local server. The server validates the native API key, creates the normal HTTP-only session cookie, and returns a short-lived one-time handoff token. The widget opens the browser to `/web/?handoff=<token>`. The web client redeems the token through a same-origin endpoint, then uses its existing cookie-based auth and WebSocket ticket flow.

The handoff token is short-lived, single-use, bound to the local server process/session, and never contains the API key. If handoff fails, the widget shows a useful recovery message instead of opening a broken page.

## Runtime contracts

### Floating runtime state additions

```text
transcript: string
latest_response: string
speaker: inactive | synthesizing | speaking | unavailable
voice: unavailable | recording | transcribing | ready | error
workspace: idle | authenticating | ready | failed
capabilities.voice_to_text: boolean
capabilities.speaker: boolean
capabilities.workspace_handoff: boolean
```

### Native runtime methods

```text
start_voice_capture()
stop_voice_capture()
speak_latest_response()
stop_speaker()
request_workspace_handoff()
```

All three operations run outside the Qt UI thread and report normalized state back through the existing Qt signal boundary.

### Backend handoff endpoints

```text
POST /api/auth/desktop-handoff
POST /api/auth/desktop-handoff/redeem
```

The first accepts native API-key authentication and creates a short-lived handoff record. The second consumes the record and sets `jarvis_session` on the browser response. The redeem route must be same-origin and must not return the server API key.

## Visual rework

The redesign keeps the Orb/Rail/Context architecture but changes the rail hierarchy:

```text
┌─────────────────────────────────────────────────────────┐
│ ● BR JARVIS                         Online · embedded  − │
│   Ready                                                  │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ transcript / Ask JARVIS…                  MIC  →  🔊│ │
│ └─────────────────────────────────────────────────────┘ │
│ Latest response summary                         Task   │
│ Open workspace                                Context  │
└─────────────────────────────────────────────────────────┘
```

The speaker control uses an explicit textual label and tooltip rather than an icon-only glyph. Voice states use “Listening”, “Transcribing”, and “Voice unavailable”. Speaker states use “Speak”, “Speaking”, and “Stop”.

## Implementation sequence

1. Extend the runtime state and add a dedicated voice controller that uses `SounddeviceMicrophone` plus `whisper_local.transcribe`, with Google/STT fallback only through existing project code.
2. Add the short-response speaker controller around `NeuralTTS`, including cancellation and last-response storage.
3. Add server desktop-handoff endpoints and browser redemption logic, then update the widget workspace action to use it.
4. Rework the command rail layout and state rendering for transcript, speaker, voice, workspace, and response states.
5. Add unit tests with fake microphone, fake STT, fake TTS, fake HTTP session, and fake browser opener. Add FastAPI handoff tests and browser JavaScript syntax checks.
6. Run offscreen Qt tests, backend tests, protected web/WebSocket tests, and a manual Windows verification checklist for microphone and speaker hardware.

## Acceptance criteria

| Requirement | Evidence |
|---|---|
| Voice-to-text | A fake microphone/STT test produces editable transcript text; real Windows path uses the project recorder and Whisper/STT stack. |
| Speaker | A fake TTS test receives only the cleaned short response; repeated click stops playback. |
| Workspace | Handoff endpoint creates a browser session without exposing the API key; redeem is single-use; browser auth status is authenticated. |
| UI | Rail visually distinguishes command, mic, send, and speaker; all states have readable labels and tooltips. |
| Safety | No auto-submit after transcription, no API key in URL, no secret in logs, no silent failure. |
| Performance | Runtime construction remains asynchronous; voice/STT/TTS workers never block Qt. |
| Regression | Existing web, WebSocket, CLI, Career OS, and floating-widget tests remain green. |
