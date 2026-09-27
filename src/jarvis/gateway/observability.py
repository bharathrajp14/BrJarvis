"""Provider telemetry and observability without leaking credentials."""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from threading import RLock
from typing import Any

logger = logging.getLogger("jarvis.gateway.telemetry")

# Patterns to scrub
_CREDENTIAL_PATTERNS = [
    re.compile(r"(api[-_]?key\s*[:=]\s*['\"]?)([\w\-]{8,})(['\"]?)", re.IGNORECASE),
    re.compile(r"(bearer\s+)([\w\-]{12,})", re.IGNORECASE),
    re.compile(r"(sk-[a-zA-Z0-9_-]{16,})", re.IGNORECASE),
    re.compile(r"(gsk_[a-zA-Z0-9_-]{16,})", re.IGNORECASE),
    re.compile(r"(AIzaSy[a-zA-Z0-9_-]{16,})", re.IGNORECASE),
]


def scrub_sensitive_text(text: str) -> str:
    """Mask any leaked API keys, tokens, or credential strings."""
    if not text:
        return text
    clean = text
    for pat in _CREDENTIAL_PATTERNS:
        clean = pat.sub(r"\1***MASKED***", clean)
    return clean


@dataclass(frozen=True, slots=True)
class ProviderTelemetryEvent:
    """Normalized telemetry event emitted for every provider call."""

    run_id: str
    task_id: str
    provider: str
    model: str
    capability: str
    start_time: float
    duration_sec: float
    status: str  # "success", "failure", "timeout", "rate_limited", "auth_failed"
    fallback: bool = False
    fallback_depth: int = 0
    error_class: str | None = None
    error_message: str | None = None
    tokens: int | None = None
    quota_state: str = "unknown"
    cache_hit: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data.get("error_message"):
            data["error_message"] = scrub_sensitive_text(str(data["error_message"]))
        return data


class ProviderTelemetryEmitter:
    """Ring buffer and logger for structured provider telemetry."""

    def __init__(self, max_events: int = 500) -> None:
        self.max_events = max_events
        self._events: list[ProviderTelemetryEvent] = []
        self._lock = RLock()

    def record(self, event: ProviderTelemetryEvent) -> None:
        with self._lock:
            self._events.append(event)
            if len(self._events) > self.max_events:
                self._events.pop(0)

        # Log structured line
        logger.info(
            "[Telemetry] %s:%s capability=%s status=%s dur=%.3fs depth=%d hit=%s",
            event.provider,
            event.model,
            event.capability,
            event.status,
            event.duration_sec,
            event.fallback_depth,
            event.cache_hit,
        )

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return [e.to_dict() for e in self._events[-limit:]]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


_GLOBAL_TELEMETRY: ProviderTelemetryEmitter | None = None


def get_telemetry_emitter() -> ProviderTelemetryEmitter:
    global _GLOBAL_TELEMETRY
    if _GLOBAL_TELEMETRY is None:
        _GLOBAL_TELEMETRY = ProviderTelemetryEmitter()
    return _GLOBAL_TELEMETRY


__all__ = [
    "ProviderTelemetryEvent",
    "ProviderTelemetryEmitter",
    "get_telemetry_emitter",
    "scrub_sensitive_text",
]
