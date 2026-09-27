# BR JARVIS MK40.2 — VOICE ASSISTANT FULL AUDIT REPORT

**Author**: Senior Voice-Systems Engineering  
**Version**: MK40.2 Production  
**Scope**: Voice Coordinator, Audio Capture, VAD, STT Fallback Chain, State Machine, Shared ReAct Orchestrator, TTS & Barge-In Echo Gating

---

## 1. Executive Summary

This forensic audit report catalogs the structural defects, concurrency flaws, and execution anomalies identified in the previous voice subsystem iterations and details the root causes, affected code components, and verified repairs.

---

## 2. Flaw Catalog

### FLAW-001: Device Contention & Concurrent Physical Stream Collisions
- **Problem**: Multiple uncoordinated components (`BRVoiceAssistant` main microphone stream, `_persistent_barge_in` stream, and `GeminiLiveVoiceLoop`) independently opened physical `sd.RawInputStream` instances on the soundcard simultaneously.
- **Root Cause**: Absence of a centralized audio broadcast bus. Each module attempted direct hardware acquisition. On Windows (WASAPI/MME), concurrent non-shared device access caused buffer overruns, stream lockups, and random crashes.
- **Affected File**: `voice/assistant.py`, `voice/gemini_live.py`, `voice/stt.py`
- **Affected Function**: `__init__()`, `_start_persistent_barge_in()`, `_run_duplex_loop()`
- **Runtime Symptom**: Sounddevice stream initialization errors, audio glitching, dropped audio frames during wake detection.
- **Severity**: P0 (Critical)
- **Fix**: Implemented `AudioBus` singleton with single hardware stream and pub/sub frame distribution to subscribers (`barge_in_monitor`, `assistant_main_mic`, `gemini_live_mic`).
- **Test**: `tests/unit/test_audio_bus.py`

---

### FLAW-002: Broad Wake-Word False Positive Activations
- **Problem**: Ambient speech mentioning words such as "Travis", "BR", "assistant", or television audio caused false wake-word activations.
- **Root Cause**: `_WAKE_RE` regex contained loose phonetic tokens (`travis`, `br`, `harvis`, `charvis`, `garvis`) and `_FUZZY_WAKE_MATCHES` accepted `"hey assistant"` and `"wake up"` indiscriminately.
- **Affected File**: `voice/assistant.py`
- **Affected Function**: `_is_wake_phrase()`, `_WAKE_RE`
- **Runtime Symptom**: Frequent unintentional wake triggers in noisy or conversational rooms.
- **Severity**: P1 (High)
- **Fix**: Implemented strict wake policy prioritizing primary wake word `"jarvis"` and explicit aliases (`"hey jarvis"`, `"ok jarvis"`, `"hi jarvis"`, `"hello jarvis"`). Removed broad phonetic tokens (`travis`, `br`, `assistant`) from default patterns. Added 1.0s wake cooldown window.
- **Test**: `tests/unit/test_voice_end_to_end.py::test_strict_wake_word_policy`

---

### FLAW-003: Loosely-Coupled State Management & Race Conditions
- **Problem**: Voice execution state was managed via scattered booleans (`self.ui.speaking = True`, `self.ui._state = "LISTENING"`), allowing impossible transitions (e.g. speaking directly into transcribing).
- **Root Cause**: Lack of an explicit, validated finite state machine.
- **Affected File**: `voice/assistant.py`, `voice/state_machine.py`
- **Affected Function**: `BRVoiceAssistant.__init__()`, `speak()`, `process_command()`, `run()`
- **Runtime Symptom**: UI displaying "LISTENING" while processing or "SPEAKING" after TTS completed.
- **Severity**: P1 (High)
- **Fix**: Created `VoiceStateMachine` with 16 validated states, transition guards, error classifications, and two-way UI synchronization.
- **Test**: `tests/unit/test_voice_state_machine.py`

---

### FLAW-004: Self-Interruption Due to Lack of Acoustic Echo Gating
- **Problem**: When JARVIS spoke via speaker/headphones, its own TTS output picked up by the microphone caused the barge-in VAD to falsely detect human speech, cutting off TTS prematurely.
- **Root Cause**: Barge-in VAD had no awareness of whether TTS audio was actively rendering to speakers.
- **Affected File**: `voice/tts.py`, `voice/silero_vad.py`, `voice/audio_bus.py`
- **Affected Function**: `_speak_streaming_worker()`, `NeuralTTS.stop()`, `is_speech()`
- **Runtime Symptom**: JARVIS cutting itself off midway through spoken sentences.
- **Severity**: P1 (High)
- **Fix**: Implemented software Acoustic Echo Gating. `NeuralTTS` notifies `AudioBus` when playback starts/stops. During active playback, `SileroVAD` raises speech probability threshold (0.72) and requires elevated SNR (>8.5 dB).
- **Test**: `tests/unit/test_audio_bus.py::test_echo_gate_flag`, `tests/unit/test_voice_pipeline.py::test_stop_speech_barge_in`

---

### FLAW-005: Leaked & Duplicate Background Task Monitors in `process_command()`
- **Problem**: When parallel multi-goal tasks were submitted, `monitor_tasks()` was instantiated in background without canceling existing monitors, resulting in duplicate monitors, race conditions on task completion, and repeated speech announcements.
- **Root Cause**: `_bg_tasks` was not pruned before starting new monitors, and multiple `create_task` invocations were tracked loosely.
- **Affected File**: `voice/assistant.py`
- **Affected Function**: `process_command()`
- **Runtime Symptom**: Spoken notifications repeating "All parallel tasks completed" multiple times.
- **Severity**: P0 (Critical)
- **Fix**: Single tracked background task lifecycle with active pruning and safe done-callback disposal.
- **Test**: `tests/unit/test_voice_pipeline.py`

---

### FLAW-006: Missing Cold-Start Warmup in Silero VAD Inference
- **Problem**: First-frame VAD inference after initialization took >50ms due to uninitialized ONNX session graph memory, tripping strict latency thresholds.
- **Root Cause**: Missing initial warmup forward pass during `_init_model()`.
- **Affected File**: `voice/silero_vad.py`
- **Affected Function**: `_init_model()`
- **Runtime Symptom**: Cold-start audio frame drop or latency spike on first speech detection.
- **Severity**: P2 (Medium)
- **Fix**: Added dummy zero-vector forward pass during ONNX/Torch session initialization.
- **Test**: `tests/unit/test_voice_latency.py::test_silero_vad_latency`

---

### FLAW-007: Lack of Technical Vocabulary Domain Protection in Prompt Refinement
- **Problem**: Technical terms like "OpenClaw", "FastAPI", "ChromaDB", "Playwright", "WebSocket" were occasionally mangled or split into lowercase plain words by speech recognition without proper normalization.
- **Root Cause**: Hardcoded partial vocabulary without domain technical term dictionary.
- **Affected File**: `voice/prompt_refiner.py`
- **Affected Function**: `_load_vocab()`, `refine()`
- **Runtime Symptom**: Tool queries failing because "open claw" wasn't recognized as the project name "OpenClaw".
- **Severity**: P1 (High)
- **Fix**: Added comprehensive `DEFAULT_TECH_VOCAB` with full casing normalization and structured confidence classification.
- **Test**: `tests/unit/test_voice_end_to_end.py::test_prompt_refiner_technical_vocabulary`
