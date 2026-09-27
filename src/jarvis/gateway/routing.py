"""Explainable adapter routing, capability mapping, state-machine scoring, and circuit protection."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any

from .contracts import ProviderAdapter
from .errors import NoRouteAvailableError
from .quota import ProviderQuotaManager, ProviderStatus, get_quota_manager

logger = logging.getLogger("jarvis.gateway.routing")


class Capability(str, Enum):
    """Canonical model and runtime capabilities."""

    TEXT_REASONING = "text_reasoning"
    CODE = "code"
    DEEP_REASONING = "deep_reasoning"
    FAST_REASONING = "fast_reasoning"
    VISION = "vision"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    REALTIME_VOICE = "realtime_voice"
    IMAGE_GENERATION = "image_generation"
    IMAGE_UNDERSTANDING = "image_understanding"
    GENERAL_FREE_FALLBACK = "general_free_fallback"
    MEDIA_GENERATION = "media_generation"


@dataclass(frozen=True, slots=True)
class CapabilitySpec:
    """Explicit modality and feature requirements for capability validation."""

    capability: str
    input_modalities: frozenset[str] = frozenset({"text"})
    output_modalities: frozenset[str] = frozenset({"text"})
    supports_streaming: bool = False
    supports_tools: bool = False


# Canonical capability specifications guaranteeing strict compatibility
CAPABILITY_SPECS: dict[str, CapabilitySpec] = {
    Capability.TEXT_REASONING.value: CapabilitySpec(
        capability=Capability.TEXT_REASONING.value,
        input_modalities=frozenset({"text"}),
        output_modalities=frozenset({"text"}),
        supports_streaming=True,
        supports_tools=True,
    ),
    Capability.CODE.value: CapabilitySpec(
        capability=Capability.CODE.value,
        input_modalities=frozenset({"text"}),
        output_modalities=frozenset({"text"}),
        supports_streaming=True,
        supports_tools=True,
    ),
    Capability.DEEP_REASONING.value: CapabilitySpec(
        capability=Capability.DEEP_REASONING.value,
        input_modalities=frozenset({"text"}),
        output_modalities=frozenset({"text"}),
        supports_streaming=True,
        supports_tools=True,
    ),
    Capability.FAST_REASONING.value: CapabilitySpec(
        capability=Capability.FAST_REASONING.value,
        input_modalities=frozenset({"text"}),
        output_modalities=frozenset({"text"}),
        supports_streaming=True,
        supports_tools=True,
    ),
    Capability.VISION.value: CapabilitySpec(
        capability=Capability.VISION.value,
        input_modalities=frozenset({"image", "text"}),
        output_modalities=frozenset({"text"}),
        supports_streaming=True,
        supports_tools=False,
    ),
    Capability.IMAGE_UNDERSTANDING.value: CapabilitySpec(
        capability=Capability.IMAGE_UNDERSTANDING.value,
        input_modalities=frozenset({"image", "text"}),
        output_modalities=frozenset({"text"}),
        supports_streaming=True,
        supports_tools=False,
    ),
    Capability.SPEECH_TO_TEXT.value: CapabilitySpec(
        capability=Capability.SPEECH_TO_TEXT.value,
        input_modalities=frozenset({"audio"}),
        output_modalities=frozenset({"text"}),
        supports_streaming=False,
        supports_tools=False,
    ),
    Capability.TEXT_TO_SPEECH.value: CapabilitySpec(
        capability=Capability.TEXT_TO_SPEECH.value,
        input_modalities=frozenset({"text"}),
        output_modalities=frozenset({"audio"}),
        supports_streaming=True,
        supports_tools=False,
    ),
    Capability.REALTIME_VOICE.value: CapabilitySpec(
        capability=Capability.REALTIME_VOICE.value,
        input_modalities=frozenset({"audio"}),
        output_modalities=frozenset({"audio"}),
        supports_streaming=True,
        supports_tools=True,
    ),
    Capability.IMAGE_GENERATION.value: CapabilitySpec(
        capability=Capability.IMAGE_GENERATION.value,
        input_modalities=frozenset({"text"}),
        output_modalities=frozenset({"image"}),
        supports_streaming=False,
        supports_tools=False,
    ),
    Capability.GENERAL_FREE_FALLBACK.value: CapabilitySpec(
        capability=Capability.GENERAL_FREE_FALLBACK.value,
        input_modalities=frozenset({"text"}),
        output_modalities=frozenset({"text"}),
        supports_streaming=True,
        supports_tools=False,
    ),
}

CAPABILITY_ALIASES: dict[str, set[str]] = {
    "text_reasoning": {"reasoning", "chat", "text_reasoning"},
    "deep_reasoning": {"reasoning", "deep_reasoning"},
    "fast_reasoning": {"chat", "fast_reasoning", "reasoning"},
    "code": {"code"},
    "vision": {"vision", "image_understanding"},
    "image_understanding": {"vision", "image_understanding"},
    "speech_to_text": {"speech_to_text", "stt", "transcription"},
    "text_to_speech": {"text_to_speech", "tts", "voice", "audio"},
    "realtime_voice": {"realtime_voice", "voice", "audio"},
    "image_generation": {"image_generation", "image", "media_generation"},
    "general_free_fallback": {"general_free_fallback", "chat", "reasoning"},
    "media_generation": {"media_generation", "image_generation", "image"},
}


@dataclass(frozen=True, slots=True)
class RoutePolicy:
    """Named policy describing provider order, default model, and constraints."""

    name: str
    strategy: str = "score"  # "score", "priority", "round_robin"
    providers: tuple[str, ...] = ()
    required_capabilities: frozenset[str] = frozenset()
    default_model: str | None = None
    preferred_models: dict[str, str] = field(default_factory=dict)
    max_fallbacks: int = 3
    capability: Capability | None = None
    free_only: bool = False
    privacy_required: bool = False


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """Explainable result returned before an invocation starts."""

    policy: str
    selected_provider: str
    candidates: tuple[str, ...]
    model: str
    reason: str
    provider_status: str = "healthy"
    routing_score: float = 1.0


@dataclass(slots=True)
class CircuitState:
    failures: int = 0
    successes: int = 0
    opened_until: float = 0.0
    last_error: str | None = None

    @property
    def available(self) -> bool:
        return time.monotonic() >= self.opened_until


def _adapter_satisfies_capabilities(adapter_caps: frozenset[str], required: set[str]) -> bool:
    for req in required:
        req_norm = req.lower()
        aliases = CAPABILITY_ALIASES.get(req_norm, {req_norm})
        if not (adapter_caps & aliases):
            return False
    return True


class RoutingScorer:
    """Multi-variable routing score calculator based on capability, health, latency, and quota."""

    @staticmethod
    def calculate_score(
        provider: str,
        adapter: ProviderAdapter,
        model: str,
        spec: CapabilitySpec | None,
        quota_mgr: ProviderQuotaManager,
        *,
        privacy_required: bool = False,
        free_only: bool = False,
    ) -> float:
        # 1. Compatibility check (modality & capability)
        if spec is not None:
            aliases = CAPABILITY_ALIASES.get(spec.capability, {spec.capability})
            if not (adapter.capabilities & aliases):
                return 0.0

        # Free-only mode constraint
        model_str = (model or "").lower()
        is_free_provider = getattr(adapter, "is_free", False) or provider == "openrouter" or "free" in model_str
        is_local_provider = getattr(adapter, "is_local", False) or provider == "proxy"
        if free_only and not (is_free_provider or is_local_provider):
            return 0.0

        # Privacy constraint: local proxy allowed; external third-party blocked if private
        if privacy_required and not is_local_provider:
            return 0.0

        # 2. Health state factor
        status = quota_mgr.get_status(provider)
        health_weights = {
            ProviderStatus.HEALTHY: 1.0,
            ProviderStatus.UNKNOWN: 0.9,
            ProviderStatus.HALF_OPEN: 0.6,
            ProviderStatus.DEGRADED: 0.3,
            ProviderStatus.RATE_LIMITED: 0.0,
            ProviderStatus.AUTH_FAILED: 0.0,
            ProviderStatus.OFFLINE: 0.0,
            ProviderStatus.OPEN_CIRCUIT: 0.0,
        }
        health_score = health_weights.get(status, 0.0)
        if health_score <= 0.0:
            return 0.0

        # 3. Latency factor
        metrics = quota_mgr.get_metrics(provider)
        latency = metrics.latency_ema if metrics.latency_ema > 0 else 0.4
        latency_score = 1.0 / (1.0 + latency)

        # 4. Quota factor
        if metrics.requests_remaining is not None and metrics.requests_remaining <= 0:
            return 0.0
        quota_score = 1.0 if metrics.requests_remaining is None or metrics.requests_remaining > 10 else 0.5

        # 5. Quality tier heuristic
        quality_score = 0.9
        if any(k in model_str for k in ("opus", "pro", "flux", "v3")):
            quality_score = 1.0
        elif any(k in model_str for k in ("lite", "low", "turbo")):
            quality_score = 0.85

        # 6. Failure penalty
        penalty = min(0.6, metrics.consecutive_failures * 0.2)

        # 7. Local provider preference bonus (local-first architecture)
        local_bonus = 0.15 if is_local_provider else 0.0

        final_score = (health_score * 0.35 + latency_score * 0.25 + quota_score * 0.15 + quality_score * 0.10 + local_bonus) - penalty
        return max(0.01, min(1.0, round(final_score, 4)))


class Router:
    """Select healthy adapters using intelligent scoring and cascading failure protection."""

    def __init__(
        self,
        *,
        cooldown_seconds: float = 15.0,
        quota_manager: ProviderQuotaManager | None = None,
        max_fallback_depth: int = 3,
    ) -> None:
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self.max_fallback_depth = max(1, max_fallback_depth)
        self._states: dict[str, CircuitState] = {}
        self._round_robin: dict[str, int] = {}
        self._quota_manager = quota_manager or get_quota_manager()
        self._lock = RLock()

    def state(self, provider: str) -> CircuitState:
        with self._lock:
            return self._states.setdefault(provider, CircuitState())

    def record_success(self, provider: str, *, tokens: int = 0, audio_seconds: float = 0.0, latency_sec: float | None = None) -> None:
        with self._lock:
            state = self._states.setdefault(provider, CircuitState())
            state.successes += 1
            state.failures = 0
            state.opened_until = 0.0
            state.last_error = None
        self._quota_manager.record_success(provider, tokens=tokens, audio_seconds=audio_seconds, latency_sec=latency_sec)

    def record_failure(self, provider: str, error: Exception) -> None:
        with self._lock:
            state = self._states.setdefault(provider, CircuitState())
            state.failures += 1
            state.last_error = str(error)[:240]
            state.opened_until = time.monotonic() + self.cooldown_seconds
        self._quota_manager.record_failure(provider, error)

    def is_provider_eligible(self, provider: str, adapter: ProviderAdapter | None) -> bool:
        if not adapter or not adapter.available:
            return False
        if not self.state(provider).available:
            return False
        status = self._quota_manager.get_status(provider)
        return status in (
            ProviderStatus.HEALTHY,
            ProviderStatus.UNKNOWN,
            ProviderStatus.DEGRADED,
            ProviderStatus.HALF_OPEN,
        )

    def choose(
        self,
        adapters: dict[str, ProviderAdapter],
        *,
        policy: RoutePolicy,
        model: str | None = None,
        capability: str | None = None,
        visited_providers: set[str] | None = None,
        free_only: bool | None = None,
        privacy_required: bool | None = None,
    ) -> RouteDecision:
        cap_name = capability or (policy.capability.value if policy.capability else policy.name)
        spec = CAPABILITY_SPECS.get(cap_name)

        # Global env or policy overrides
        is_free_only = (
            free_only
            if free_only is not None
            else (policy.free_only or os.environ.get("BRJARVIS_FREE_ONLY", "").lower() in ("true", "1"))
        )
        is_privacy = privacy_required if privacy_required is not None else policy.privacy_required

        provider_ids = policy.providers or tuple(adapters)
        visited = visited_providers or set()
        eligible_with_scores: list[tuple[str, str, float]] = []

        for provider in provider_ids:
            if provider in visited:
                continue  # Cascading failure protection: do not revisit failed provider

            adapter = adapters.get(provider)
            if not self.is_provider_eligible(provider, adapter):
                continue
            assert adapter is not None

            # Resolve model for this provider
            target_model = model or policy.preferred_models.get(provider) or (
                policy.default_model if adapter.supports(policy.default_model, cap_name) else adapter.default_model
            )

            # Modality and capability filtering
            if not adapter.supports(target_model, cap_name):
                # Check if it satisfies capability spec
                if spec and not (adapter.capabilities & CAPABILITY_ALIASES.get(spec.capability, {spec.capability})):
                    continue

            score = RoutingScorer.calculate_score(
                provider,
                adapter,
                target_model,
                spec,
                self._quota_manager,
                privacy_required=is_privacy,
                free_only=is_free_only,
            )
            if score > 0.0:
                eligible_with_scores.append((provider, target_model, score))

        if not eligible_with_scores:
            reasons = []
            for p in provider_ids:
                status = self._quota_manager.get_status(p)
                reasons.append(f"{p}: status={status.value}")
            detail = "; ".join(reasons) if reasons else "no adapters configured"
            raise NoRouteAvailableError(
                f"No healthy provider satisfies policy '{policy.name}' ({detail})"
            )

        # Sort by routing score descending; preserve policy provider priority for ties
        eligible_with_scores.sort(
            key=lambda x: (x[2], -provider_ids.index(x[0]) if x[0] in provider_ids else 0),
            reverse=True,
        )

        ordered_providers = [item[0] for item in eligible_with_scores]
        if getattr(policy, "strategy", None) == "round_robin" and ordered_providers:
            with self._lock:
                idx = self._round_robin.get(policy.name, 0) % len(ordered_providers)
                self._round_robin[policy.name] = idx + 1
                ordered_providers = ordered_providers[idx:] + ordered_providers[:idx]

        candidates = tuple(ordered_providers[: max(1, policy.max_fallbacks + 1)])
        selected_provider = candidates[0]
        selected_model = next(item[1] for item in eligible_with_scores if item[0] == selected_provider)
        selected_score = next(item[2] for item in eligible_with_scores if item[0] == selected_provider)
        provider_status = self._quota_manager.get_status(selected_provider).value

        return RouteDecision(
            policy=policy.name,
            selected_provider=selected_provider,
            candidates=candidates,
            model=selected_model,
            reason=f"score-based routing (score={selected_score:.3f}); {len(candidates)} candidate(s)",
            provider_status=provider_status,
            routing_score=selected_score,
        )

    def status(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            quota_report = self._quota_manager.status()
            out: dict[str, dict[str, Any]] = {}
            for provider, state in self._states.items():
                qm = quota_report.get(provider, {})
                out[provider] = {
                    "available": state.available and qm.get("available", True),
                    "status": qm.get("status", "unknown"),
                    "failures": state.failures,
                    "successes": state.successes,
                    "last_error": state.last_error or qm.get("last_error"),
                    "rpm": qm.get("rpm", 0),
                    "tpm": qm.get("tpm", 0),
                    "cooldown_remaining_sec": qm.get("cooldown_remaining_sec", 0.0),
                }
            return out


def build_canonical_policies(available_providers: set[str]) -> list[RoutePolicy]:
    """Build production capability routing policies with deterministic fallback hierarchies."""

    def filter_p(providers: tuple[str, ...]) -> tuple[str, ...]:
        existing = tuple(p for p in providers if p in available_providers)
        return existing if existing else providers

    return [
        # 1. Text Reasoning
        RoutePolicy(
            name="text_reasoning",
            capability=Capability.TEXT_REASONING,
            providers=filter_p(("proxy", "openrouter")),
            default_model="gemini-3.1-pro-high",
            preferred_models={"proxy": "gemini-3.1-pro-high", "openrouter": "openrouter/free"},
            required_capabilities=frozenset({"reasoning"}),
            max_fallbacks=2,
        ),
        # 2. Coding
        RoutePolicy(
            name="code",
            capability=Capability.CODE,
            providers=filter_p(("proxy", "openrouter")),
            default_model="claude-sonnet-4-6",
            preferred_models={"proxy": "claude-sonnet-4-6", "openrouter": "openrouter/free"},
            required_capabilities=frozenset({"code"}),
            max_fallbacks=2,
        ),
        # 3. Deep Architecture Reasoning
        RoutePolicy(
            name="deep_reasoning",
            capability=Capability.DEEP_REASONING,
            providers=filter_p(("proxy",)),
            default_model="claude-opus-4-6-thinking",
            preferred_models={"proxy": "claude-opus-4-6-thinking"},
            required_capabilities=frozenset({"reasoning"}),
            max_fallbacks=1,
        ),
        # 4. Fast Conversational Reasoning
        RoutePolicy(
            name="fast_reasoning",
            capability=Capability.FAST_REASONING,
            providers=filter_p(("proxy", "openrouter")),
            default_model="gemini-3.8-flash-low",
            preferred_models={"proxy": "gemini-3.8-flash-low", "openrouter": "openrouter/free"},
            required_capabilities=frozenset({"chat"}),
            max_fallbacks=2,
        ),
        # 5. Speech to Text
        RoutePolicy(
            name="speech_to_text",
            capability=Capability.SPEECH_TO_TEXT,
            providers=filter_p(("groq", "gemini_audio")),
            default_model="whisper-large-v3-turbo",
            preferred_models={"groq": "whisper-large-v3-turbo"},
            required_capabilities=frozenset({"speech_to_text"}),
            max_fallbacks=1,
        ),
        # 6. Text to Speech
        RoutePolicy(
            name="text_to_speech",
            capability=Capability.TEXT_TO_SPEECH,
            providers=filter_p(("gemini_audio", "elevenlabs")),
            default_model="gemini-3.8-flash-lite-tts",
            preferred_models={"gemini_audio": "gemini-3.8-flash-lite-tts", "elevenlabs": "eleven_turbo_v2_5"},
            required_capabilities=frozenset({"text_to_speech"}),
            max_fallbacks=2,
        ),
        # 7. Realtime Voice
        RoutePolicy(
            name="realtime_voice",
            capability=Capability.REALTIME_VOICE,
            providers=filter_p(("gemini_audio",)),
            default_model="gemini-3.8-live",
            required_capabilities=frozenset({"voice"}),
            max_fallbacks=0,
        ),
        # 8. Image Generation (Strictly Pollinations - NO text fallback!)
        RoutePolicy(
            name="image_generation",
            capability=Capability.IMAGE_GENERATION,
            providers=filter_p(("pollinations",)),
            default_model="tongyi-mai/z-image-turbo",
            preferred_models={"pollinations": "tongyi-mai/z-image-turbo"},
            required_capabilities=frozenset({"image_generation"}),
            max_fallbacks=1,
        ),
        # 9. Vision & Multimodal Understanding
        RoutePolicy(
            name="vision",
            capability=Capability.VISION,
            providers=filter_p(("proxy", "openrouter")),
            default_model="gemini-3.1-flash-image",
            preferred_models={"proxy": "gemini-3.1-flash-image", "openrouter": "openrouter/free"},
            required_capabilities=frozenset({"vision"}),
            max_fallbacks=2,
        ),
        # 10. General Free Fallback
        RoutePolicy(
            name="general_free_fallback",
            capability=Capability.GENERAL_FREE_FALLBACK,
            providers=filter_p(("openrouter",)),
            default_model="openrouter/free",
            preferred_models={"openrouter": "openrouter/free"},
            required_capabilities=frozenset({"general_free_fallback"}),
            max_fallbacks=1,
            free_only=True,
        ),
    ]


__all__ = [
    "Capability",
    "CapabilitySpec",
    "CAPABILITY_SPECS",
    "CAPABILITY_ALIASES",
    "RoutePolicy",
    "RouteDecision",
    "CircuitState",
    "RoutingScorer",
    "Router",
    "build_canonical_policies",
]
