"""Build the multi-provider autonomous gateway with real adapters and capability routing."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from .adapters import (
    ElevenLabsAdapter,
    GeminiAudioAdapter,
    GroqSTTAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
    PollinationsAdapter,
)
from .contracts import ProviderAdapter
from .model_gateway import ModelGateway
from .quota import get_quota_manager
from .routing import RoutePolicy, Router, build_canonical_policies


def _read_env_val(key: str, env_dict: dict[str, str]) -> str:
    return os.environ.get(key) or env_dict.get(key, "")


def _load_env_dict(root_dir: Path) -> dict[str, str]:
    env_file = root_dir / ".env"
    out: dict[str, str] = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def build_configured_gateway(config_path: str | Path | None = None) -> ModelGateway:
    """Load configuration and instantiate all local and external provider adapters."""
    root_dir = Path(__file__).resolve().parents[3]
    source = Path(config_path or root_dir / "config" / "models.yaml")
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    env_map = _load_env_dict(root_dir)

    proxy = data.get("proxy", {})
    routing = data.get("routing", {})
    base_url = str(proxy.get("base_url", "http://localhost:8045/v1"))
    api_key_env = str(proxy.get("api_key_env", "BRJARVIS_PROXY_API_KEY"))
    proxy_api_key = (
        os.environ.get(api_key_env)
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("BRJARVIS_PROXY_API_KEY")
        or env_map.get(api_key_env, "")
        or env_map.get("BRJARVIS_PROXY_API_KEY", "")
        or env_map.get("OPENAI_API_KEY", "")
    )

    hierarchy = tuple(str(model) for model in routing.get("fallback_hierarchy", []))
    default_model = str(routing.get("default_model", hierarchy[0] if hierarchy else "gemini-3.1-pro-high"))
    model_ids = tuple(dict.fromkeys((default_model, *hierarchy)))
    capabilities_cfg = routing.get("capabilities", {})

    quota_mgr = get_quota_manager()
    adapters: dict[str, ProviderAdapter] = {}

    # 1. Primary Intelligence Gateway: Local Proxy models
    all_proxy_models = frozenset(model_ids)
    adapters["proxy"] = OpenAIAdapter(
        provider="proxy",
        model=default_model,
        api_key=proxy_api_key,
        base_url=base_url,
        models=all_proxy_models,
        capabilities=frozenset({"chat", "code", "reasoning", "vision", "image", "image_understanding"}),
    )
    for model_id in model_ids:
        adapters[model_id] = OpenAIAdapter(
            provider="proxy",
            model=model_id,
            api_key=proxy_api_key,
            base_url=base_url,
            models=frozenset({model_id}),
            capabilities=frozenset({"chat", "code", "reasoning", "vision", "image", "image_understanding"}),
        )

    # 2. Provider A: Groq STT
    groq_key = _read_env_val("GROQ_API_KEY", env_map)
    adapters["groq"] = GroqSTTAdapter(api_key=groq_key, quota_manager=quota_mgr)

    # 3. Provider B: Dedicated Gemini Native Audio (TTS & Voice)
    gemini_key = _read_env_val("GEMINI_API_KEY", env_map)
    adapters["gemini_audio"] = GeminiAudioAdapter(api_key=gemini_key, quota_manager=quota_mgr)

    # 4. Provider C: Pollinations Media & Image Generation
    pollinations_key = _read_env_val("POLLINATIONS_API_KEY", env_map)
    adapters["pollinations"] = PollinationsAdapter(api_key=pollinations_key, quota_manager=quota_mgr)

    # 5. Provider D: OpenRouter Free Reasoning / Vision Fallback
    openrouter_key = _read_env_val("OPENROUTER_API_KEY", env_map)
    adapters["openrouter"] = OpenRouterAdapter(api_key=openrouter_key, quota_manager=quota_mgr)

    # 6. Provider E: ElevenLabs Premium Voice Fallback
    elevenlabs_key = _read_env_val("ELEVENLABS_API_KEY", env_map)
    adapters["elevenlabs"] = ElevenLabsAdapter(api_key=elevenlabs_key, quota_manager=quota_mgr)

    # Build canonical capability policies
    policies: list[RoutePolicy] = [
        RoutePolicy(name="default", providers=("proxy", *model_ids)),
        *build_canonical_policies(set(adapters.keys())),
    ]

    # Overlay any specific routes from models.yaml
    if isinstance(capabilities_cfg, dict):
        for capability, model in capabilities_cfg.items():
            model_id = str(model)
            if model_id in adapters:
                policies.append(
                    RoutePolicy(
                        name=str(capability),
                        providers=(model_id,),
                        required_capabilities=frozenset({str(capability).lower()}),
                        max_fallbacks=1,
                    )
                )

    cooldown = float(data.get("cooldown_seconds", 15.0))
    router = Router(cooldown_seconds=cooldown, quota_manager=quota_mgr)
    return ModelGateway(adapters, policies=policies, router=router)


__all__ = ["build_configured_gateway"]
