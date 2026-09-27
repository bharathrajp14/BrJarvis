# BR JARVIS MK40.2 — VOICE TEST MATRIX & COVERAGE REPORT

**Version**: MK40.2 Production  
**Scope**: Automated Unit, Integration, Latency, and Stress Verification

---

## 1. Test Suite Coverage Summary

| Test Suite | Module Under Test | Key Assertions & Scenarios | Status |
|---|---|---|---|
| `test_voice_pipeline.py` | `voice/prompt_refiner.py`, `voice/assistant.py`, `voice/sound_effects.py` | Filler stripping, prompt refinement, acoustic chimes, recognizer tuning, repetition collapsing, backend binding | **PASS** |
| `test_voice_latency.py` | `voice/silero_vad.py`, `voice/whisper_local.py`, `tools/registry.py` | Silero VAD frame latency (<50ms), zero-disk in-memory Whisper STT, async registry safety | **PASS** |
| `test_ultrafast_wake.py` | `voice/whisper_local.py`, `voice/assistant.py` | Ultrafast wake spotter decoding, empty/silence buffers, wake phrase matching, embedded command extraction | **PASS** |
| `test_stt_variations.py` | `core/intent_engine.py`, `voice/prompt_refiner.py` | Acoustic STT noise normalization, WhatsApp variations, tool pruning under informal speech | **PASS** |
| `test_offline_voice.py` | `voice/assistant.py`, `voice/whisper_local.py` | 100% offline wake phrase detection, trailing command extraction | **PASS** |
| `test_gemini_stt.py` | `voice/gemini_stt.py` | Gemini Flash Listen API key resolution, base64 payload construction, fallback on junk bytes | **PASS** |
| `test_voice_state_machine.py` | `voice/state_machine.py` | 16 formal states, valid transitions, invalid transition rejection, barge-in transitions, error classifications, listener callbacks | **PASS** |
| `test_audio_bus.py` | `voice/audio_bus.py` | Single-stream capture, multi-subscriber broadcast, queue overflow backpressure, frame draining, acoustic echo gate flag, pre-roll rolling buffer | **PASS** |
| `test_voice_diagnostics.py` | `voice/assistant.py` | End-to-end voice self-diagnostics report generation | **PASS** |
| `test_voice_end_to_end.py` | `voice/assistant.py`, `voice/prompt_refiner.py`, `voice/state_machine.py` | Strict wake policy (rejects "travis", "br"), technical vocabulary refinement ("OpenClaw", "FastAPI"), conversational approval/cancellation | **PASS** |

---

## 2. Granular Test Cases

### 2.1 Wake Detection & False Positive Immunity
- `test_strict_wake_word_policy`: Confirms `"jarvis"`, `"hey jarvis"`, `"ok jarvis"` trigger wake detection while `"travis"`, `"br"`, `"assistant"` are rejected.
- `test_embedded_command_extraction`: Confirms single-breath phrases like `"hey jarvis open notepad"` extract `"open notepad"` and trigger instant execution.

### 2.2 Audio Bus & Concurrency
- `test_audio_subscriber_queue_and_drain`: Confirms subscribers receive sequential frames and can drain backlog instantly.
- `test_multiple_subscribers_broadcast`: Confirms single producer broadcasts identical frames to multiple consumers without device contention.
- `test_echo_gate_flag`: Confirms software acoustic echo gating state is toggleable and queryable.

### 2.3 State Machine & Error Handling
- `test_valid_transitions`: Validates state path from `IDLE` through `WAKE`, `CAPTURING`, `TRANSCRIBING`, `EXECUTING`, `SPEAKING`, and back to `IDLE`.
- `test_invalid_transition_rejected`: Confirms illegal state jumps (e.g. `SPEAKING` -> `TRANSCRIBING`) are safely rejected.
- `test_barge_in_interruption_transition`: Validates `SPEAKING` -> `INTERRUPTED` -> `CAPTURING`.

### 2.4 Prompt Refinement & Domain Technical Vocabulary
- `test_prompt_refiner_technical_vocabulary`: Confirms `"open claw"`, `"fast api"`, `"chroma db"` are accurately transformed into `"OpenClaw"`, `"FastAPI"`, `"ChromaDB"`.
- `test_conversational_clarification_and_approval`: Confirms affirmative utterances (`"yes"`, `"confirm"`) execute pending tasks.
