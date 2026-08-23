"""Configurable AI backend pool and gateway routing for Br-Jarvis.

This module intentionally keeps routing policy separate from provider SDKs. A
backend only needs to implement the existing ``BaseBackend`` contract; the
router handles policy selection, health-aware fallback, and configuration.

The design is inspired by OmniRouter's one-endpoint/provider-pool model, while
remaining local-first and dependency-light for Br-Jarvis.
"""

from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

logger = logging.getLogger("JARVIS.AIGatewayRouter")


@dataclass(frozen=True)
class BackendConfig:
    """Operational metadata for one configured backend connection."""

    id: str
    provider: str
    model: str
    base_url: str = ""
    api_key_env: str = ""
    enabled: bool = True
    priority: int = 100
    weight: int = 1
    cost_per_1k_tokens: float = 0.0
    latency_ms: float = 500.0
    capabilities: frozenset[str] = frozenset({"chat"})
    max_context: int = 128_000

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BackendConfig":
        backend_id = str(data.get("id", "")).strip()
        if not backend_id:
            raise ValueError("Each AI backend must have a non-empty id")
        return cls(
            id=backend_id,
            provider=str(data.get("provider", backend_id)).strip(),
            model=str(data.get("model", "")).strip(),
            base_url=str(data.get("base_url", "")).strip(),
            api_key_env=str(data.get("api_key_env", "")).strip(),
            enabled=bool(data.get("enabled", True)),
            priority=int(data.get("priority", 100)),
            weight=max(1, int(data.get("weight", 1))),
            cost_per_1k_tokens=max(0.0, float(data.get("cost_per_1k_tokens", 0.0))),
            latency_ms=max(1.0, float(data.get("latency_ms", 500.0))),
            capabilities=frozenset(str(v).lower() for v in data.get("capabilities", ["chat"])),
            max_context=max(1, int(data.get("max_context", 128_000))),
        )

    @property
    def has_credentials(self) -> bool:
        """Whether the configured credential env var is present, if one is required."""
        return not self.api_key_env or bool(os.getenv(self.api_key_env, "").strip())


@dataclass(frozen=True)
class RoutePolicy:
    """A named policy describing how eligible backends are ordered."""

    name: str
    strategy: str = "priority"
    backends: tuple[str, ...] = ()
    required_capabilities: frozenset[str] = frozenset()
    max_fallbacks: int = 3

    @classmethod
    def from_dict(cls, name: str, data: Mapping[str, Any]) -> "RoutePolicy":
        return cls(
            name=name,
            strategy=str(data.get("strategy", "priority")).lower(),
            backends=tuple(str(v) for v in data.get("backends", [])),
            required_capabilities=frozenset(str(v).lower() for v in data.get("required_capabilities", [])),
            max_fallbacks=max(0, int(data.get("max_fallbacks", 3))),
        )


@dataclass(frozen=True)
class RouteDecision:
    """Explainable routing result returned before execution."""

    policy: str
    selected_backend: str
    candidates: tuple[str, ...]
    reason: str


@dataclass
class BackendStats:
    """Small in-memory health signal used by adaptive routing."""

    successes: int = 0
    failures: int = 0
    last_latency_ms: float | None = None
    cooldown_until: float = 0.0

    @property
    def available(self) -> bool:
        return time.monotonic() >= self.cooldown_until


@dataclass(frozen=True)
class GatewayResponse:
    """Completion output plus routing provenance."""

    text: str
    backend_id: str
    model: str
    attempts: tuple[str, ...]


class AIGatewayRouter:
    """Route requests across configured backend instances with safe fallback.

    ``backend_factory`` is optional. Applications may register already-created
    ``BaseBackend`` instances, or provide a factory that receives a
    :class:`BackendConfig` and returns a compatible backend object.
    """

    def __init__(
        self,
        backend_configs: Iterable[BackendConfig] = (),
        policies: Iterable[RoutePolicy] = (),
        backend_factory: Callable[[BackendConfig], Any] | None = None,
        cooldown_seconds: float = 15.0,
    ) -> None:
        self.backends = {item.id: item for item in backend_configs}
        self.policies = {item.name: item for item in policies}
        self.instances: dict[str, Any] = {}
        self.stats = {item.id: BackendStats() for item in backend_configs}
        self.backend_factory = backend_factory
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self._lock = threading.RLock()
        self._round_robin_cursor: dict[str, int] = {}

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
        backend_factory: Callable[[BackendConfig], Any] | None = None,
    ) -> "AIGatewayRouter":
        configs = [BackendConfig.from_dict(item) for item in data.get("backends", [])]
        policies = [RoutePolicy.from_dict(name, value) for name, value in data.get("routes", {}).items()]
        if "default" not in {policy.name for policy in policies}:
            policies.append(RoutePolicy(name="default", strategy="priority", backends=tuple(c.id for c in configs)))
        cooldown = os.getenv("BRJARVIS_GATEWAY_COOLDOWN_SECONDS", "").strip()
        cooldown_seconds = float(cooldown) if cooldown else float(data.get("cooldown_seconds", 15))
        return cls(configs, policies, backend_factory=backend_factory, cooldown_seconds=cooldown_seconds)

    @classmethod
    def from_file(cls, path: str | Path, backend_factory: Callable[[BackendConfig], Any] | None = None) -> "AIGatewayRouter":
        """Load JSON or YAML without requiring YAML for JSON-only deployments."""
        source = Path(path)
        raw = source.read_text(encoding="utf-8")
        if source.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            try:
                import yaml
            except ImportError as exc:
                raise RuntimeError("Install PyYAML or use a JSON gateway config") from exc
            data = yaml.safe_load(raw) or {}
        if not isinstance(data, Mapping):
            raise ValueError("Gateway config root must be a mapping")
        return cls.from_mapping(data, backend_factory=backend_factory)

    def register(self, backend_id: str, instance: Any) -> None:
        """Attach a live backend instance to a configured backend id."""
        if backend_id not in self.backends:
            raise KeyError(f"Backend '{backend_id}' is not configured")
        self.instances[backend_id] = instance

    def _eligible(self, policy: RoutePolicy, capability: str | None) -> list[BackendConfig]:
        requested = set(policy.required_capabilities)
        if capability:
            requested.add(capability.lower())
        ids = policy.backends or tuple(self.backends)
        result = []
        for backend_id in ids:
            config = self.backends.get(backend_id)
            stats = self.stats.setdefault(backend_id, BackendStats())
            if not config or not config.enabled or not config.has_credentials or not stats.available:
                continue
            if requested and not requested.issubset(config.capabilities):
                continue
            result.append(config)
        return result

    def route(self, policy_name: str = "default", capability: str | None = None) -> RouteDecision:
        """Select a backend and produce the complete ordered fallback chain."""
        policy = self.policies.get(policy_name) or self.policies.get("default")
        if not policy:
            raise LookupError("No default AI gateway route is configured")
        candidates = self._eligible(policy, capability)
        if not candidates:
            raise RuntimeError(f"No healthy backend matches route '{policy.name}'")

        strategy = policy.strategy
        if strategy == "priority":
            ordered = sorted(candidates, key=lambda item: (item.priority, item.id))
        elif strategy == "cost":
            ordered = sorted(candidates, key=lambda item: (item.cost_per_1k_tokens, item.priority, item.id))
        elif strategy == "latency":
            ordered = sorted(candidates, key=lambda item: (item.latency_ms, item.priority, item.id))
        elif strategy == "weighted":
            pool = [item for item in candidates for _ in range(item.weight)]
            random.shuffle(pool)
            ordered = []
            for item in pool:
                if item not in ordered:
                    ordered.append(item)
        elif strategy == "round_robin":
            cursor = self._round_robin_cursor.get(policy.name, 0) % len(candidates)
            ordered = candidates[cursor:] + candidates[:cursor]
            self._round_robin_cursor[policy.name] = cursor + 1
        else:
            raise ValueError(f"Unsupported gateway routing strategy: {strategy}")

        selected = ordered[0]
        ordered_ids = tuple(item.id for item in ordered[: policy.max_fallbacks + 1])
        return RouteDecision(policy.name, selected.id, ordered_ids, f"{strategy} strategy; {len(ordered_ids)} eligible backend(s)")

    def complete(
        self,
        messages: list[dict],
        system: str = "",
        tools: list | None = None,
        policy: str = "default",
        capability: str | None = None,
    ) -> GatewayResponse:
        """Complete with ordered fallback, isolating failures per backend."""
        decision = self.route(policy, capability)
        attempts: list[str] = []
        last_error: Exception | None = None
        for backend_id in decision.candidates:
            attempts.append(backend_id)
            backend = self.instances.get(backend_id)
            if backend is None and self.backend_factory:
                backend = self.backend_factory(self.backends[backend_id])
                self.instances[backend_id] = backend
            if backend is None:
                last_error = RuntimeError(f"Backend '{backend_id}' has no registered instance")
                continue
            started = time.monotonic()
            try:
                text = backend.complete(messages, system=system, tools=tools)
                elapsed = (time.monotonic() - started) * 1000
                stats = self.stats[backend_id]
                stats.successes += 1
                stats.last_latency_ms = elapsed
                return GatewayResponse(str(text), backend_id, self.backends[backend_id].model, tuple(attempts))
            except Exception as exc:  # noqa: BLE001 - fallback must isolate provider errors
                last_error = exc
                stats = self.stats[backend_id]
                stats.failures += 1
                stats.cooldown_until = time.monotonic() + self.cooldown_seconds
                logger.warning("AI backend %s failed; trying next candidate: %s", backend_id, exc)
        raise RuntimeError(f"All AI gateway candidates failed after {len(attempts)} attempt(s)") from last_error

    def status(self) -> list[dict[str, Any]]:
        """Return safe operational metadata; secrets are never included."""
        return [
            {
                "id": config.id,
                "provider": config.provider,
                "model": config.model,
                "enabled": config.enabled,
                "healthy": self.stats.get(config.id, BackendStats()).available,
                "successes": self.stats.get(config.id, BackendStats()).successes,
                "failures": self.stats.get(config.id, BackendStats()).failures,
            }
            for config in self.backends.values()
        ]


def build_backend_from_config(config: BackendConfig) -> Any:
    """Instantiate one of Br-Jarvis's existing provider adapters from config."""
    from brjarvis.integrations.backends import (
        ClaudeBackend,
        DeepSeekBackend,
        GeminiBackend,
        ManusBackend,
        MistralBackend,
        NvidiaBackend,
        OllamaBackend,
        OpenAIBackend,
    )

    provider = config.provider.lower().replace("_", "-")
    api_key = os.getenv(config.api_key_env, "") if config.api_key_env else None
    if provider in {"ollama", "local"} and OllamaBackend:
        host = config.base_url.removesuffix("/v1") if config.base_url else None
        return OllamaBackend(model=config.model or None, host=host)

    adapter = {
        "openai": OpenAIBackend,
        "openai-compatible": OpenAIBackend,
        "proxy": OpenAIBackend,
        "proxy-brain": OpenAIBackend,
        "gemini": GeminiBackend,
        "manus": ManusBackend,
        "google": GeminiBackend,
        "anthropic": ClaudeBackend,
        "claude": ClaudeBackend,
        "deepseek": DeepSeekBackend,
        "mistral": MistralBackend,
        "nvidia": NvidiaBackend,
    }.get(provider)
    if adapter is None:
        raise ValueError(f"No Br-Jarvis adapter is registered for provider '{config.provider}'")
    try:
        return adapter(model=config.model or None, api_key=api_key, base_url=config.base_url or None)
    except TypeError:
        # Provider-native adapters may not expose the OpenAI-compatible kwargs.
        return adapter(model=config.model or None)


_gateway_singleton: AIGatewayRouter | None = None


def get_configured_gateway_router(force_reload: bool = False, config_path: str | Path | None = None) -> AIGatewayRouter:
    """Return the shared router loaded from ``config/ai_gateway.yaml``."""
    global _gateway_singleton
    if _gateway_singleton is None or force_reload:
        if config_path is None:
            configured_path = os.getenv("BRJARVIS_AI_GATEWAY_CONFIG", "").strip()
            if configured_path:
                config_path = configured_path
            else:
                from brjarvis.core.paths import paths

                config_path = paths.CONFIG_ROOT / "ai_gateway.yaml"
        _gateway_singleton = AIGatewayRouter.from_file(config_path, backend_factory=build_backend_from_config)
    return _gateway_singleton


__all__ = [
    "AIGatewayRouter",
    "BackendConfig",
    "RoutePolicy",
    "RouteDecision",
    "GatewayResponse",
    "build_backend_from_config",
    "get_configured_gateway_router",
]
