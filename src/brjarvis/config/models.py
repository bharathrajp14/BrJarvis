# src/brjarvis/config/models.py — BR JARVIS Central Model Configuration (Proxy-Brain & Gemini-First)
"""Central model configuration. Loads from config/models.yaml, models.json, and environment variables."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from brjarvis.core.paths import paths

logger = logging.getLogger(__name__)

_CONFIG_DIR = paths.CONFIG_ROOT
_MODELS_YAML = _CONFIG_DIR / "models.yaml"
_MODELS_JSON = _CONFIG_DIR / "models.json"

# ── Defaults (Calibrated from Live OmniRouter Benchmark on http://127.0.0.1:20128/v1) ───
_DEFAULTS = {
    "voice_live": "antigravity/gemini-3.7-flash-high",
    "voice_name": "Charon",
    "gemini": "antigravity/gemini-3.7-flash-high",
    "gemini_code": "antigravity/claude-sonnet-4-6",
    "gemini_reasoning": "antigravity/claude-opus-4-6-thinking",
    "gemini_general": "antigravity/gemini-3.7-flash-high",
    "gemini_agent": "antigravity/gemini-3.7-flash-high",
    "gemini_pro_agent": "antigravity/gemini-3.7-flash-high",
    "gemini_fast": "antigravity/gemini-3.1-flash-lite",
    "gemini_vision": "antigravity/gemini-3.7-flash-high",
    "gemini_lite": "antigravity/gemini-3.1-flash-lite",
    "claude": "antigravity/claude-sonnet-4-6",
    "claude_opus": "antigravity/claude-opus-4-6-thinking",
    "gpt": "antigravity/gemini-3.7-flash-high",
    "gpt_mini": "antigravity/gemini-3.1-flash-lite",
    "gpt_4o": "antigravity/gemini-3.7-flash-high",
    "ollama": "llama3.3",
    "nvidia": "meta/llama-3.1-70b-instruct",
    "mistral": "mistral-large-latest",
    "default_backend": "gpt",
    "disable_gemini": True,
    "planner_model": "antigravity/gemini-3.7-flash-high",
    "fast_model": "antigravity/gemini-3.1-flash-lite",
    "proxy_base_url": "http://127.0.0.1:20128/v1",
    "proxy_api_key": "",
    "openai_base_url": "http://127.0.0.1:20128/v1",
    "openai_api_key": "",
    "openai_model": "antigravity/gemini-3.7-flash-high",
}

_ENV_MAP = {
    "BRJARVIS_PROXY_BASE_URL": "proxy_base_url",
    "OPENAI_BASE_URL": "openai_base_url",
    "BRJARVIS_PROXY_API_KEY": "proxy_api_key",
    "BRJARVIS_DEFAULT_MODEL": "gemini_general",
    "JARVIS_MODEL_GEMINI": "gemini",
    "JARVIS_MODEL_CLAUDE": "claude",
    "JARVIS_MODEL_GPT": "gpt",
    "JARVIS_MODEL_OLLAMA": "ollama",
    "JARVIS_MODEL_NVIDIA": "nvidia",
    "JARVIS_MODEL_MISTRAL": "mistral",
    "JARVIS_MODEL_VOICE": "voice_live",
    "JARVIS_VOICE_NAME": "voice_name",
    "JARVIS_DEFAULT_BACKEND": "default_backend",
    "OPENAI_MODEL": "openai_model",
}

_cache: dict | None = None


def get_model_config(force_reload: bool = False) -> dict[str, Any]:
    """Retrieve merged model configuration."""
    global _cache
    if _cache is not None and not force_reload:
        return _cache.copy()

    config = dict(_DEFAULTS)

    # 1. Load models.json if present
    if _MODELS_JSON.exists():
        try:
            data = json.loads(_MODELS_JSON.read_text(encoding="utf-8"))
            for k, v in data.items():
                if not k.startswith("_") and isinstance(v, str) and v.strip():
                    config[k] = v.strip()
        except Exception as e:
            logger.debug("Warning reading models.json: %s", e)

    # 2. Load models.yaml if present and yaml is installed
    if _MODELS_YAML.exists():
        try:
            import yaml

            ydata = yaml.safe_load(_MODELS_YAML.read_text(encoding="utf-8"))
            if isinstance(ydata, dict):
                proxy_cfg = ydata.get("proxy", {})
                if proxy_cfg.get("base_url"):
                    config["proxy_base_url"] = str(proxy_cfg["base_url"]).strip()
                    config["openai_base_url"] = str(proxy_cfg["base_url"]).strip()
                routing = ydata.get("routing", {})
                if routing.get("default_model"):
                    config["gemini"] = str(routing["default_model"]).strip()
                    config["gemini_general"] = str(routing["default_model"]).strip()
                caps = routing.get("capabilities", {})
                if caps.get("reasoning"):
                    config["gemini_reasoning"] = str(caps["reasoning"]).strip()
                if caps.get("code"):
                    config["gemini_code"] = str(caps["code"]).strip()
                if caps.get("agent"):
                    config["gemini_agent"] = str(caps["agent"]).strip()
                if caps.get("vision"):
                    config["gemini_vision"] = str(caps["vision"]).strip()
                if caps.get("fast_chat"):
                    config["gemini_fast"] = str(caps["fast_chat"]).strip()
        except ImportError:
            pass
        except Exception as exc:
            logger.debug("Notice parsing models.yaml: %s", exc)

    # 3. ENV overrides (highest priority)
    for env_key, cfg_key in _ENV_MAP.items():
        val = os.environ.get(env_key, "").strip()
        if val:
            config[cfg_key] = val

    if config.get("default_backend") not in ("gemini", "claude", "gpt", "ollama", "nvidia", "mistral"):
        config["default_backend"] = "gemini"

    _cache = config
    return config.copy()


def clear_model_config_cache():
    """Clear cached model configuration."""
    global _cache
    _cache = None


def get_model(backend: str) -> str:
    """Get the active model ID for a backend or task."""
    return get_model_config().get(backend, _DEFAULTS.get(backend, ""))


def get_model_for_task(task_type: str | None = None, messages: list[dict] | None = None, system: str = "") -> str:
    """Intelligently select the best model ID for a given task type."""
    cfg = get_model_config()
    task = (task_type or "general").lower()

    if task in ("code", "coding", "architecture", "refactor", "debug"):
        return cfg.get("gemini_code", "gemini-3-flash-agent")
    elif task in ("reasoning", "math", "logic", "audit", "security"):
        return cfg.get("gemini_reasoning", "gemini-3-flash-agent")
    elif task in ("agent", "planner", "workflow", "dag", "multi_step"):
        return cfg.get("gemini_agent", "gemini-3-flash-agent")
    elif task in ("vision", "ocr", "screen", "image", "ui_scan"):
        return cfg.get("gemini_vision", "gemini-3.1-flash-image")
    elif task in ("fast", "status", "quick", "summary", "log"):
        return cfg.get("gemini_fast", "gemini-3.5-flash-low")
    elif task in ("lite", "autocomplete", "prefix", "token"):
        return cfg.get("gemini_lite", "gemini-3.5-flash-extra-low")
    else:
        return cfg.get("gemini_general", "gemini-3-flash-agent")
