# 10 — VOICE & AUDIO MULTIMODAL FORENSIC RECORD

## 1. Overview & Voice Pipeline Architecture
The `voice/` subsystem provides zero-latency voice interaction, real-time voice activity detection (VAD), local and cloud speech-to-text, adaptive ambient noise calibration, and speech synthesis with immediate barge-in cancellation.

---

## 2. File-by-File Forensic Analysis

### `voice/assistant.py` (872 lines)
- **Role**: Full-duplex voice assistant daemon (`BRVoiceAssistant`).
- **Loop Architecture**:
  - Dedicated capture thread reading 16kHz 16-bit PCM audio from `SounddeviceMicrophone`.
  - Silero VAD evaluation every 30ms.
  - Speech frame buffering in `voice/ring_buffer.py`.
  - When endpoint silence is detected (default: 450ms), audio chunk is sent to STT.
  - Dispatches transcribed text to `orchestrator/core.py`.
  - Plays generated response via `voice/tts.py` while continuously monitoring for user speech (Barge-In).
- **Barge-In Cancellation**: If VAD probability > 0.85 while TTS is actively playing, immediately invokes `tts.stop()` and flushes `voice/tts_queue.py`.
- **Disposition**: **KEEP + IMPROVE**.

### `voice/silero_vad.py` (361 lines)
- **Role**: Local neural Voice Activity Detection using ONNX Runtime Silero VAD v5.
- **Latency**: < 1.5ms per 30ms audio frame on CPU.
- **Disposition**: **KEEP**.

### `voice/whisper_local.py` (500 lines)
- **Role**: Local Speech-To-Text engine.
- **Backends**: `faster-whisper` (CTranslate2 INT8 quantized Whisper model) with fallback to `whisper.cpp` / OpenAI Whisper.
- **Model Tiers**: `tiny.en`, `base.en`, `small.en` (automatic CUDA / CPU selection).
- **Disposition**: **KEEP**.

### `voice/gemini_live.py` (197 lines)
- **Role**: WebSocket client for Gemini 2.0 Live Bidirectional Audio streaming over WebSockets.
- **Latency**: ~300ms end-to-end cloud voice loop.
- **Disposition**: **KEEP**.

### `voice/tts.py` (637 lines) & `voice/tts_queue.py` (105 lines)
- **Role**: Text-To-Speech synthesis engine.
- **Synthesizers**:
  1. Microsoft Edge TTS (`edge-tts` - high quality neural voices, e.g. `en-GB-SoniaNeural`, `en-US-ChristopherNeural`).
  2. Local Piper TTS (`piper-tts` - ultra-fast offline neural TTS).
  3. Windows SAPI5 (`pyttsx3` - instant zero-dependency offline fallback).
- **Queue Priority**: `ALERT > SPEECH > BACKGROUND`.
- **Disposition**: **KEEP + IMPROVE**.

### `voice/noise_calibrator.py` (314 lines)
- **Role**: Dynamic ambient noise estimator. Adapts VAD thresholds dynamically when background noise (fans, air conditioning, typing) changes.
- **Disposition**: **KEEP**.
