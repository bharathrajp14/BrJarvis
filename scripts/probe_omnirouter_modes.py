"""
scripts/probe_omnirouter_modes.py
Probes OmniRouter auto modes and antigravity models on http://localhost:20128/v1
"""
import time
import json
import os
import openai

BASE_URL = os.environ.get("OMNIROUTER_BASE_URL", "http://localhost:20128/v1")
API_KEY = os.environ.get("OMNIROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY") or "sk-local-omnirouter"

client = openai.OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=25.0)

def test_model(model_id, prompt="Hello, respond with the exact word 'READY' and your model name if known."):
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.1,
        )
        dt = (time.perf_counter() - t0) * 1000
        reply = (resp.choices[0].message.content or "").strip()
        return {
            "model": model_id,
            "status": "PASS",
            "latency_ms": round(dt, 1),
            "reply": reply[:100],
            "error": None
        }
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000
        return {
            "model": model_id,
            "status": "FAIL",
            "latency_ms": round(dt, 1),
            "reply": None,
            "error": str(e)[:150]
        }

def main():
    with open('workspace/omnirouter_models.json', 'r', encoding='utf-8') as f:
        all_models = json.load(f)

    # 1. Target auto modes
    auto_models = [m for m in all_models if m.startswith('auto/')]
    
    # 2. Antigravity models
    antigravity_models = [m for m in all_models if m.startswith('antigravity/')]

    # 3. High quality frontier candidates
    frontier_candidates = [
        "cl/google/gemini-3.8-flash",
        "kr/claude-sonnet-4.5",
        "kiro/claude-sonnet-4.5",
        "cl/openai/gpt-4.1",
        "cl/openai/o3-mini",
        "cl/openai/o3",
        "kr/deepseek-3.2",
        "cl/deepseek/deepseek-v4.1-flash",
        "cl/meta-llama/llama-3.3-70b-instruct",
        "kr/qwen3-coder-next"
    ]
    frontier_candidates = [m for m in frontier_candidates if m in all_models]

    test_list = auto_models + antigravity_models + frontier_candidates
    print(f"Testing {len(test_list)} models across auto modes, antigravity, and frontier models...")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {pool.submit(test_model, m): m for m in test_list}
        for f in concurrent.futures.as_completed(future_map):
            res = f.result()
            results.append(res)
            icon = "[PASS]" if res["status"] == "PASS" else "[FAIL]"
            print(f"{icon} {res['model']:<45} {res['latency_ms']:>6.0f}ms | {res['reply'] or res['error']}")

    with open("workspace/omnirouter_probe_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    passed = [r for r in results if r["status"] == "PASS"]
    failed = [r for r in results if r["status"] == "FAIL"]
    print("\n" + "="*80)
    print(f"Summary: {len(passed)}/{len(results)} passed, {len(failed)} failed.")
    print("="*80)

if __name__ == "__main__":
    main()
