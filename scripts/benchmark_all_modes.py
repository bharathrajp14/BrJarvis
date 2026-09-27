"""
scripts/benchmark_all_modes.py
Comprehensive multi-mode benchmark for OmniRouter (http://localhost:20128/v1).
Tests connectivity, latency, reasoning accuracy, coding ability, and tool-calling support.
"""
from __future__ import annotations

import time
import json
import concurrent.futures
from pathlib import Path
import os
import openai

BASE_URL = os.environ.get("OMNIROUTER_BASE_URL", "http://localhost:20128/v1")
API_KEY = os.environ.get("OMNIROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY") or "sk-local-omnirouter"

client = openai.OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=40.0)

# Models to evaluate across all modes
MODES_TO_TEST = [
    # 1. OmniRouter Auto Modes
    "auto/chat",
    "auto/fast",
    "auto/best-chat",
    "auto/best-fast",
    "auto/smart",
    "auto/coding",
    "auto/best-coding",
    "auto/best-coding-fast",
    "auto/pro-coding",
    "auto/reasoning",
    "auto/best-reasoning",
    "auto/pro-reasoning",
    "auto/best-vision",
    "auto/vision",
    "auto/pro-chat",
    "auto/claude-sonnet",
    "auto/claude-opus",
    "auto/gemini",
    "auto/best-free",

    # 2. Antigravity Suite
    "antigravity/gemini-3.7-flash-high",
    "antigravity/gemini-3.7-flash-medium",
    "antigravity/gemini-3.7-flash-low",
    "antigravity/gemini-pro-agent",
    "antigravity/gemini-3.1-pro-low",
    "antigravity/gemini-3.1-flash-lite",
    "antigravity/claude-sonnet-4-6",
    "antigravity/claude-opus-4-6-thinking",
    "antigravity/gpt-oss-120b-medium",
    "antigravity/gemini-3.1-flash-image",

    # 3. Frontier Models in Registry
    "kr/claude-sonnet-4.5",
    "kr/deepseek-3.2",
    "kr/qwen3-coder-next",
    "github/gpt-4o-mini",
    "cl/openai/gpt-4.1",
    "cl/openai/o3-mini",
    "cl/meta-llama/llama-3.3-70b-instruct"
]

def ping_test(model: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Ping. Respond with 'PONG'."}],
            max_tokens=10,
            temperature=0.0
        )
        dt = (time.perf_counter() - t0) * 1000
        content = (resp.choices[0].message.content or "").strip()
        return {"model": model, "online": True, "ping_ms": round(dt, 1), "reply": content[:40], "error": None}
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000
        return {"model": model, "online": False, "ping_ms": round(dt, 1), "reply": None, "error": str(e)[:120]}

def test_reasoning(model: str) -> dict[str, Any]:
    prompt = (
        "Solve this puzzle carefully: A bat and a baseball ball together cost $1.10. "
        "The bat costs $1.00 more than the ball. How much does the ball cost in cents? "
        "Answer with just the number of cents or amount."
    )
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.0
        )
        dt = (time.perf_counter() - t0) * 1000
        reply = (resp.choices[0].message.content or "").strip().lower()
        # Correct answer is 5 cents ($0.05)
        passed = ("5" in reply or "0.05" in reply or "five" in reply) and not ("10" in reply and "5" not in reply)
        return {"passed": passed, "latency_ms": round(dt, 1), "reply": reply[:100], "error": None}
    except Exception as e:
        return {"passed": False, "latency_ms": 0, "reply": None, "error": str(e)[:100]}

def test_coding(model: str) -> dict[str, Any]:
    prompt = (
        "Write a Python function `def is_palindrome(s: str) -> bool:` that returns True if the alphanumeric "
        "characters in s (ignoring case) form a palindrome, False otherwise. Return ONLY the code inside a python block."
    )
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.0
        )
        dt = (time.perf_counter() - t0) * 1000
        reply = resp.choices[0].message.content or ""
        passed = "def is_palindrome" in reply and ("isalnum" in reply or "[c for c in" in reply or "lower" in reply)
        return {"passed": passed, "latency_ms": round(dt, 1), "snippet": reply[:120].strip(), "error": None}
    except Exception as e:
        return {"passed": False, "latency_ms": 0, "snippet": None, "error": str(e)[:100]}

def test_tools(model: str) -> dict[str, Any]:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city and state, e.g. San Francisco, CA"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "What is the weather in Tokyo right now?"}],
            tools=tools,
            tool_choice="auto",
            max_tokens=150,
            temperature=0.0
        )
        dt = (time.perf_counter() - t0) * 1000
        choice = resp.choices[0]
        has_tool_call = False
        args = None
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                if tc.function.name == "get_current_weather":
                    has_tool_call = True
                    args = tc.function.arguments
        return {"passed": has_tool_call, "latency_ms": round(dt, 1), "args": args, "error": None}
    except Exception as e:
        return {"passed": False, "latency_ms": 0, "args": None, "error": str(e)[:100]}

def main():
    print("=" * 80, flush=True)
    print("  BR JARVIS — OMNIROUTER COMPREHENSIVE MODES BENCHMARK", flush=True)
    print(f"  Target: {BASE_URL}", flush=True)
    print("=" * 80, flush=True)

    # 1. Ping Phase
    print(f"\n[PHASE 1] Pinging {len(MODES_TO_TEST)} models...", flush=True)
    ping_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(ping_test, m): m for m in MODES_TO_TEST}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            ping_results[res["model"]] = res
            status = "ONLINE " if res["online"] else "OFFLINE"
            print(f"  [{status}] {res['model']:<42} {res['ping_ms']:>6.0f}ms | {res['reply'] or res['error']}", flush=True)

    online_models = [m for m, r in ping_results.items() if r["online"]]
    print(f"\nPhase 1 complete: {len(online_models)}/{len(MODES_TO_TEST)} models online.\n", flush=True)

    # 2. Deep Capability Evaluation Phase for Online Models
    print(f"[PHASE 2] Evaluating capabilities on {len(online_models)} online models...", flush=True)
    benchmark_data = {}

    for m in online_models:
        print(f"\n--- Testing: {m} ---", flush=True)
        # Reasoning
        r_res = test_reasoning(m)
        r_str = f"PASS ({r_res['latency_ms']:.0f}ms)" if r_res["passed"] else f"FAIL ({r_res.get('error') or r_res.get('reply')})"
        print(f"  Reasoning : {r_str}", flush=True)

        # Coding
        c_res = test_coding(m)
        c_str = f"PASS ({c_res['latency_ms']:.0f}ms)" if c_res["passed"] else f"FAIL ({c_res.get('error') or ''})"
        print(f"  Coding    : {c_str}", flush=True)

        # Tool Calling (Agent)
        t_res = test_tools(m)
        t_str = f"PASS ({t_res['latency_ms']:.0f}ms)" if t_res["passed"] else f"FAIL ({t_res.get('error') or 'no call'})"
        print(f"  Tool-Call : {t_str}", flush=True)

        benchmark_data[m] = {
            "ping_ms": ping_results[m]["ping_ms"],
            "reasoning": r_res,
            "coding": c_res,
            "tools": t_res
        }

    # 3. Determine best models per category
    print("\n" + "=" * 80, flush=True)
    print("  ANALYSIS & MODEL SELECTION FOR BR-JARVIS", flush=True)
    print("=" * 80, flush=True)

    # Ultra-Fast / Low Latency
    fast_candidates = sorted(online_models, key=lambda x: benchmark_data[x]["ping_ms"])
    best_fast = fast_candidates[0] if fast_candidates else "auto/fast"
    print(f"  Best Ultra-Fast / Low Latency : {best_fast} ({benchmark_data.get(best_fast, {}).get('ping_ms')}ms)", flush=True)

    # Coding
    coding_candidates = [m for m in online_models if benchmark_data[m]["coding"]["passed"]]
    if coding_candidates:
        # Prefer auto/best-coding or kr/claude-sonnet-4.5 or antigravity/claude-sonnet-4-6 if passed
        preferred_coding = ["auto/best-coding", "auto/coding", "kr/claude-sonnet-4.5", "antigravity/claude-sonnet-4-6"]
        best_coding = next((p for p in preferred_coding if p in coding_candidates), coding_candidates[0])
    else:
        best_coding = "auto/coding"
    print(f"  Best Coding Model             : {best_coding}", flush=True)

    # Reasoning
    reasoning_candidates = [m for m in online_models if benchmark_data[m]["reasoning"]["passed"]]
    if reasoning_candidates:
        preferred_reasoning = ["auto/best-reasoning", "auto/pro-reasoning", "auto/reasoning", "kr/claude-sonnet-4.5", "antigravity/claude-opus-4-6-thinking"]
        best_reasoning = next((p for p in preferred_reasoning if p in reasoning_candidates), reasoning_candidates[0])
    else:
        best_reasoning = "auto/reasoning"
    print(f"  Best Reasoning Model          : {best_reasoning}", flush=True)

    # Tool calling / Agent
    agent_candidates = [m for m in online_models if benchmark_data[m]["tools"]["passed"]]
    if agent_candidates:
        preferred_agent = ["antigravity/gemini-3.7-flash-high", "antigravity/gemini-pro-agent", "auto/chat", "github/gpt-4o-mini"]
        best_agent = next((p for p in preferred_agent if p in agent_candidates), agent_candidates[0])
    else:
        best_agent = best_fast
    print(f"  Best Agent / Tool Call Model  : {best_agent}", flush=True)

    # General Chat
    chat_candidates = [m for m in online_models if benchmark_data[m]["coding"]["passed"] and benchmark_data[m]["reasoning"]["passed"]]
    if chat_candidates:
        preferred_chat = ["auto/best-chat", "auto/chat", "antigravity/gemini-3.7-flash-high", "github/gpt-4o-mini"]
        best_chat = next((p for p in preferred_chat if p in chat_candidates), chat_candidates[0])
    else:
        best_chat = "auto/chat"
    print(f"  Best General Chat Model       : {best_chat}", flush=True)

    # Vision
    vision_candidates = [m for m in online_models if "vision" in m or "image" in m]
    best_vision = vision_candidates[0] if vision_candidates else "auto/best-vision"
    print(f"  Best Vision Model             : {best_vision}", flush=True)

    final_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "base_url": BASE_URL,
        "total_tested": len(MODES_TO_TEST),
        "online_count": len(online_models),
        "online_models": online_models,
        "best_selection": {
            "chat": best_chat,
            "fast_chat": best_fast,
            "ultra_fast": best_fast,
            "reasoning": best_reasoning,
            "deep_reasoning": best_reasoning,
            "code": best_coding,
            "agent": best_agent,
            "planning": best_agent,
            "pro_agent": best_agent,
            "vision": best_vision,
            "summarization": best_chat,
            "voice_live": best_fast,
            "fallback": best_fast,
        },
        "details": benchmark_data
    }

    out_file = Path("workspace/omnirouter_benchmark_report.json")
    out_file.parent.mkdir(exist_ok=True)
    out_file.write_text(json.dumps(final_report, indent=2), encoding="utf-8")
    print(f"\nReport saved to: {out_file}", flush=True)
    print("=" * 80, flush=True)

if __name__ == "__main__":
    main()
