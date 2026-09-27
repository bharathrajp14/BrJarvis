# BR JARVIS — FINAL CANONICAL RUNTIME EXECUTION FLOWS

## 1. Unified Master Cognitive Loop
Every interaction (Voice, Screen Automation, GUI Chat, CLI, Web API) flows through a single canonical cognitive loop:

```text
[1. INGESTION]
   User Input (Voice Audio / Text / Screen Frame / Web Request)
     ↓
[2. NORMALIZATION & PRE-FILTERING]
   Voice: Silero VAD v5 (30ms) -> Faster-Whisper -> Filler Stripping (voice/prompt_refiner.py)
   Text: Prompt Injection Shield (guardian/prompt_injection_shield.py)
     ↓
[3. CONTEXT ENRICHMENT]
   Working Memory (memory/working.py)
   + Semantic Vector Recall (memory/vector_store.py)
   + Knowledge Graph Query (memory/canonical_db.py)
   + Active Task State (agent/task_state.py)
     ↓
[4. DUAL-PATH INTENT ROUTER]
   core/intent_engine.py
   ├─ [FAST-PATH MATCH: Zero-Token Deterministic Heuristics]
   │    ↓
   │  Policy Validation (security/policy_engine.py) -> Direct Execution -> Response (< 1ms)
   │
   └─ [COGNITIVE-PATH: Complex Reasoning Required]
        ↓
[5. MODEL ROUTING & INVOCATION]
   router/smart_router.py (Task Complexity & Latency-Aware Multi-Factor Ranking)
     ↓
   gateway/model_gateway.py (Circuit-Breakers, Multi-Key Rotation, Quota Fallback)
     ↓
   LLM Generation (Gemini 2.5 Flash / Claude 3.7 / DeepSeek R1 / Ollama Local)
     ↓
[6. EXECUTION TRUTH & VERIFICATION LOOP]
   Model proposes Tool Invocation
     ↓ [STATE: PROPOSED]
   security/policy_engine.py (6-Tuple Authorization: User, Device, App, Resource, Action, Risk)
     ├─ [DENIED] -> Policy Error returned to Model Context -> Model Replans
     └─ [AUTHORIZED] -> [STATE: AUTHORIZED]
          ↓
        agent/executor.py -> tools/registry.py (Tool Execution in Sandbox or Host OS)
          ↓ [STATE: EXECUTED]
        agent/verifier.py (Physical Post-Condition Verification: File exists? Process running? HTTP 200?)
          ├─ [VERIFIED: TRUE] -> [STATE: VERIFIED] -> Result fed to Model
          └─ [VERIFIED: FALSE] -> [STATE: FAILED] -> agent/recovery_engine.py -> Re-planning
     ↓
[7. MEMORY CONSOLIDATION & EXPERIENCE]
   Episodic Transcript Store (history/session_store.py)
   + Procedural Lesson Extraction (memory/canonical_db.py :: lessons table)
     ↓
[8. MULTIMODAL RESPONSE DISPATCH]
   Text Response -> GUI Timeline / CLI Output
   + Audio Synthesis -> voice/tts_queue.py -> voice/tts.py (Streaming Edge TTS with Barge-In)
```
