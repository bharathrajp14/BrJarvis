# 04 — END-TO-END RUNTIME EXECUTION FLOWS

## 1. Text & Query Execution Flow
```text
User Input (CLI / Web / UI)
  ↓
core/intent_engine.py (Regex / Fast Heuristics Check)
  ├─ [Match: Fast-Path Rule] → Direct Action Execution (e.g. Open App, Set Volume) → Response
  └─ [No Match: Complex Query]
       ↓
orchestrator/core.py (JarvisOrchestrator.process_query)
  ↓
context/builder.py + memory/unified_memory.py (Context Assembly & History Recall)
  ↓
router/core.py (Model Selection: Fast / Advanced / Vision / Local)
  ↓
gateway/model_gateway.py (Model Invocation with Failover & Circuit Breaker)
  ↓
[Model Output: Tool Invocation Required]
  ↓
security/policy_engine.py (6-Tuple Permission Validation: User/Device/Resource/Action/Risk)
  ├─ [DENIED] → Policy Violation Error → Orchestrator Re-planning
  └─ [ALLOWED]
       ↓
agent/executor.py (Tool Execution in Sandbox or Host OS)
  ↓
agent/verifier.py (Post-Condition State Verification)
  ↓
memory/unified_memory.py (Turn Consolidation & Knowledge Graph Update)
  ↓
UI / CLI / TTS Audio Response Output
```

---

## 2. Voice Pipeline Flow (Low-Latency Audio Loop)
```text
Microphone Input Stream (voice/stt.py :: SounddeviceMicrophone)
  ↓
voice/ring_buffer.py (Continuous 500ms Pre-roll Ring Buffer)
  ↓
voice/silero_vad.py (Silero VAD v5 Frame Evaluation: 30ms frames)
  ├─ [Silence / Noise] → Dropped (Adaptive Noise Floor Calibration in voice/noise_calibrator.py)
  └─ [Speech Detected]
       ↓
voice/whisper_local.py OR voice/gemini_stt.py (Speech-To-Text Transcriber)
  ↓
voice/prompt_refiner.py (Filler word removal: "uh", "um", wake word stripping)
  ↓
orchestrator/core.py (Cognitive Dispatch)
  ↓
voice/tts_queue.py (Priority Speech Queue with Barge-In Cancellation)
  ↓
voice/tts.py (Edge TTS / Local Piper / Windows SAPI5)
  ↓
Audio Output Device (Speakers / Headphones)
```

---

## 3. Vision & Screen Automation Flow
```text
Vision Request / Screen Automation Intent
  ↓
vision/screen_analyst.py (Multi-Monitor Capture via DXGI / Win32 GDI)
  ↓
vision/hybrid_pipeline.py (Dual Resolution Processing: High-res for OCR, Low-res for VLM)
  ├─ vision/ocr_engine.py (Tesseract / Windows OCR / EasyOCR Element Bounding Boxes)
  ├─ vision/accessibility.py (Win32 UI Automation Accessibility Tree)
  └─ vision/dom_bridge.py (Chrome DevTools Protocol for Web Browsers)
       ↓
computer/semantic_operator.py (Element Resolution & Coordinate Translation)
  ↓
security/policy_engine.py (Destructive Action Check: e.g. Close window, Submit form)
  ↓
computer/operator.py (PyAutoGUI / Win32 SendInput Mouse & Keyboard Execution)
  ↓
computer/recovery.py (Self-Healing Visual Verification)
```

---

## 4. Failure Recovery & Self-Healing Re-Planning Flow
```text
Tool Execution Failure / API Rate Limit / Network Disconnect
  ↓
router/diagnostics.py (Failure Classification: TIMEOUT / PERMISSION / AUTH / SYNTAX / RATE_LIMIT)
  ↓
agent/recovery_engine.py (Recovery Strategy Selection)
  ├─ [RATE_LIMIT] → Fallback to secondary model backend (e.g. Gemini → Claude → Ollama)
  ├─ [SYNTAX / SCHEMA] → Dynamic JSON Prompt Repair & One-Shot Re-prompt
  ├─ [TOOL_ERROR] → Alternative Tool Selection (e.g. Browser CDP → Direct HTTP Request)
  └─ [FATAL] → Graceful Degradation Message to User & Rollback via guardian/rollback.py
```
