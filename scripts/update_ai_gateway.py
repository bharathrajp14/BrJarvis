import yaml
from pathlib import Path

def update_ai_gateway():
    path = Path("config/ai_gateway.yaml")
    text = path.read_text(encoding="utf-8")
    
    # 1. Update base_url references from 8045 to 20128
    text = text.replace("http://localhost:8045/v1", "http://127.0.0.1:20128/v1")
    text = text.replace("https://api.omnirouter.io/v1", "http://127.0.0.1:20128/v1")
    text = text.replace("Antigravity Custom Proxy  (http://localhost:8045/v1)", "OmniRouter Local Gateway  (http://127.0.0.1:20128/v1)")

    # 2. Update model IDs to match OmniRouter names
    replacements = {
        "model: gemini-3.7-flash-high": "model: antigravity/gemini-3.7-flash-high",
        "model: gemini-3.6-flash-high": "model: antigravity/gemini-3.7-flash-high",
        "model: gemini-3.1-pro-high": "model: antigravity/gemini-pro-agent",
        "model: claude-sonnet-4-6": "model: antigravity/claude-sonnet-4-6",
        "model: claude-opus-4-6-thinking": "model: antigravity/claude-opus-4-6-thinking",
        "model: gemini-3-flash-agent": "model: antigravity/gemini-pro-agent",
        "model: gemini-3.6-flash-low": "model: antigravity/gemini-3.7-flash-low",
        "model: gemini-3.1-pro-low": "model: antigravity/gemini-3.1-pro-low",
        "model: gemini-3.5-flash-extra-low": "model: antigravity/gemini-3.1-pro-low",
        "model: gemini-3.1-flash-image": "model: auto/best-vision",
        "model: gpt-oss-120b-medium": "model: github/gpt-4o-mini",
    }
    for old_m, new_m in replacements.items():
        text = text.replace(old_m, new_m)

    # Enable omnirouter_fallback
    text = text.replace("enabled: false\n    priority: 90\n    weight: 1\n    cost_per_1k_tokens: 0\n    latency_ms: 2000\n    capabilities: [chat, code, reasoning]",
                        "enabled: true\n    priority: 85\n    weight: 1\n    cost_per_1k_tokens: 0\n    latency_ms: 1800\n    capabilities: [chat, code, reasoning]")

    # Validate yaml parses properly
    yaml.safe_load(text)
    path.write_text(text, encoding="utf-8")
    print("Successfully updated and validated config/ai_gateway.yaml")

if __name__ == "__main__":
    update_ai_gateway()
