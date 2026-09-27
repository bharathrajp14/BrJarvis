# 07 — MODEL PROVIDERS & GATEWAY FORENSIC RECORD

## 1. Overview & Architecture
BR JARVIS interfaces with multiple cloud LLMs and local models across two distinct subsystems: `backends/` (direct vendor adapters) and `gateway/` (proxy client and load balancer).

---

## 2. Multi-Model Architecture Matrix
| Model / Tier | Provider Adapter | Model ID | Modalities | Tool Calling | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gemini 2.5 Flash** | `backends/gemini.py` | `gemini-2.5-flash` | Text, Vision, Audio | Native JSON | Fast queries, Voice STT, Vision analysis |
| **Gemini 2.5 Pro** | `backends/gemini.py` | `gemini-2.5-pro` | Text, Vision | Native JSON | Deep reasoning, Architecture, Complex coding |
| **Claude 3.7 Sonnet**| `backends/anthropic.py`| `claude-3-7-sonnet` | Text, Vision | Tool Use API | Code synthesis, Refactoring, Complex DAGs |
| **DeepSeek R1 / V3** | `backends/deepseek.py` | `deepseek-reasoner` | Text | XML / Markdown | Algorithmic logic, Math, Verification |
| **Mistral Large** | `backends/mistral.py` | `mistral-large` | Text | Native JSON | Fallback reasoning, Multilingual |
| **Nvidia NIM** | `backends/nvidia.py` | `meta/llama-3.3-70b` | Text | OpenAI-compat | Low-latency cloud inference |
| **Ollama (Local)** | `backends/ollama.py` | `qwen2.5:7b` / `llama3.2` | Text | Structured Schema | 100% Offline fallback mode |

---

## 3. Detailed Forensic Findings

### A. Triplicate Model Gateway Abstraction
1. `backends/adapter.py`: Implements `BaseProviderAdapter` interface for local vendor SDKs (`google-genai`, `anthropic`, `httpx`).
2. `gateway/model_gateway.py`: Implements circuit-breakers, exponential backoff, health tracking (`gateway/health.py`), and latency benchmarking (`gateway/benchmark.py`).
3. `gateway/client.py`: Implements `ProxyBrainClient` which sends queries to a remote HTTP proxy endpoint (`PROXY_BRAIN_URL`).
*Finding*: The codebase has two divergent invocation philosophies (Local Direct API Keys vs Cloud Proxy Brain).

### B. Gemini Adapter Deep Dive (`backends/gemini.py`, 469 lines)
- Implements `GeminiBackend` supporting both the new Google GenAI SDK (`google.genai`) and legacy `google.generativeai`.
- Features multi-key rotation across multiple `GEMINI_API_KEY_*` environment variables when rate-limits (HTTP 429) occur.
- Handles inline base64 image data for multimodal vision queries.
- **Disposition**: **KEEP + IMPROVE**.
