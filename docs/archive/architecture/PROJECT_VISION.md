# 👁️ BR JARVIS — Project Vision & Identity (Project BR)

## Project Identity
- **Project Name**: BR JARVIS
- **Codename**: Project BR
- **Version**: 38.0.0 (MK38 Architecture)
- **Category**: Local-First Autonomous Artificial Intelligence Operating System (AIOS)

---

## 🎯 Mission Statement
BR JARVIS is NOT a chatbot. It is NOT merely an automation script or simple voice assistant.

BR JARVIS is a next-generation **AI Operating System (AIOS)** designed to act as a complete cognitive partner capable of understanding, reasoning, planning, learning, observing, and operating digital environments with human-level workflow intelligence and absolute local safety.

---

## 💡 Core Philosophy & Engineering Principles

### 1. Goal-Oriented Execution & Planning Mode
Users describe goals in natural language. BR JARVIS understands intent, dynamically evaluates task complexity via `agent/planning_mode.py`, generates standard GFM implementation plans (`implementation_plan.md`), executes task DAGs, logs step trajectory transcripts (`transcript.jsonl`), verifies results, recovers from failures, and continuously optimizes performance.

### 2. Local-First & Zero-Token Efficiency
Prioritizes local AI models (Ollama, local Whisper STT, fast FNV-1a hashing) and 50+ zero-token deterministic intent triggers (`core/intent_engine.py`) whenever possible, seamlessly augmenting with cloud backends (Gemini, Claude, GPT, DeepSeek, NVIDIA, Mistral) for high-reasoning tasks.

### 3. Absolute Efficiency & Speed
Every architectural decision prioritizes:
- Prompt payload compression and context reference resolution (`orchestrator._resolve_context_references`)
- 5-tier response, vector, SQLite, and FNV-1a hashing memory caches
- Low latency (<5ms zero-token intents, <10ms accessibility extractions) and minimal RAM overhead
- Modularity & clean architecture (SOLID principles across 30+ core packages)

### 4. Human-in-the-Loop Safety & Guardian Core
Destructive OS operations (deleting files, git pushes, production deployments, system config changes) automatically pass through `guardian/path_policy.py` and permission interlocks before execution. A global kill-switch (`guardian/kill_switch.py`) and automatic rollback engine (`guardian/rollback.py`) safeguard user assets at all times.

### 5. Multi-Modal Vision & Desktop Mastery
BR JARVIS observes desktop screens via a 7-tier hybrid vision engine (Accessibility API, Browser DOM CDP bridge, local Tesseract OCR) and operates desktop apps natively via mouse, keyboard, and 5-tier clipboard engine with visual target trace overlays.
