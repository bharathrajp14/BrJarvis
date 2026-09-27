# BR JARVIS MK40.2 — VOICE FAILURE & RECOVERY MATRIX

**Version**: MK40.2 Production  
**Scope**: Fault Tolerance, Exception Handling, Watchdogs, and Self-Healing Policies

---

| Subsystem | Failure Mode | Trigger / Root Cause | Detection Mechanism | Immediate Action | Automatic Recovery Strategy | Fallback / User Notification |
|---|---|---|---|---|---|---|
| **Audio Hardware** | Microphone Disconnected / Detached | USB physical unplug or driver stall | `AudioBus.is_alive()` timeout watchdog (5.0s) | Transition to `RECOVERING`, stop stalled stream | Device re-enumeration; probe physical hardware mics; reopen stream | If re-probe succeeds: recalibrate noise floor & resume `WAKE_DETECTION`. If fails: `state=ERROR`, notify "Using keyboard text control". |
| **Audio Hardware** | Stream Buffer Overflow / Underflow | CPU scheduler spike or high latency thread | `AudioSubscriber.put()` queue full | Drop oldest frame; increment drop counter | Backpressure protection; drain stale subscriber queue on wake | Log dropped frame metric; zero memory leak. |
| **Wake Detection** | False Negative / Missed Wake Word | Low SNR, quiet speech, distant mic | Silence timeout in `sr.Recognizer.listen()` | Transition back to `WAKE_DETECTION` | Dynamic pause threshold adjustment (0.55s - 0.90s based on environment) | Continuous passive monitoring without crashing. |
| **Wake Detection** | False Positive Activation | Ambient background TV or conversation | `_is_wake_phrase()` evaluated on ambient audio | Cooldown check | Strict regex filter rejecting broad tokens (`travis`, `br`); 1.0s cooldown | Rejects artifact; silently returns to `WAKE_DETECTION`. |
| **Speech-to-Text** | Gemini Online STT Network Timeout | DNS outage, proxy 503, or rate limit | `httpx.TimeoutException` or HTTP status != 200 | Catch network exception | Immediate fallback to 100% Offline Local Whisper CTranslate2 | Zero user-visible error; offline transcription returns result seamlessly. |
| **Speech-to-Text** | Local Whisper Model Missing | First run without local model cache | `whisper_available() == False` | Import / engine check | Fallback to Google Speech Recognition (`r.recognize_google`) | Continues operation; logs advisory to install faster-whisper. |
| **Speech-to-Text** | Hallucination / Blank Audio | Silence or background white noise | `_is_hallucination()` tag & repetition filter | Strip artifact | Collapse repetition loops; drop meaningless fillers | Logs "Ignored wake/noise artifact"; returns to `LISTENING`. |
| **Orchestrator** | AI Backend Failure / Outage | Model API token expiration or provider 500 | `TASK_EXECUTION_FAILED` in ReAct response | Transition to `ERROR` | Retry configured fallback providers in `FALLBACK_MODELS` | Spoken notification: "Unable to complete planning stage because model backends failed." |
| **Tool Execution** | Tool Execution Error | Missing file, permission denied, invalid arg | Exception raised during `execute_tool()` | Catch in ReAct loop | ReAct self-correction: model receives error message and tries alternative approach | If all retries exhausted: reports honest failure to user without fabricating results. |
| **Text-to-Speech** | Edge-TTS Network Failure | Microsoft Bing speech endpoint unreachable | Socket timeout or `edge_tts` network exception | Catch in `_synth_sentence` | 60s cooldown on Edge-TTS; instant fallback to Windows OneCore HD / SAPI5 Offline | Audio speaks with zero latency via local Windows natural voice. |
| **Text-to-Speech** | SAPI5 COM Initialization Error | Non-Windows OS or COM threading issue | `ImportError` or `win32com` exception | Exception handler in `_init_sapi5` | Fallback to Linux/Darwin system players (`afplay`, `ffplay`, `mpv`, `aplay`) | Text displayed in UI log even if all speech output channels fail. |
| **Barge-In** | Acoustic Echo Self-Interruption | Microphone hearing assistant's own TTS output | `AudioBus.is_echo_gate_active == True` | Echo gate asserted | `SileroVAD` elevates speech threshold (0.72) and requires SNR >8.5 dB | Eliminates false interruptions while preserving ability for user to shout "Stop". |
