# BR JARVIS Floating Widget — Logical Flaw Audit and Rework

## Audit findings

| Flaw | Impact | Fix |
|---|---|---|
| A stopped microphone worker could emit a late timeout/error callback | STOP could appear to work and then be overwritten by an error state | Added generation tokens; stale workers cannot publish state. |
| Sending a command while listening did not stop capture | Voice and text command workers could overlap and race | `submit_command` now stops active capture and speaker playback before starting. |
| MIC had no distinct stop state in minimized mode | User could not tell how to interrupt listening | Orb becomes a circular listening stop control; expanded MIC becomes STOP. |
| Mic timeout/error wording exposed implementation detail | Confusing and stressful study experience | Timeout becomes “Listening timed out. Click MIC to try again.”; microphone errors are actionable. |
| Minimized orb behaved only as an expand button | It could not control active listening | Listening orb click stops capture; idle orb click expands. |
| Task button showed only the current task | Previous tasks could not be reopened or continued | Added recent-task history, safe goal loading, editable continuation, and explicit Send confirmation. |
| Task continuation could have silently duplicated work | Re-running an old goal without review is unsafe | Previous task is loaded into the command field; user must review and press Send. |
| Raw connection-pool failures were rendered in the activity line | User saw HTTP implementation details | Normalized backend errors to a plain recovery message. |
| Expanded surface was opaque and visually heavy | Covered study material and created unnecessary stimulation | Added translucent panel background, lower shadow, bounded rectangle, and calm state semantics. |
| Qt offscreen font deployment is incomplete | Sandbox screenshots show square glyph placeholders | Prefer installed system fonts and require a real Windows font check before visual sign-off. |

## Unified state rules

The widget now follows these rules:

```text
IDLE + click MIC       -> LISTENING
LISTENING + click MIC -> STOPPED/READY
LISTENING + click orb -> STOPPED/READY
LISTENING + Send      -> stop capture -> PROCESSING
LISTENING timeout     -> ERROR with retry instruction
TRANSCRIBING          -> MIC disabled until transcript/error
Previous task select  -> editable command field, no auto-submit
Speaking + click      -> stop speaker
Idle orb click        -> expand rectangle
```

## Validation result

The final focused and protected suite passed with **95 tests**. It covers stale worker suppression, microphone stop, timeout messages, command interruption, previous-task loading, circular listening orb state, translucent rail state, Qt UI, runtime, workspace, WebSocket, CLI, and Career OS regressions.
