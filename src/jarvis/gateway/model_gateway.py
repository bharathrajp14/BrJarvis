"""Single provider-neutral gateway entrypoint for the rebuilt runtime."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any, BinaryIO

from .contracts import Message, ModelRequest, ModelResponse, ProviderAdapter, ToolDefinition
from .errors import GatewayError, NoRouteAvailableError
from .routing import Capability, RouteDecision, RoutePolicy, Router


class ModelGateway:
    """Route every model and capability request through one adapter registry and one failover path."""

    def __init__(
        self,
        adapters: Mapping[str, ProviderAdapter],
        *,
        policies: Iterable[RoutePolicy] = (),
        router: Router | None = None,
    ) -> None:
        self.adapters = dict(adapters)
        self.policies = {policy.name: policy for policy in policies}
        if "default" not in self.policies:
            self.policies["default"] = RoutePolicy(name="default", providers=tuple(self.adapters))
        self.router = router or Router()

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
        adapters: Mapping[str, ProviderAdapter],
        *,
        router: Router | None = None,
    ) -> "ModelGateway":
        """Build routing policy from normalized YAML/JSON configuration."""
        routing = data.get("routing", data)
        policies_data = routing.get("policies", routing.get("routes", {}))
        policies: list[RoutePolicy] = []
        if isinstance(policies_data, Mapping):
            for name, raw in policies_data.items():
                if not isinstance(raw, Mapping):
                    continue
                policies.append(
                    RoutePolicy(
                        name=str(name),
                        strategy=str(raw.get("strategy", "priority")).lower(),
                        providers=tuple(str(item) for item in raw.get("providers", raw.get("backends", []))),
                        required_capabilities=frozenset(
                            str(item).lower() for item in raw.get("required_capabilities", [])
                        ),
                        max_fallbacks=max(0, int(raw.get("max_fallbacks", 3))),
                    )
                )
        if not policies:
            fallback = routing.get("fallback_hierarchy", [])
            providers = tuple(str(item) for item in fallback if str(item) in adapters) or tuple(adapters)
            policies.append(RoutePolicy(name="default", providers=providers))
        cooldown = float(data.get("cooldown_seconds", routing.get("cooldown_seconds", 15.0)))
        resolved_router = router or Router(cooldown_seconds=cooldown)
        return cls(adapters, policies=policies, router=resolved_router)

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        adapters: Mapping[str, ProviderAdapter],
        *,
        router: Router | None = None,
    ) -> "ModelGateway":
        source = Path(path)
        raw = source.read_text(encoding="utf-8")
        if source.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            import yaml

            data = yaml.safe_load(raw) or {}
        if not isinstance(data, Mapping):
            raise ValueError("Gateway configuration root must be a mapping")
        return cls.from_mapping(data, adapters, router=router)

    def route(
        self, *, model: str | None = None, capability: str | Capability | None = None, policy: str = "default"
    ) -> RouteDecision:
        cap_str = capability.value if isinstance(capability, Capability) else capability
        route_policy = self.policies.get(policy) or self.policies.get("default")
        if (policy == "default" or policy not in self.policies) and cap_str and cap_str in self.policies:
            route_policy = self.policies[cap_str]
        if route_policy is None:
            raise NoRouteAvailableError(f"Gateway policy '{policy}' is not configured")
        return self.router.choose(self.adapters, policy=route_policy, model=model, capability=cap_str)

    def generate(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        system: str | None = None,
        tools: list[ToolDefinition] | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        capability: str | Capability | None = None,
        policy: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> ModelResponse:
        cap_str = capability.value if isinstance(capability, Capability) else capability
        request = ModelRequest.from_values(
            messages,
            model=model,
            system=system,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            metadata=metadata,
        )
        decision = self.route(model=model, capability=cap_str, policy=policy)
        last_error: Exception | None = None
        for provider in decision.candidates:
            adapter = self.adapters[provider]
            try:
                response = adapter.generate(request.with_model(decision.model if model is None else model))
                self.router.record_success(provider)
                return response
            except Exception as exc:
                last_error = exc
                self.router.record_failure(provider, exc)
        raise GatewayError(f"All gateway providers failed after {len(decision.candidates)} attempt(s)") from last_error

    def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        system: str | None = None,
        tools: list[ToolDefinition] | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        capability: str | Capability | None = None,
        policy: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[str]:
        cap_str = capability.value if isinstance(capability, Capability) else capability
        request = ModelRequest.from_values(
            messages,
            model=model,
            system=system,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            metadata=metadata,
        )
        decision = self.route(model=model, capability=cap_str, policy=policy)
        last_error: Exception | None = None
        for provider in decision.candidates:
            adapter = self.adapters[provider]
            emitted = False
            try:
                for chunk in adapter.stream(request.with_model(decision.model if model is None else model)):
                    emitted = True
                    yield chunk
                self.router.record_success(provider)
                return
            except Exception as exc:
                last_error = exc
                self.router.record_failure(provider, exc)
                if emitted:
                    continue
        raise GatewayError(f"All gateway providers failed after {len(decision.candidates)} attempt(s)") from last_error

    def transcribe(
        self,
        audio_source: str | Path | bytes | BinaryIO,
        *,
        model: str | None = None,
        language: str | None = None,
        prompt: str | None = None,
        timestamps: bool = False,
    ) -> dict[str, Any]:
        """Execute speech-to-text with automatic fallback across eligible STT adapters."""
        decision = self.route(capability=Capability.SPEECH_TO_TEXT, policy="speech_to_text")
        last_error: Exception | None = None
        for provider in decision.candidates:
            adapter = self.adapters[provider]
            if hasattr(adapter, "transcribe"):
                try:
                    result = adapter.transcribe(
                        audio_source,
                        model=model or decision.model,
                        language=language,
                        prompt=prompt,
                        timestamps=timestamps,
                    )
                    self.router.record_success(provider)
                    return result
                except Exception as exc:
                    last_error = exc
                    self.router.record_failure(provider, exc)
        raise GatewayError("All speech-to-text providers failed") from last_error

    def synthesize_speech(
        self,
        text: str,
        *,
        model: str | None = None,
        voice: str | None = None,
        use_cache: bool = True,
    ) -> Any:
        """Execute text-to-speech with automatic fallback across eligible TTS adapters."""
        decision = self.route(capability=Capability.TEXT_TO_SPEECH, policy="text_to_speech")
        last_error: Exception | None = None
        for provider in decision.candidates:
            adapter = self.adapters[provider]
            if hasattr(adapter, "synthesize_speech"):
                try:
                    result = adapter.synthesize_speech(
                        text,
                        model=model or decision.model,
                        voice=voice,
                        use_cache=use_cache,
                    )
                    self.router.record_success(provider)
                    return result
                except Exception as exc:
                    last_error = exc
                    self.router.record_failure(provider, exc)
        raise GatewayError("All text-to-speech providers failed") from last_error

    def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        width: int = 1024,
        height: int = 1024,
        aspect_ratio: str | None = None,
        seed: int | None = None,
    ) -> Any:
        """Execute image generation with automatic fallback across eligible image adapters."""
        decision = self.route(capability=Capability.IMAGE_GENERATION, policy="image_generation")
        last_error: Exception | None = None
        for provider in decision.candidates:
            adapter = self.adapters[provider]
            if hasattr(adapter, "generate_image"):
                try:
                    result = adapter.generate_image(
                        prompt,
                        model=model or decision.model,
                        width=width,
                        height=height,
                        aspect_ratio=aspect_ratio,
                        seed=seed,
                    )
                    self.router.record_success(provider)
                    return result
                except Exception as exc:
                    last_error = exc
                    self.router.record_failure(provider, exc)
        raise GatewayError("All image generation providers failed") from last_error

    def status(self) -> dict[str, Any]:
        """Return safe provider and circuit state without credentials."""
        return {
            "providers": {
                name: {
                    "provider": adapter.provider,
                    "available": adapter.available,
                    "default_model": adapter.default_model,
                    "capabilities": sorted(adapter.capabilities),
                }
                for name, adapter in self.adapters.items()
            },
            "circuits": self.router.status(),
        }


__all__ = ["ModelGateway"]
