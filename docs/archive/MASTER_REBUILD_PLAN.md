# BR JARVIS — MASTER REBUILD & MODERNIZATION PLAN

## 1. Current System Summary
Exhaustive forensic analysis of all 2,037 files in the repository confirms that BR JARVIS is a powerful, production-grade AI operating system with advanced multimodal and automation capabilities, currently encumbered by evolutionary layer fragmentation.

---

## 2. Major Architectural Problems & Remediation
1. **Duplicate Bootstrapping**: Consolidate `core/bootstrapper.py` and `start.py` into canonical `core/bootstrap.py`.
2. **Competing Model Callers**: Unify `backends/`, `gateway/`, and `router/` into a single Gateway layer.
3. **Duplicate Tool & Action Implementations**: Refactor 58 files in `actions/` into standard tools in `tools/` and connectors in `connectors/`.
4. **Memory Store Fragmentation**: Migrate 8 independent storage locations to `.jarvis/jarvis_core.db`.
5. **Monolithic Modules**: Split `core/intent_engine.py` rules into structured configuration.
6. **Browser Profile Git Tracking**: Clean up `workspace/browser_user_data` and enforce `.gitignore`.

---

## 3. Target Subsystem Blueprints

### A. Runtime Architecture (`core/`)
- Single entrypoint bootstrap via `core/bootstrap.py`.
- Thread-safe DI Container in `core/di.py`.
- Graceful lifecycle management in `core/lifecycle.py`.

### B. Model Architecture (`gateway/` & `backends/`)
- `gateway/model_gateway.py` routes all requests with circuit-breakers and fallback.
- Direct SDK adapters in `backends/` (Gemini, Claude, DeepSeek, Mistral, Ollama).

### C. Tool & Connector Architecture (`tools/` & `connectors/`)
- Declarative JSON schemas for all tools.
- External services (GitHub, Slack, Notion, Weather, News) managed in `connectors/hub.py`.

### D. Memory Architecture (`memory/`)
- Single unified coordinator `memory/unified_memory.py`.
- Relational state in `.jarvis/jarvis_core.db`.
- Vector embeddings in `memory/vector_store.py`.

### E. Voice & Vision Architecture (`voice/`, `vision/`)
- Silero VAD v5 + Faster-Whisper + Edge TTS with priority queue and barge-in.
- Multi-monitor DXGI capture + Windows OCR + Accessibility Tree.

---

## 4. Execution Phases Summary
- **Phase 1: Security, Gitignore & Privacy Hardening** (Remove browser cache from git, verify path policy).
- **Phase 2: Bootstrapper & Lifecycle Consolidation** (Unify `bootstrap.py` and thin `start.py`).
- **Phase 3: Model Gateway & Provider Unification** (Standardize all LLM calls).
- **Phase 4: Tool & Action System Consolidation** (Migrate `actions/` to `tools/` and `connectors/`).
- **Phase 5: Memory & Database Store Unification** (Consolidate into `jarvis_core.db`).
- **Phase 6: Full Regression & E2E Validation** (Run all 116 test suites).
