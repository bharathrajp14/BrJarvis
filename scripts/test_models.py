"""
scripts/test_models.py — BR JARVIS Model Availability Prober
Tests every model across all three provider tiers and prints a live report.
"""
from __future__ import annotations

import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import NamedTuple

# ── Load .env ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

try:
    import openai
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)

# ── Provider configs ─────────────────────────────────────────────────────────
PROXY_BASE  = os.environ.get("BRJARVIS_PROXY_BASE_URL", "http://127.0.0.1:20128/v1")
PROXY_KEY   = os.environ.get("BRJARVIS_PROXY_API_KEY",  os.environ.get("OPENAI_API_KEY", ""))
OR_BASE     = os.environ.get("OPENROUTER_BASE_URL",     "https://openrouter.ai/api/v1")
OR_KEY      = os.environ.get("OPENROUTER_API_KEY",      "")
OMR_BASE    = os.environ.get("OMNIROUTER_BASE_URL",     "http://127.0.0.1:20128/v1")
OMR_KEY     = os.environ.get("OMNIROUTER_API_KEY",      "")

# ── All models to probe ───────────────────────────────────────────────────────
PROXY_MODELS = [
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
    "github/gpt-4o-mini",
]

OPENROUTER_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "google/gemma-3-27b-it:free",
    "deepseek/deepseek-r1-0528:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free",
]

OMNIROUTER_MODELS = [
    "auto/chat",
    "auto/best-chat",
    "auto/best-coding",
    "auto/best-reasoning",
    "auto/best-vision",
    "auto/fast",
]

PROBE_PROMPT = [{"role": "user", "content": "Reply with exactly: OK"}]


class Result(NamedTuple):
    tier: str
    model: str
    ok: bool
    latency_ms: float
    reply: str
    error: str


def probe(tier: str, model: str, base_url: str, api_key: str, timeout: int = 25) -> Result:
    t0 = time.perf_counter()
    if not api_key:
        return Result(tier, model, False, 0.0, "", "NO API KEY")
    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        resp = client.chat.completions.create(
            model=model,
            messages=PROBE_PROMPT,
            max_tokens=10,
        )
        latency = (time.perf_counter() - t0) * 1000
        reply = (resp.choices[0].message.content or "").strip()[:40]
        return Result(tier, model, True, latency, reply, "")
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        err = str(e)[:80]
        return Result(tier, model, False, latency, "", err)


def run_parallel(jobs: list) -> list:
    results = [None] * len(jobs)
    lock = threading.Lock()

    def worker(idx, args):
        r = probe(*args)
        with lock:
            results[idx] = r
            status = "PASS" if r.ok else "FAIL"
            info = repr(r.reply) if r.ok else r.error
            print(f"  [{status}] [{r.tier:<10}] {r.model:<42} {r.latency_ms:>7.0f}ms  {info}")

    threads = [threading.Thread(target=worker, args=(i, j), daemon=True) for i, j in enumerate(jobs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=35)
    return [r for r in results if r is not None]


def main():
    print()
    print("=" * 80)
    print("  BR JARVIS — MODEL AVAILABILITY PROBER")
    print(f"  Proxy     : {PROXY_BASE}  key={'SET' if PROXY_KEY else 'MISSING'}")
    print(f"  OpenRouter: {OR_BASE}  key={'SET' if OR_KEY else 'MISSING'}")
    print(f"  OmniRouter: {OMR_BASE}  key={'SET' if OMR_KEY else 'MISSING'}")
    print("=" * 80)

    jobs = []
    for m in PROXY_MODELS:
        jobs.append(("PROXY", m, PROXY_BASE, PROXY_KEY))
    for m in OPENROUTER_MODELS:
        jobs.append(("OPENROUTER", m, OR_BASE, OR_KEY))
    for m in OMNIROUTER_MODELS:
        jobs.append(("OMNIROUTER", m, OMR_BASE, OMR_KEY))

    print(f"\n  Probing {len(jobs)} models in parallel (timeout 25s each)...\n")
    t_start = time.perf_counter()
    results = run_parallel(jobs)
    elapsed = time.perf_counter() - t_start

    ok_results   = [r for r in results if r.ok]
    fail_results = [r for r in results if not r.ok]

    print()
    print("=" * 80)
    print(f"  RESULTS: {len(ok_results)}/{len(results)} models ONLINE  ({elapsed:.1f}s total)")
    print("=" * 80)

    if ok_results:
        print("\n  WORKING MODELS:")
        print(f"  {'Tier':<12} {'Model':<42} {'Latency':>9}  Reply")
        print(f"  {'-'*12} {'-'*42} {'-'*9}  -----")
        for r in sorted(ok_results, key=lambda x: x.latency_ms):
            print(f"  {r.tier:<12} {r.model:<42} {r.latency_ms:>7.0f}ms  {repr(r.reply)}")

    if fail_results:
        print("\n  FAILED / OFFLINE MODELS:")
        print(f"  {'Tier':<12} {'Model':<42}  Error")
        print(f"  {'-'*12} {'-'*42}  -----")
        for r in sorted(fail_results, key=lambda x: x.tier):
            print(f"  {r.tier:<12} {r.model:<42}  {r.error}")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(results),
        "online": len(ok_results),
        "offline": len(fail_results),
        "working": [
            {"tier": r.tier, "model": r.model, "latency_ms": round(r.latency_ms)}
            for r in sorted(ok_results, key=lambda x: x.latency_ms)
        ],
        "failed": [
            {"tier": r.tier, "model": r.model, "error": r.error}
            for r in fail_results
        ],
    }
    out = BASE_DIR / "workspace" / "model_probe_report.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n  Report saved -> {out}")
    print("=" * 80)
    print()
    return 0 if ok_results else 1


if __name__ == "__main__":
    sys.exit(main())
