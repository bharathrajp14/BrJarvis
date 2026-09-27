"""Explainable adapter routing, capability mapping, and circuit-breaker state."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from threading import RLock

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
class RoutePolicy:
    """Named policy describing adapter order, fallback hierarchy, and selection strategy."""

    name: str
    strategy: str = "priority"
    providers: tuple[str, ...] = ()
    required_capabilities: frozenset[str] = frozenset()
    default_model: str | None = None
    max_fallbacks: int = 3
    capability: Capability | None = None


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """Explainable result returned before an invocation starts."""

    policy: str
    selected_provider: str
    candidates: tuple[str, ...]
    model: str
    reason: str
    provider_status: str = "healthy"


@dataclass(slots=True)
class CircuitState:
    failures: int = 0
    successes: int = 0
    opened_until: float = 0.0
    last_error: str | None = None

    @property
    def available(self) -> bool:
        return time.monotonic() >= self.opened_until


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


def _adapter_satisfies_capabilities(adapter_caps: frozenset[str], required: set[str]) -> bool:
    for req in required:
        req_norm = req.lower()
        aliases = CAPABILITY_ALIASES.get(req_norm, {req_norm})
        if not (adapter_caps & aliases):
            return False
    return True


class Router:
    """Select healthy adapters while keeping routing deterministic by default."""

    def __init__(
        self,
        *,
        cooldown_seconds: float = 15.0,
        quota_manager: ProviderQuotaManager | None = None,
    ) -> None:
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self._states: dict[str, CircuitState] = {}
        self._round_robin: dict[str, int] = {}
        self._quota_manager = quota_manager or get_quota_manager()
        self._lock = RLock()

    def state(self, provider: str) -> CircuitState:
        with self._lock:
            return self._states.setdefault(provider, CircuitState())

    def record_success(self, provider: str, *, tokens: int = 0, audio_seconds: float = 0.0) -> None:
        with self._lock:
            state = self._states.setdefault(provider, CircuitState())
            state.successes += 1
            state.failures = 0
            state.opened_until = 0.0
            state.last_error = None
        self._quota_manager.record_success(provider, tokens=tokens, audio_seconds=audio_seconds)

    def record_failure(self, provider: str, error: Exception) -> None:
        with self._lock:
            state = self._states.setdefault(provider, CircuitState())
            state.failures += 1
            state.last_error = str(error)[:240]
            state.opened_until = time.monotonic() + self.cooldown_seconds
        self._quota_manager.record_failure(provider, error)

    def is_provider_eligible(self, provider: str, adapter: ProviderAdapter | None) -> bool:
        """Check availability via both circuit state and quota manager."""
        if not adapter or not adapter.available:
            return False
        if not self.state(provider).available:
            return False
        status = self._quota_manager.get_status(provider)
        if status in (
            ProviderStatus.DISABLED,
            ProviderStatus.AUTH_FAILURE,
            ProviderStatus.RATE_LIMITED,
            ProviderStatus.QUOTA_EXHAUSTED,
        ):
            return False
        return True

    def choose(
        self,
        adapters: dict[str, ProviderAdapter],
        *,
        policy: RoutePolicy,
        model: str | None = None,
        capability: str | None = None,
    ) -> RouteDecision:
        required = set(policy.required_capabilities)
        if capability:
            required.add(capability.lower())

        provider_ids = policy.providers or tuple(adapters)
        eligible: list[str] = []

        for provider in provider_ids:
            adapter = adapters.get(provider)
            if not self.is_provider_eligible(provider, adapter):
                continue
            assert adapter is not None
            if model and not adapter.supports(model, capability):
                continue
            if required and not _adapter_satisfies_capabilities(adapter.capabilities, required):
                continue
            eligible.append(provider)

        if not eligible:
            # Check reasons for diagnostics
            reasons = []
            for p in provider_ids:
                status = self._quota_manager.get_status(p)
                reasons.append(f"{p}: status={status.value}")
            detail = "; ".join(reasons) if reasons else "no adapters configured"
            raise NoRouteAvailableError(
                f"No healthy provider satisfies policy '{policy.name}' ({detail})"
            )

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
        selected_model = model or policy.default_model or adapters[selected].default_model
        provider_status = self._quota_manager.get_status(selected).value

        return RouteDecision(
            policy=policy.name,
            selected_provider=selected,
            candidates=candidates,
            model=selected_model,
            reason=f"{policy.strategy} strategy; {len(candidates)} eligible provider(s)",
            provider_status=provider_status,
        )

    def status(self) -> dict[str, dict[str, object]]:
        with self._lock:
            quota_report = self._quota_manager.status()
            out: dict[str, dict[str, object]] = {}
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
            providers=filter_p(("proxy", "gemini-3.1-pro-high", "gemini-3.8-flash-high", "openrouter")),
            default_model="gemini-3.1-pro-high",
            required_capabilities=frozenset({"reasoning"}),
            max_fallbacks=2,
        ),
        # 2. Coding
        RoutePolicy(
            name="code",
            capability=Capability.CODE,
            providers=filter_p(("proxy", "claude-sonnet-4-6", "gemini-3.1-pro-high", "openrouter")),
            default_model="claude-sonnet-4-6",
            required_capabilities=frozenset({"code"}),
            max_fallbacks=2,
        ),
        # 3. Deep Architecture Reasoning
        RoutePolicy(
            name="deep_reasoning",
            capability=Capability.DEEP_REASONING,
            providers=filter_p(("proxy", "claude-opus-4-6-thinking", "gemini-3.1-pro-high", "gpt-oss-120b-medium")),
            default_model="claude-opus-4-6-thinking",
            required_capabilities=frozenset({"reasoning"}),
            max_fallbacks=2,
        ),
        # 4. Fast Conversational Reasoning
        RoutePolicy(
            name="fast_reasoning",
            capability=Capability.FAST_REASONING,
            providers=filter_p(("proxy", "gemini-3.8-flash-low", "gemini-3.7-flash-low", "gemini-3.6-flash-low", "openrouter")),
            default_model="gemini-3.8-flash-low",
            required_capabilities=frozenset({"chat"}),
            max_fallbacks=2,
        ),
        # 5. Speech to Text
        RoutePolicy(
            name="speech_to_text",
            capability=Capability.SPEECH_TO_TEXT,
            providers=filter_p(("groq", "gemini_audio")),
            default_model="whisper-large-v3-turbo",
            required_capabilities=frozenset({"speech_to_text"}),
            max_fallbacks=1,
        ),
        # 6. Text to Speech
        RoutePolicy(
            name="text_to_speech",
            capability=Capability.TEXT_TO_SPEECH,
            providers=filter_p(("gemini_audio", "groq", "elevenlabs", "pollinations")),
            default_model="gemini-3.8-flash-lite-tts",
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
        # 8. Image Generation
        RoutePolicy(
            name="image_generation",
            capability=Capability.IMAGE_GENERATION,
            providers=filter_p(("pollinations",)),
            default_model="tongyi-mai/z-image-turbo",
            required_capabilities=frozenset({"image_generation"}),
            max_fallbacks=1,
        ),
        # 9. Vision & Multimodal Understanding
        RoutePolicy(
            name="vision",
            capability=Capability.VISION,
            providers=filter_p(("proxy", "gemini-3.1-flash-image", "gemini-2.5-pro", "openrouter")),
            default_model="gemini-3.1-flash-image",
            required_capabilities=frozenset({"vision"}),
            max_fallbacks=2,
        ),
        # 10. General Free Fallback
        RoutePolicy(
            name="general_free_fallback",
            capability=Capability.GENERAL_FREE_FALLBACK,
            providers=filter_p(("openrouter",)),
            default_model="openrouter/free",
            required_capabilities=frozenset({"general_free_fallback"}),
            max_fallbacks=1,
        ),
    ]


__all__ = [
    "Capability",
    "RoutePolicy",
    "RouteDecision",
    "CircuitState",
    "Router",
    "build_canonical_policies",
]
