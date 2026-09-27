# BR JARVIS — FINAL MODEL GATEWAY & ROUTER ARCHITECTURE

## 1. Architectural Invariants
1. **Single Invocation Gateway**: `gateway/model_gateway.py` is the single gateway through which all cloud and local model calls flow. Direct ad-hoc API client instantiation in feature modules is prohibited.
2. **Deterministic Fallback Pipeline**: Primary Cloud (Gemini 2.5 Flash / Claude 3.7) → Multi-Key Rotation → Secondary Cloud (Mistral / Nvidia) → 100% Offline Local (Ollama Qwen2.5-7B).
3. **Structured Diagnostics**: On failure, the gateway returns a rich `TaskExecutionDiagnostic` containing `provider`, `model`, `stage`, `failure_type`, `retry_count`, `fallback_chain`, and `trace_id`.

---

## 2. Multi-Factor Routing Matrix (`router/smart_router.py`)

$$\text{RoutingScore} = \text{TaskFit} \times \text{CapabilityMatch} \times \text{QualityScore} \times \text{HealthFactor} \times \text{LatencyFactor} \times \text{ProviderPreference}$$

| Model Profile | Provider | Modalities | Primary Task Domain | Fallback Candidate |
| :--- | :--- | :--- | :--- | :--- |
| **`gemini-flash`** | Google GenAI | Text, Vision, Audio | Fast queries, voice dialogues, live OCR, general chat | `claude-sonnet` / `ollama-local` |
| **`gemini-pro`** | Google GenAI | Text, Vision | Deep multimodal analysis, massive context (>100k tokens) | `claude-sonnet` |
| **`claude-sonnet`**| Anthropic | Text, Vision | Complex code synthesis, refactoring, multi-step DAGs | `gemini-pro` / `deepseek-r1` |
| **`deepseek-r1`** | DeepSeek | Text | Deep algorithmic reasoning, logic puzzles, formal verification| `claude-sonnet` |
| **`ollama-local`** | Local Ollama | Text | 100% Offline execution, air-gapped tasks, fallback on network cut | Pure-Python heuristics |
