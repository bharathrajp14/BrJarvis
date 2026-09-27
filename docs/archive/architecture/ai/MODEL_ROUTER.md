# 🔀 Model Router & Provider Engine Specification

> **Module**: `router.py`, `reasoning/meta_cognition.py`, `reasoning/speculative.py` & `backends/`  
> **Version**: MK38.2.0  
> **Primary Purpose**: Dynamic multi-backend AI model selection, meta-cognitive risk evaluation, speculative step drafting, adaptive complexity routing, token budgeting, and automatic failover.

---

## 1. Supported Provider Backends

BR JARVIS supports 7 LLM provider backends through modular adapters in `backends/`:

| Provider | Backend Module | Primary Models | Usage Role |
|---|---|---|---|
| **Google Gemini** | `backends/gemini.py` | Gemini 3.6 Flash High, Gemini 3 Flash Agent, Gemini Pro Agent, Gemini 3.5 Flash Low | High-speed multimodal reasoning & vision |
| **Anthropic Claude** | `backends/claude.py` | Claude 3.5 Sonnet, Claude 3 Opus | Complex code synthesis & architectural design |
| **OpenAI** | `backends/openai.py` | GPT-4o, GPT-4o-mini | Standard tool invocation & structured JSON |
| **Ollama** | `backends/ollama.py` | Llama 3, Qwen 2.5, DeepSeek R1 | 100% offline local inference & privacy tasks |
| **DeepSeek** | `backends/deepseek.py` | DeepSeek R1, DeepSeek V3 | Deep chain-of-thought mathematical reasoning |
| **NVIDIA NIM** | `backends/nvidia.py` | Llama-3-70B-Instruct | High-throughput cloud inference |
| **Mistral AI** | `backends/mistral.py` | Mistral Large, Codestral | Code completion & multi-lingual synthesis |

---

## 2. Adaptive Routing & Meta-Cognitive Pipeline

```
Task Execution Request
         │
         ▼
[ DeterministicIntentEngine (core/intent_engine.py) ]
         │ (Matches 50+ 0-token system intents -> 0ms, 0 tokens)
         ├─────────────────────────────────────────┐
         │ (No match)                              │ (Matched)
         ▼                                         ▼
[ MetaCognitionEngine (reasoning/meta_cognition.py) ] Instant Execution
         │ (Evaluates Confidence score 0.0-1.0 & Risk Level)
         ▼
[ SpeculativeExecutionEngine (reasoning/speculative.py) ]
         │ (Generates draft step proposals)
         ▼
[ Multi-Objective Router (router.py) ]
         │
         ├───────────────────────┬───────────────────────┐
         ▼                       ▼                       ▼
   Simple Goal              Medium Goal             Complex Goal
   (Ollama / Gemini Flash)  (GPT-4o / Gemini 3.6)   (Claude 3.5 Sonnet / DeepSeek R1)
```

---

## 3. Token Budget Tracking & Failover Strategy

- **Token Budgeting**: `router.py` monitors input/output tokens per session, enforcing configurable soft and hard limits.
- **Multi-Objective Routing (`select_multi_objective_backend()`)**:
  Computes a dynamic utility score balancing model quality, token cost, and estimated latency:
  $$\text{Score} = (\text{Quality} \times w_{\text{quality}}) - (\text{EstCost} \times w_{\text{cost}}) - (\text{EstLatency} \times w_{\text{latency}})$$
- **Failover Cascade**: If a primary backend fails (e.g. Rate Limit 429 or API Error 500), the router automatically attempts the fallback chain:
  `gemini-3.5-flash-low -> gemini-3-flash -> gemini-3.6-flash-high -> gemini-3-flash-agent -> gemini-pro-agent -> gemini-2.0-flash -> Claude 3.5 Sonnet -> GPT-4o -> Local Ollama`.
