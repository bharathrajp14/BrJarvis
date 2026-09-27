import os
import time
import openai

client = openai.OpenAI(
    base_url=os.environ.get("OMNIROUTER_BASE_URL", "http://localhost:20128/v1"),
    api_key=os.environ.get("OMNIROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY") or "sk-local-omnirouter",
    timeout=45.0
)

models_to_test = [
    "antigravity/gemini-3.7-flash-high",
    "cl/google/gemini-3.8-flash",
    "kr/claude-sonnet-4.5",
    "auto/chat",
    "auto/best-fast",
    "auto/coding",
    "github/gpt-4o-mini"
]

for m in models_to_test:
    print(f"Testing {m}...", flush=True)
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Reply with 'OK'"}],
            max_tokens=10
        )
        dt = (time.perf_counter() - t0) * 1000
        content = resp.choices[0].message.content
        print(f"  [SUCCESS] {m} in {dt:.0f}ms -> {content!r}", flush=True)
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000
        print(f"  [ERROR] {m} in {dt:.0f}ms: {e}", flush=True)
