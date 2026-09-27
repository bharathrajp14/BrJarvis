"""Explainable adapter routing and circuit-breaker state."""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import RLock

from .contracts import ProviderAdapter
from .errors import NoRouteAvailableError


@dataclass(frozen=True, slots=True)
class RoutePolicy:
    """Named policy describing adapter order and selection strategy."""

    name: str
    strategy: str = "priority"
    providers: tuple[str, ...] = ()
    required_capabilities: frozenset[str] = frozenset()
    max_fallbacks: int = 3


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """Explainable result returned before an invocation starts."""

    policy: str
    selected_provider: str
    candidates: tuple[str, ...]
    model: str
    reason: str


@dataclass(slots=True)
class CircuitState:
    failures: int = 0
    successes: int = 0
    opened_until: float = 0.0
    last_error: str | None = None

    @property
    def available(self) -> bool:
        return time.monotonic() >= self.opened_until


class Router:
    """Select healthy adapters while keeping routing deterministic by default."""

    def __init__(self, *, cooldown_seconds: float = 15.0) -> None:
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self._states: dict[str, CircuitState] = {}
        self._round_robin: dict[str, int] = {}
        self._lock = RLock()

    def state(self, provider: str) -> CircuitState:
        with self._lock:
            return self._states.setdefault(provider, CircuitState())

    def record_success(self, provider: str) -> None:
        with self._lock:
            state = self._states.setdefault(provider, CircuitState())
            state.successes += 1
            state.failures = 0
            state.opened_until = 0.0
            state.last_error = None

    def record_failure(self, provider: str, error: Exception) -> None:
        with self._lock:
            state = self._states.setdefault(provider, CircuitState())
            state.failures += 1
            state.last_error = str(error)[:240]
            state.opened_until = time.monotonic() + self.cooldown_seconds

    def choose(
        self,
        adapters: dict[str, ProviderAdapter],
        *,
        policy: RoutePolicy,
        model: str | None,
        capability: str | None,
    ) -> RouteDecision:
        required = set(policy.required_capabilities)
        if capability:
            required.add(capability.lower())
        provider_ids = policy.providers or tuple(adapters)
        eligible: list[str] = []
        for provider in provider_ids:
            adapter = adapters.get(provider)
            if not adapter or not adapter.available or not self.state(provider).available:
                continue
            if model and not adapter.supports(model, capability):
                continue
            if required and not required.issubset(adapter.capabilities):
                continue
            eligible.append(provider)
        if not eligible:
            raise NoRouteAvailableError(f"No healthy provider satisfies policy '{policy.name}'")

        if policy.strategy == "round_robin":
            cursor = self._round_robin.get(policy.name, 0) % len(eligible)
            ordered = eligible[cursor:] + eligible[:cursor]
            self._round_robin[policy.name] = cursor + 1
        elif policy.strategy == "priority":
            ordered = eligible
        else:
            raise ValueError(f"Unsupported gateway routing strategy: {policy.strategy}")

        candidates = tuple(ordered[: max(0, policy.max_fallbacks) + 1])
        selected = candidates[0]
        selected_model = model or adapters[selected].default_model
        return RouteDecision(
            policy=policy.name,
            selected_provider=selected,
            candidates=candidates,
            model=selected_model,
            reason=f"{policy.strategy} strategy; {len(candidates)} eligible provider(s)",
        )

    def status(self) -> dict[str, dict[str, object]]:
        with self._lock:
            return {
                provider: {
                    "available": state.available,
                    "failures": state.failures,
                    "successes": state.successes,
                    "last_error": state.last_error,
                }
                for provider, state in self._states.items()
            }
