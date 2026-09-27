# BR JARVIS — MASTER RUNTIME FLOW & EXECUTION TRUTH MODEL

## 1. Master Execution Sequence
```text
[1. USER INVOCATION] (Voice PCM Audio / Text Prompt / Web API / Desktop Hotkey)
        ↓
[2. INPUT NORMALIZATION & SHIELD]
        ├─ Audio: Silero VAD (Speech Detection) -> Faster-Whisper (STT Transcription)
        ├─ Text: Token normalization, prompt-injection audit (guardian/prompt_injection_shield.py)
        ↓
[3. INTENT CLASSIFICATION & STAGE DECOMPOSITION]
        ├─ Deterministic Fast-Path: Instant local OS shortcuts (Volume, Launch, App Controls)
        └─ Cognitive Path: Multi-clause query decomposed into DAG (agent/stage_decomposer.py)
        ↓
[4. SMART MODEL ROUTING & GATEWAY]
        ├─ Router selects optimal model (Gemini 2.5, Claude 3.5, Local Ollama) based on task profile
        └─ Model Gateway handles circuit breakers, retries, and API key rotation
        ↓
[5. TOOL PROPOSAL & POLICY EVALUATION]
        ├─ LLM emits structured tool call: {"tool": "write_file", "args": {...}}
        ├─ 6-Tuple Policy Evaluation: (User, Device, App, Resource, Action, Risk)
        └─ Path Security Policy: Canonicalizes path, blocks denylist & junction traversal
        ↓
[6. UNIVERSAL TOOL EXECUTION RUNTIME]
        ├─ ArgumentNormalizer standardizes paths, URLs, booleans
        ├─ ToolRuntimeEngine executes action with strict timeout and token isolation
        └─ Captures stdout, stderr, execution latency
        ↓
[7. PHYSICAL POST-CONDITION OBSERVATION & VERIFICATION]
        ├─ ActionVerifier asserts physical state (File exists & readable, Process active, DOM loaded)
        └─ BROWSER / ARTIFACT: Ensures SHA256 host export before browser launch
        ↓
[8. EPISTEMIC STATE UPDATE & RESPONSE SYNTHESIS]
        ├─ Verified observations committed to TaskState and SQLite WAL Memory DB
        └─ Response synthesized from verified truth -> Spoken via Edge TTS & rendered in UI
```
