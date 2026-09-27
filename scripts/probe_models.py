# scripts/probe_models.py — Fast Concurrent Model Probe for Proxy Brain
import concurrent.futures
import json
import os
import time
import requests

def main():
    base_url = os.environ.get('BRJARVIS_PROXY_BASE_URL', os.environ.get('OPENAI_BASE_URL', 'http://127.0.0.1:20128/v1')).rstrip('/')
    api_key = os.environ.get('BRJARVIS_PROXY_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
    if not api_key:
        try:
            from pathlib import Path
            cfg_file = Path(__file__).resolve().parent.parent / "config" / "api_keys.json"
            if cfg_file.exists():
                data = json.loads(cfg_file.read_text(encoding="utf-8"))
                api_key = data.get("proxy_api_key") or data.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
        except Exception:
            api_key = os.environ.get("OPENAI_API_KEY", "")
    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    print(f"Target Gateway: {base_url}", flush=True)
    print("-" * 80, flush=True)

    # 1. Discover models from GET /v1/models
    discovered = []
    try:
        r = requests.get(f"{base_url}/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=4)
        if r.status_code == 200:
            data = r.json()
            discovered = [m.get("id") for m in data.get("data", []) if m.get("id")]
            print(f"Discovered {len(discovered)} models from /v1/models:", flush=True)
            for m in sorted(discovered):
                print(f"  • {m}", flush=True)
        else:
            print(f"Notice: /v1/models returned HTTP {r.status_code}", flush=True)
    except Exception as e:
        print(f"Could not query /v1/models: {e}", flush=True)

    # 2. Candidate models
    candidates = [
        "antigravity/gemini-3.7-flash-high",
        "antigravity/gemini-3.7-flash-medium",
        "antigravity/gemini-3.7-flash-low",
        "antigravity/gemini-pro-agent",
        "antigravity/gemini-3.1-pro-low",
        "antigravity/gemini-3.1-flash-lite",
        "antigravity/claude-sonnet-4-6",
        "antigravity/claude-opus-4-6-thinking",
        "kr/claude-sonnet-4.5",
        "kr/deepseek-3.2",
        "kr/qwen3-coder-next",
        "auto/chat",
        "auto/best-chat",
        "auto/best-coding",
        "auto/best-reasoning",
        "auto/best-vision",
        "auto/fast",
        "github/gpt-4o-mini",
    ]

    test_list = list(dict.fromkeys(discovered + candidates)) if discovered else candidates

    print(f"\nTesting {len(test_list)} models concurrently...", flush=True)
    print("=" * 80, flush=True)

    def test_model(model: str):
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Respond with exactly: pong"}],
            "max_tokens": 15,
            "temperature": 0.1
        }
        t0 = time.monotonic()
        try:
            r = requests.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=8
            )
            dt = int((time.monotonic() - t0) * 1000)
            if r.status_code == 200:
                res = r.json()
                reply = res.get("choices", [{}])[0].get("message", {}).get("content", "").strip().replace("\n", " ")[:60]
                return {"status": "ACTIVE", "model": model, "latency": dt, "reply": reply}
            else:
                err = r.text.replace("\n", " ")[:60]
                return {"status": "INACTIVE", "model": model, "latency": dt, "error": f"HTTP {r.status_code}: {err}"}
        except Exception as e:
            dt = int((time.monotonic() - t0) * 1000)
            return {"status": "ERROR", "model": model, "latency": dt, "error": str(e)[:60]}

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(test_model, m): m for m in test_list}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            if res["status"] == "ACTIVE":
                print(f"  [ONLINE]  {res['model']:<28} | {res['latency']:>5} ms | reply: \"{res['reply']}\"", flush=True)
            else:
                print(f"  [OFFLINE] {res['model']:<28} | {res['latency']:>5} ms | {res.get('error', '')}", flush=True)

    working = [r for r in results if r["status"] == "ACTIVE"]
    failed = [r for r in results if r["status"] != "ACTIVE"]

    print("=" * 80, flush=True)
    print(f"Summary: {len(working)} ONLINE / WORKING, {len(failed)} OFFLINE / INACTIVE.", flush=True)


if __name__ == "__main__":
    main()

