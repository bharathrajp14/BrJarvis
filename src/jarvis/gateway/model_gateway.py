"""Single provider-neutral gateway entrypoint with telemetry, cascade protection, and fault injection."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any, BinaryIO

from .contracts import Message, ModelRequest, ModelResponse, ProviderAdapter, ToolDefinition
from .errors import GatewayError, NoRouteAvailableError
from .observability import ProviderTelemetryEvent, get_telemetry_emitter
from .quota import ProviderStatus
from .routing import Capability, RouteDecision, RoutePolicy, Router


class ModelGateway:
    """Route every model and capability request through normalized providers with telemetry and cascade protection."""

    def __init__(
        self,
        adapters: Mapping[str, ProviderAdapter],
        *,
        policies: Iterable[RoutePolicy] = (),
        router: Router | None = None,
        max_fallback_depth: int = 3,
    ) -> None:
        self.adapters = dict(adapters)
        self.policies = {policy.name: policy for policy in policies}
        if "default" not in self.policies:
            self.policies["default"] = RoutePolicy(name="default", providers=tuple(self.adapters))
        self.router = router or Router()
        self.max_fallback_depth = max(1, max_fallback_depth)
        self._telemetry = get_telemetry_emitter()
        self._injected_faults: dict[str, Exception] = {}

    def inject_fault(self, provider: str, error: Exception | None = None) -> None:
        """Inject a simulated failure into a provider to test fallback chains."""
        self._injected_faults[provider] = error or RuntimeError(f"Simulated fault injection for '{provider}'")

    def clear_injected_faults(self) -> None:
        """Clear all simulated fault injections."""
        self._injected_faults.clear()

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
        adapters: Mapping[str, ProviderAdapter],
        *,
        router: Router | None = None,
    ) -> "ModelGateway":
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
                        strategy=str(raw.get("strategy", "score")).lower(),
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
        self,
        *,
        model: str | None = None,
        capability: str | Capability | None = None,
        policy: str = "default",
        visited_providers: set[str] | None = None,
        free_only: bool | None = None,
        privacy_required: bool | None = None,
    ) -> RouteDecision:
        cap_str = capability.value if isinstance(capability, Capability) else capability
        route_policy = self.policies.get(policy) or self.policies.get("default")
        if (policy == "default" or policy not in self.policies) and cap_str and cap_str in self.policies:
            route_policy = self.policies[cap_str]
        if route_policy is None:
            raise NoRouteAvailableError(f"Gateway policy '{policy}' is not configured")
        return self.router.choose(
            self.adapters,
            policy=route_policy,
            model=model,
            capability=cap_str,
            visited_providers=visited_providers,
            free_only=free_only,
            privacy_required=privacy_required,
        )

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
        meta = dict(metadata or {})
        run_id = meta.get("run_id", f"run_{uuid.uuid4().hex[:8]}")
        task_id = meta.get("task_id", "task_main")
        free_only = meta.get("free_only")
        privacy_required = meta.get("privacy") == "private"

        request = ModelRequest.from_values(
            messages,
            model=model,
            system=system,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            metadata=meta,
        )

        visited: set[str] = set()
        fallback_depth = 0
        last_error: Exception | None = None

        while fallback_depth <= self.max_fallback_depth:
            try:
                decision = self.route(
                    model=model,
                    capability=cap_str,
                    policy=policy,
                    visited_providers=visited,
                    free_only=free_only,
                    privacy_required=privacy_required,
                )
            except NoRouteAvailableError as e:
                if last_error is not None:
                    raise GatewayError(f"All gateway providers exhausted after {fallback_depth} attempt(s)") from last_error
                raise e

            provider = decision.selected_provider
            adapter = self.adapters[provider]
            target_model = decision.model if model is None else model
            visited.add(provider)
            start_mono = time.monotonic()
            start_wall = time.time()

            try:
                if provider in self._injected_faults:
                    raise self._injected_faults[provider]

                response = adapter.generate(request.with_model(target_model))
                dur = time.monotonic() - start_mono
                tokens = sum(response.usage.values()) if response.usage else 0

                self.router.record_success(provider, tokens=tokens, latency_sec=dur)
                self._record_telemetry(run_id, task_id, provider, target_model, cap_str or "text", start_wall, dur, "success", fallback_depth, tokens=tokens)
                return response

            except Exception as exc:
                dur = time.monotonic() - start_mono
                last_error = exc
                self.router.record_failure(provider, exc)
                self._record_telemetry(run_id, task_id, provider, target_model, cap_str or "text", start_wall, dur, "failure", fallback_depth, error=exc)
                fallback_depth += 1

        raise GatewayError(f"All gateway providers failed after {fallback_depth} attempt(s)") from last_error

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
        meta = dict(metadata or {})
        run_id = meta.get("run_id", f"run_{uuid.uuid4().hex[:8]}")
        task_id = meta.get("task_id", "task_main")
        free_only = meta.get("free_only")
        privacy_required = meta.get("privacy") == "private"

        request = ModelRequest.from_values(
            messages,
            model=model,
            system=system,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            metadata=meta,
        )

        visited: set[str] = set()
        fallback_depth = 0
        last_error: Exception | None = None

        while fallback_depth <= self.max_fallback_depth:
            try:
                decision = self.route(
                    model=model,
                    capability=cap_str,
                    policy=policy,
                    visited_providers=visited,
                    free_only=free_only,
                    privacy_required=privacy_required,
                )
            except NoRouteAvailableError as e:
                if last_error is not None:
                    raise GatewayError(f"All gateway streaming providers exhausted after {fallback_depth} attempt(s)") from last_error
                raise e

            provider = decision.selected_provider
            adapter = self.adapters[provider]
            target_model = decision.model if model is None else model
            visited.add(provider)
            start_mono = time.monotonic()
            start_wall = time.time()

            try:
                if provider in self._injected_faults:
                    raise self._injected_faults[provider]

                for chunk in adapter.stream(request.with_model(target_model)):
                    yield chunk

                dur = time.monotonic() - start_mono
                self.router.record_success(provider, latency_sec=dur)
                self._record_telemetry(run_id, task_id, provider, target_model, cap_str or "stream", start_wall, dur, "success", fallback_depth)
                return

            except Exception as exc:
                dur = time.monotonic() - start_mono
                last_error = exc
                self.router.record_failure(provider, exc)
                self._record_telemetry(run_id, task_id, provider, target_model, cap_str or "stream", start_wall, dur, "failure", fallback_depth, error=exc)
                fallback_depth += 1

        raise GatewayError(f"All gateway streaming providers failed after {fallback_depth} attempt(s)") from last_error

    def _execute_capability(
        self,
        capability: Capability,
        method_name: str,
        meta: dict[str, Any],
        invoker: Any,
        model_override: str | None = None,
    ) -> Any:
        run_id = meta.get("run_id", f"run_{uuid.uuid4().hex[:8]}")
        task_id = meta.get("task_id", f"task_{capability.value}")
        policy_name = capability.value
        visited: set[str] = set()
        fallback_depth = 0
        last_error: Exception | None = None

        while fallback_depth <= self.max_fallback_depth:
            try:
                decision = self.route(capability=capability, policy=policy_name, visited_providers=visited)
            except NoRouteAvailableError:
                break

            provider = decision.selected_provider
            visited.add(provider)
            adapter = self.adapters[provider]
            target_model = model_override or decision.model
            start_mono = time.monotonic()
            start_wall = time.time()

            if hasattr(adapter, method_name):
                try:
                    if provider in self._injected_faults:
                        raise self._injected_faults[provider]

                    result = invoker(adapter, target_model)
                    dur = time.monotonic() - start_mono
                    cache_hit = getattr(result, "cached", False)
                    audio_sec = getattr(result, "duration_seconds", 0.0)

                    self.router.record_success(provider, audio_seconds=audio_sec, latency_sec=dur)
                    self._record_telemetry(run_id, task_id, provider, target_model, capability.value, start_wall, dur, "success", fallback_depth, cache_hit=cache_hit)
                    return result

                except Exception as exc:
                    dur = time.monotonic() - start_mono
                    last_error = exc
                    self.router.record_failure(provider, exc)
                    self._record_telemetry(run_id, task_id, provider, target_model, capability.value, start_wall, dur, "failure", fallback_depth, error=exc)
                    fallback_depth += 1

        raise GatewayError(f"All {capability.value} providers failed after {fallback_depth} attempt(s)") from last_error

    def transcribe(
        self,
        audio_source: str | Path | bytes | BinaryIO,
        *,
        model: str | None = None,
        language: str | None = None,
        prompt: str | None = None,
        timestamps: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._execute_capability(
            Capability.SPEECH_TO_TEXT,
            "transcribe",
            dict(metadata or {}),
            lambda ad, tm: ad.transcribe(audio_source, model=tm, language=language, prompt=prompt, timestamps=timestamps),
            model_override=model,
        )

    def synthesize_speech(
        self,
        text: str,
        *,
        model: str | None = None,
        voice: str | None = None,
        use_cache: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        return self._execute_capability(
            Capability.TEXT_TO_SPEECH,
            "synthesize_speech",
            dict(metadata or {}),
            lambda ad, tm: ad.synthesize_speech(text, model=tm, voice=voice, use_cache=use_cache),
            model_override=model,
        )

    def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        width: int = 1024,
        height: int = 1024,
        aspect_ratio: str | None = None,
        seed: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        return self._execute_capability(
            Capability.IMAGE_GENERATION,
            "generate_image",
            dict(metadata or {}),
            lambda ad, tm: ad.generate_image(prompt, model=tm, width=width, height=height, aspect_ratio=aspect_ratio, seed=seed),
            model_override=model,
        )

    def _record_telemetry(
        self,
        run_id: str,
        task_id: str,
        provider: str,
        model: str,
        capability: str,
        start_time: float,
        duration_sec: float,
        status: str,
        fallback_depth: int,
        tokens: int | None = None,
        cache_hit: bool = False,
        error: Exception | None = None,
    ) -> None:
        self._telemetry.record(
            ProviderTelemetryEvent(
                run_id=run_id,
                task_id=task_id,
                provider=provider,
                model=model,
                capability=capability,
                start_time=start_time,
                duration_sec=duration_sec,
                status=status,
                fallback=(fallback_depth > 0),
                fallback_depth=fallback_depth,
                tokens=tokens,
                cache_hit=cache_hit,
                error_class=error.__class__.__name__ if error else None,
                error_message=str(error)[:200] if error else None,
            )
        )

    def reset_circuits(self) -> None:
        """Reset all circuit breakers and temporary degradation cooldowns."""
        self.clear_injected_faults()
        quota_mgr = getattr(self.router, "_quota_manager", None)
        for provider in self.adapters:
            state = self.router.state(provider)
            state.opened_until = 0.0
            state.failures = 0
            state.last_error = None
            if quota_mgr is not None:
                metrics = quota_mgr.get_metrics(provider)
                metrics.cooldown_until = 0.0
                metrics.consecutive_failures = 0
                if metrics.status in (ProviderStatus.OPEN_CIRCUIT, ProviderStatus.DEGRADED, ProviderStatus.RATE_LIMITED):
                    metrics.status = ProviderStatus.HEALTHY

    def status(self) -> dict[str, Any]:
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
            "telemetry_recent": self._telemetry.get_recent(limit=10),
        }


__all__ = ["ModelGateway"]
