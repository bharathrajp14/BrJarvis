"""Build the new gateway from the existing model catalogue without legacy imports."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from .adapters import OpenAIAdapter
from .model_gateway import ModelGateway
from .routing import RoutePolicy, Router


def build_configured_gateway(config_path: str | Path | None = None) -> ModelGateway:
    """Load the current YAML model catalogue into the canonical gateway.

    The current catalogue describes several models behind one OpenAI-compatible
    proxy. Each model is represented as a logical adapter so the new gateway can
    apply capability filtering and failover before provider-native adapters land.
    """
    source = Path(config_path or Path(__file__).resolve().parents[3] / "config" / "models.yaml")
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    proxy = data.get("proxy", {})
    routing = data.get("routing", {})
    base_url = str(proxy.get("base_url", "http://localhost:8045/v1"))
    api_key_env = str(proxy.get("api_key_env", "BRJARVIS_PROXY_API_KEY"))
    api_key = os.environ.get(api_key_env) or os.environ.get("OPENAI_API_KEY") or os.environ.get("BRJARVIS_PROXY_API_KEY", "")
    if not api_key:
        env_file = Path(__file__).resolve().parents[3] / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    if k.strip() in (api_key_env, "BRJARVIS_PROXY_API_KEY", "OPENAI_API_KEY") and v.strip():
                        api_key = v.strip()
                        break
    hierarchy = tuple(str(model) for model in routing.get("fallback_hierarchy", []))
    default_model = str(routing.get("default_model", hierarchy[0] if hierarchy else "gpt-4o-mini"))
    model_ids = tuple(dict.fromkeys((default_model, *hierarchy)))
    capabilities = routing.get("capabilities", {})

    adapters = {
        model_id: OpenAIAdapter(
            provider="proxy",
            model=model_id,
            api_key=api_key,
            base_url=base_url,
            models=frozenset({model_id}),
            capabilities=frozenset({"chat", "code", "reasoning", "vision", "image"}),
        )
        for model_id in model_ids
    }
    policies: list[RoutePolicy] = [
        RoutePolicy(name="default", providers=tuple(model_ids)),
    ]
    if isinstance(capabilities, dict):
        for capability, model in capabilities.items():
            model_id = str(model)
            if model_id in adapters:
                policies.append(
                    RoutePolicy(
                        name=str(capability),
                        providers=(model_id,),
                        required_capabilities=frozenset({str(capability).lower()}),
                        max_fallbacks=0,
                    )
                )
    cooldown = float(data.get("cooldown_seconds", 15.0))
    return ModelGateway(adapters, policies=policies, router=Router(cooldown_seconds=cooldown))


__all__ = ["build_configured_gateway"]
