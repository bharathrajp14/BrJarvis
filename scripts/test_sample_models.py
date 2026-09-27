"""
scripts/test_sample_models.py
Rapidly test a representative set of models from different providers/prefixes
to discover which backends are actually live and responding in OmniRouter.
"""
import time
import json
import os
import openai

BASE_URL = os.environ.get("OMNIROUTER_BASE_URL", "http://localhost:20128/v1")
API_KEY = os.environ.get("OMNIROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY") or "sk-local-omnirouter"

client = openai.OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=8.0)

SAMPLE_MODELS = [
    # Auto modes
    "auto/chat",
    "auto/fast",
    "auto/coding",
    "auto/best-chat",
    "auto/best-coding",
    "auto/best-reasoning",
    "auto/best-vision",
    "auto/pro-chat",
    "auto/pro-coding",
    "auto/pro-reasoning",
    "auto/reasoning",
    "auto/smart",
    "auto/gemini",
    "auto/claude-sonnet",
    "auto/claude-opus",
    
    # Antigravity namespace
    "antigravity/gemini-3.7-flash-high",
    "antigravity/gemini-3.7-flash-low",
    "antigravity/gemini-pro-agent",
    "antigravity/gemini-3.1-pro-low",
    "antigravity/claude-sonnet-4-6",
    "antigravity/claude-opus-4-6-thinking",
    "antigravity/gpt-oss-120b-medium",
    "antigravity/gemini-3.1-flash-image",

    # CL / Cline namespace
    "cl/google/gemini-3.8-flash",
    "cl/openai/gpt-4.1",
    "cl/openai/o3-mini",
    "cl/openai/o3",
    "cl/anthropic/claude-opus-5",
    "cl/deepseek/deepseek-v4.1-flash",
    "cl/meta-llama/llama-3.3-70b-instruct",
    "cl/qwen/qwen3.8-max-0902",

    # KR / Kiro namespace
    "kr/claude-sonnet-4.5",
    "kr/deepseek-3.2",
    "kr/qwen3-coder-next",

    # GitHub namespace
    "github/gpt-4o-mini",
    "gh/gpt-4o-mini",

    # OpenRouter namespace
    "openrouter/google/gemini-2.5-flash",
    "openrouter/anthropic/claude-3.5-sonnet",
    "openrouter/meta-llama/llama-3.1-8b-instruct:free",
]

def probe(m):
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=15,
            temperature=0.1
        )
        dt = (time.perf_counter() - t0) * 1000
        text = (resp.choices[0].message.content or "").strip()
        return {"model": m, "status": "PASS", "latency": dt, "reply": text, "error": None}
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000
        return {"model": m, "status": "FAIL", "latency": dt, "reply": None, "error": str(e)[:100]}

def main():
    print(f"--- Probing {len(SAMPLE_MODELS)} sample models with 8s timeout ---", flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(probe, m): m for m in SAMPLE_MODELS}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            results.append(res)
            tag = "PASS" if res["status"] == "PASS" else "FAIL"
            print(f"[{tag}] {res['model']:<45} {res['latency']:>6.0f}ms | {res['reply'] or res['error']}", flush=True)

    passed = [r for r in results if r["status"] == "PASS"]
    print(f"\nCompleted: {len(passed)}/{len(SAMPLE_MODELS)} models passed.", flush=True)
    if passed:
        print("\nWorking models (sorted by latency):", flush=True)
        for p in sorted(passed, key=lambda x: x["latency"]):
            print(f"  {p['model']:<45} {p['latency']:>6.0f}ms -> {p['reply']}", flush=True)

if __name__ == "__main__":
    main()
