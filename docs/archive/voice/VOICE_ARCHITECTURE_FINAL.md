# BR JARVIS MK40.2 — UNIFIED VOICE ARCHITECTURE BLUEPRINT

**Architecture Designation**: MK40.2 Unified Single-Stream ReAct Voice Pipeline  
**Core Directive**: Voice is an interface, not a second brain.

---

## 1. High-Level Architectural Flow

```text
                  PHYSICAL MICROPHONE
                           │
                           ▼
                 CENTRAL AUDIO BUS
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     WAKE SPOTTER     COMMAND STT     BARGE-IN VAD
     (CTranslate2)   (Gemini/Whisper)  (Silero ONNX)
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                 VOICE STATE MACHINE
               (16 Validated Transitions)
                           │
                           ▼
                  PROMPT REFINER
          (Fillers, Repetitions, Tech Vocab)
                           │
                           ▼
               SHARED JARVIS ORCHESTRATOR
               (ReAct Reasoning & Tools)
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      SHARED MEMORY               SHARED TOOLS
   (Working & Episodic)       (File, Web, OS, Dev)
             │                           │
             └─────────────┬─────────────┘
                           ▼
                 VERIFIED OUTCOME
                           │
                           ▼
                 VOICE PRESENTATION
             (Concise Spoken Summarizer)
                           │
                           ▼
                  NEURAL TTS ENGINE
              (Edge-TTS / OneCore SAPI5)
                           │
                 ACOUSTIC ECHO GATING
                           │
                    USER INTERRUPTS
                           │
                           ▼
                NEW CAPTURE & DISPATCH
```

---

## 2. Core Architectural Pillars

### 2.1 Centralized Audio Capture (`AudioBus`)
- **Single Producer**: Exactly one `sounddevice.RawInputStream` captures from the primary soundcard.
- **Multiple Subscribers**:
  - `assistant_main_mic`: Feeds command speech recognition (`speech_recognition.Recognizer`).
  - `barge_in_monitor`: Real-time VAD speech monitoring during TTS playback.
  - `noise_calibrator`: Background ambient noise floor sampling and drift tracking.
- **Ring Buffer Pre-Roll**: Maintains a 500ms rolling PCM buffer ensuring zero audio truncation during wake detection transitions.

### 2.2 Explicit Finite State Machine (`VoiceStateMachine`)
Tracks 16 formal states with strict transition guards:
- `IDLE`: Base resting state.
- `WAKE_DETECTION`: Listening passively for "Jarvis" / "Hey Jarvis".
- `WAKE_CONFIRMED`: Wake detected; acoustic chime triggered.
- `LISTENING_FOR_COMMAND`: Active command window opened.
- `CAPTURING`: Collecting user speech PCM frames.
- `TRANSCRIBING`: Processing speech through STT fallback pipeline.
- `UNDERSTANDING`: Running prompt refinement, intent extraction, vocabulary mapping.
- `PLANNING`: Orchestrator decomposing task steps.
- `EXECUTING`: Real tool execution (file operations, web search, OS automation).
- `RESPONDING`: Synthesizing evidence from tools into final result.
- `SPEAKING`: Neural TTS streaming audio playback.
- `WAITING_APPROVAL`: Prompting user for destructive operation confirmation.
- `WAITING_USER`: Awaiting user clarification (e.g. "DOCX or PDF?").
- `INTERRUPTED`: Barge-in detected during speech; TTS halted instantly.
- `CANCELLED`: User verbal cancellation ("Stop", "Never mind").
- `MUTED`: Audio input muted by user hotkey or UI.
- `RECOVERING`: Watchdog reconnecting detached hardware device.
- `ERROR`: Classified failure state with structured diagnostics.

### 2.3 STT Fallback & Confidence Pipeline
1. **Primary STT**: Dedicated Online Gemini Flash REST API (in-memory base64 WAV payload, <300ms).
2. **Local STT**: 100% Offline CTranslate2 `faster-whisper` / `openai-whisper` (zero network dependency).
3. **Secondary STT**: Google Speech Recognition fallback.
4. **Confidence Scoring**: Classifies transcript into `HIGH_CONFIDENCE`, `MEDIUM_CONFIDENCE`, `LOW_CONFIDENCE`, or `UNKNOWN`.
5. **Clarification Protocol**: Low-confidence or ambiguous requests trigger structured clarification questions rather than guessing.

### 2.4 Prompt Refinement & Domain Technical Dictionary
- Collapses repetitive ASR token stutter loops (`"hey hey hey"` -> `"hey"`).
- Strips filler hesitations (`"um"`, `"uh"`, `"ah"`, `"hmm"`) and polite prefix bloat.
- Applies domain vocabulary preservation:
  `OpenClaw`, `FastAPI`, `ChromaDB`, `Playwright`, `PowerShell`, `Docker`, `MCP`, `Telegram`, `Gemini`, `Python`, `GitHub`, `API`, `WebSocket`, `DOCX`, `PDF`, `JSON`, `CSV`.
- Retains three audit levels: `raw_transcript`, `normalized_transcript`, and `execution_prompt`.

### 2.5 Acoustic Echo Gating & Interruption (Barge-In)
- While TTS is speaking, `AudioBus.is_echo_gate_active` is asserted `True`.
- `SileroVAD` dynamically raises the speech probability threshold (0.72) and requires SNR >8.5 dB.
- When human speech is confirmed:
  1. TTS playback stops within <10ms.
  2. State transitions to `INTERRUPTED`.
  3. Pre-roll speech frames are preserved so the interrupting utterance is not lost.
  4. AudioBus command queue is drained and active capture begins.

### 2.6 Shared Cognitive Execution
- Spoken tasks route directly to `self.orchestrator.chat(refined_prompt)`.
- Tools execute on the real machine through the unified tool registry (`file_controller`, `web_search`, `open_app`, `dev_agent`, `scratchpad_eval`, etc.).
- Outlines, lessons, and working memory are stored in the canonical memory engine.
