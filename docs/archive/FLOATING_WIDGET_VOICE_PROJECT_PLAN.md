# BR JARVIS Voice-to-Project Workflow

## User flow

1. The user clicks **MIC**. The widget enters **Listening** and keeps collecting audio.
2. The user clicks **STOP**. The capture source closes, the accumulated PCM is converted to WAV, and transcription begins.
3. The transcript is sent to the configured refinement model. The model is instructed to return only one concise project instruction and not execute it.
4. The refined instruction is shown in the command field/state and then submitted to the project orchestrator.
5. The project response becomes the latest answer and is available to the speaker control.
6. The completed-task panel loads recent tasks with goals, statuses, and available final answers/results. Selecting one loads its original goal into the editable command field; the user must press Send to continue.
7. Open workspace probes the backend. If unavailable, it starts `python start.py web --port <port> --no-open`, waits for health, creates a one-time authenticated handoff, and opens the workspace URL.

## Safety rules

The voice flow has a safety recording cap as a fail-safe, but it does not finish normally on silence. Only STOP ends a normal recording. Cancellation for a new command or shutdown discards the capture and suppresses late callbacks. Refinement never executes a command; project submission happens only after refinement completes.

The workspace starter inherits the current environment, uses the configured project root and server port, suppresses duplicate server processes, waits for readiness, and reports a recoverable error if the backend does not start.

## Extension ideas implemented or reserved

The completed-task area now shows prior answers/results rather than only task names. The same state model can support pinning a task, copying a refined instruction, replaying the latest answer through TTS, opening a task directly in the web workspace, and attaching the original audio transcript for audit without changing the core state machine.

## Validation

The integrated suite passed with **101 tests**, including manual-stop PCM capture, transcript conversion, model refinement injection, project submission, backend startup probing, workspace handoff, task history/results, Qt controls, WebSocket, CLI, and Career OS regressions.
