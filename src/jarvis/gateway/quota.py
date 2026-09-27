"""Production-grade quota, rate-limit, and health manager for gateway providers."""

from __future__ import annotations

import logging
import math
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any

logger = logging.getLogger("jarvis.gateway.quota")


class ProviderStatus(str, Enum):
    """Normalized provider operational status."""

    HEALTHY = "healthy"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXHAUSTED = "quota_exhausted"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    AUTH_FAILURE = "authentication_failure"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class SlidingWindowCounter:
    """Thread-safe minute/hour/day rolling timestamp counter."""

    timestamps: list[float] = field(default_factory=list)
    quantities: list[int] = field(default_factory=list)

    def record(self, count: int = 1, timestamp: float | None = None) -> None:
        now = time.monotonic() if timestamp is None else timestamp
        self.timestamps.append(now)
        self.quantities.append(count)
        # Prune entries older than 24 hours
        self.prune(86400.0, now=now)

    def count_since(self, window_seconds: float, now: float | None = None) -> int:
        current_time = time.monotonic() if now is None else now
        cutoff = current_time - window_seconds
        total = 0
        for ts, qty in zip(self.timestamps, self.quantities):
            if ts >= cutoff:
                total += qty
        return total

    def prune(self, max_retention_seconds: float = 86400.0, now: float | None = None) -> None:
        current_time = time.monotonic() if now is None else now
        cutoff = current_time - max_retention_seconds
        idx = 0
        while idx < len(self.timestamps) and self.timestamps[idx] < cutoff:
            idx += 1
        if idx > 0:
            del self.timestamps[:idx]
            del self.quantities[:idx]


@dataclass(slots=True)
class ProviderMetrics:
    """Operational health and quota metrics for a single provider."""

    provider: str
    status: ProviderStatus = ProviderStatus.UNKNOWN
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_request_time: float = 0.0
    last_success_time: float = 0.0
    last_error_time: float = 0.0
    last_error: str | None = None
    cooldown_until: float = 0.0
    # Limits and remaining quotas (None when unknown)
    remaining_requests: int | None = None
    limit_requests: int | None = None
    remaining_tokens: int | None = None
    limit_tokens: int | None = None
    reset_time_epoch: float | None = None
    # Rolling counters
    request_counter: SlidingWindowCounter = field(default_factory=SlidingWindowCounter)
    token_counter: SlidingWindowCounter = field(default_factory=SlidingWindowCounter)
    audio_seconds_counter: SlidingWindowCounter = field(default_factory=SlidingWindowCounter)

    @property
    def rpm(self) -> int:
        return self.request_counter.count_since(60.0)

    @property
    def rpd(self) -> int:
        return self.request_counter.count_since(86400.0)

    @property
    def tpm(self) -> int:
        return self.token_counter.count_since(60.0)

    @property
    def tpd(self) -> int:
        return self.token_counter.count_since(86400.0)

    @property
    def audio_minutes_last_hour(self) -> float:
        return self.audio_seconds_counter.count_since(3600.0) / 60.0

    @property
    def in_cooldown(self) -> bool:
        return time.monotonic() < self.cooldown_until


class ProviderQuotaManager:
    """Central quota and health tracker across all providers and model capabilities."""

    def __init__(self, *, default_cooldown_seconds: float = 30.0) -> None:
        self.default_cooldown_seconds = max(1.0, default_cooldown_seconds)
        self._providers: dict[str, ProviderMetrics] = {}
        self._lock = RLock()

    def get_metrics(self, provider: str) -> ProviderMetrics:
        with self._lock:
            if provider not in self._providers:
                self._providers[provider] = ProviderMetrics(provider=provider)
            return self._providers[provider]

    def get_status(self, provider: str) -> ProviderStatus:
        with self._lock:
            metrics = self.get_metrics(provider)
            if metrics.status == ProviderStatus.DISABLED:
                return ProviderStatus.DISABLED
            if metrics.status == ProviderStatus.AUTH_FAILURE:
                return ProviderStatus.AUTH_FAILURE
            if metrics.in_cooldown:
                if metrics.status in (ProviderStatus.RATE_LIMITED, ProviderStatus.QUOTA_EXHAUSTED):
                    return metrics.status
                return ProviderStatus.TEMPORARILY_UNAVAILABLE
            if metrics.status in (ProviderStatus.RATE_LIMITED, ProviderStatus.QUOTA_EXHAUSTED, ProviderStatus.TEMPORARILY_UNAVAILABLE):
                # Cooldown expired, restore to healthy / unknown
                metrics.status = ProviderStatus.HEALTHY if metrics.consecutive_successes > 0 else ProviderStatus.UNKNOWN
            return metrics.status

    def is_available(self, provider: str) -> bool:
        status = self.get_status(provider)
        return status in (ProviderStatus.HEALTHY, ProviderStatus.UNKNOWN)

    def record_request(
        self,
        provider: str,
        *,
        model: str | None = None,
        capability: str | None = None,
    ) -> None:
        with self._lock:
            now = time.monotonic()
            metrics = self.get_metrics(provider)
            metrics.last_request_time = now
            metrics.request_counter.record(1, now)

    def record_success(
        self,
        provider: str,
        *,
        tokens: int = 0,
        audio_seconds: float = 0.0,
    ) -> None:
        with self._lock:
            now = time.monotonic()
            metrics = self.get_metrics(provider)
            metrics.consecutive_successes += 1
            metrics.consecutive_failures = 0
            metrics.last_success_time = now
            metrics.cooldown_until = 0.0
            metrics.status = ProviderStatus.HEALTHY
            if tokens > 0:
                metrics.token_counter.record(tokens, now)
            if audio_seconds > 0.0:
                metrics.audio_seconds_counter.record(int(math.ceil(audio_seconds)), now)

    def record_failure(
        self,
        provider: str,
        error: Exception,
        *,
        cooldown_override: float | None = None,
    ) -> ProviderStatus:
        with self._lock:
            now = time.monotonic()
            metrics = self.get_metrics(provider)
            metrics.consecutive_failures += 1
            metrics.consecutive_successes = 0
            metrics.last_error_time = now
            err_str = str(error)
            metrics.last_error = err_str[:300]

            # Detect failure category
            status_code = getattr(error, "status_code", None)
            err_lower = err_str.lower()

            if status_code in (401, 403) or "unauthorized" in err_lower or "invalid api key" in err_lower or "auth" in err_lower:
                metrics.status = ProviderStatus.AUTH_FAILURE
                cooldown = 86400.0  # auth errors don't resolve automatically
            elif status_code == 429 or "rate limit" in err_lower or "quota" in err_lower or "too many requests" in err_lower:
                if "quota" in err_lower or "insufficient_quota" in err_lower or "credit" in err_lower:
                    metrics.status = ProviderStatus.QUOTA_EXHAUSTED
                    cooldown = cooldown_override or (self.default_cooldown_seconds * 4)
                else:
                    metrics.status = ProviderStatus.RATE_LIMITED
                    cooldown = cooldown_override or self.default_cooldown_seconds
            elif status_code in (500, 502, 503, 504) or "timeout" in err_lower or "connection" in err_lower or "unavailable" in err_lower:
                metrics.status = ProviderStatus.TEMPORARILY_UNAVAILABLE
                # Exponential backoff based on consecutive failures, capped at 120s
                multiplier = min(8, 2 ** (metrics.consecutive_failures - 1))
                cooldown = cooldown_override or (self.default_cooldown_seconds * multiplier)
            else:
                metrics.status = ProviderStatus.TEMPORARILY_UNAVAILABLE
                cooldown = cooldown_override or self.default_cooldown_seconds

            metrics.cooldown_until = now + cooldown
            logger.warning(
                "[QuotaManager] Provider '%s' failure (#%d): status=%s, cooldown=%.1fs, err=%s",
                provider,
                metrics.consecutive_failures,
                metrics.status.value,
                cooldown,
                metrics.last_error,
            )
            return metrics.status

    def update_from_headers(self, provider: str, headers: Mapping[str, str]) -> None:
        """Parse standard rate-limit and quota headers from provider HTTP responses."""
        with self._lock:
            metrics = self.get_metrics(provider)
            lower_headers = {k.lower(): v for k, v in headers.items()}

            # 1. Remaining requests
            for key in ("x-ratelimit-remaining-requests", "x-ratelimit-remaining", "ratelimit-remaining"):
                if key in lower_headers:
                    try:
                        metrics.remaining_requests = int(lower_headers[key])
                        if metrics.remaining_requests <= 0:
                            metrics.status = ProviderStatus.RATE_LIMITED
                        break
                    except ValueError:
                        pass

            # 2. Limit requests
            for key in ("x-ratelimit-limit-requests", "x-ratelimit-limit", "ratelimit-limit"):
                if key in lower_headers:
                    try:
                        metrics.limit_requests = int(lower_headers[key])
                        break
                    except ValueError:
                        pass

            # 3. Remaining tokens
            for key in ("x-ratelimit-remaining-tokens",):
                if key in lower_headers:
                    try:
                        metrics.remaining_tokens = int(lower_headers[key])
                        if metrics.remaining_tokens <= 0:
                            metrics.status = ProviderStatus.RATE_LIMITED
                        break
                    except ValueError:
                        pass

            # 4. Limit tokens
            for key in ("x-ratelimit-limit-tokens",):
                if key in lower_headers:
                    try:
                        metrics.limit_tokens = int(lower_headers[key])
                        break
                    except ValueError:
                        pass

            # 5. Reset time or Retry-After
            retry_after = lower_headers.get("retry-after")
            if retry_after:
                try:
                    delay = float(retry_after)
                    metrics.cooldown_until = time.monotonic() + delay
                    metrics.status = ProviderStatus.RATE_LIMITED
                except ValueError:
                    pass

            for key in ("x-ratelimit-reset-requests", "x-ratelimit-reset"):
                if key in lower_headers:
                    val = lower_headers[key]
                    # Parse values like "43.2s", "1m30s", or epoch seconds
                    delay = self._parse_reset_string(val)
                    if delay > 0:
                        metrics.reset_time_epoch = time.time() + delay
                        if metrics.remaining_requests == 0:
                            metrics.cooldown_until = time.monotonic() + delay
                    break

    @staticmethod
    def _parse_reset_string(val: str) -> float:
        val = val.strip().lower()
        if val.endswith("ms"):
            try:
                return float(val[:-2]) / 1000.0
            except ValueError:
                return 0.0
        if val.endswith("s"):
            try:
                return float(val[:-1])
            except ValueError:
                return 0.0
        if val.endswith("m"):
            try:
                return float(val[:-1]) * 60.0
            except ValueError:
                return 0.0
        m = re.match(r"(?:(\d+)m)?(\d+(?:\.\d+)?)s?", val)
        if m:
            minutes = float(m.group(1) or 0)
            seconds = float(m.group(2) or 0)
            return minutes * 60.0 + seconds
        try:
            ts = float(val)
            # If large, treat as epoch seconds
            if ts > 1_000_000_000:
                return max(0.0, ts - time.time())
            return ts
        except ValueError:
            return 0.0

    def disable_provider(self, provider: str, reason: str = "") -> None:
        with self._lock:
            metrics = self.get_metrics(provider)
            metrics.status = ProviderStatus.DISABLED
            metrics.last_error = f"Disabled: {reason}" if reason else "Disabled by user/system"

    def status(self) -> dict[str, dict[str, Any]]:
        """Explainable provider status report for observability and router diagnostics."""
        with self._lock:
            out: dict[str, dict[str, Any]] = {}
            for name, m in self._providers.items():
                out[name] = {
                    "status": self.get_status(name).value,
                    "available": self.is_available(name),
                    "consecutive_failures": m.consecutive_failures,
                    "consecutive_successes": m.consecutive_successes,
                    "rpm": m.rpm,
                    "rpd": m.rpd,
                    "tpm": m.tpm,
                    "tpd": m.tpd,
                    "audio_minutes_hour": round(m.audio_minutes_last_hour, 2),
                    "remaining_requests": m.remaining_requests if m.remaining_requests is not None else "UNKNOWN",
                    "remaining_tokens": m.remaining_tokens if m.remaining_tokens is not None else "UNKNOWN",
                    "cooldown_remaining_sec": max(0.0, round(m.cooldown_until - time.monotonic(), 1)),
                    "last_error": m.last_error,
                }
            return out


# Global singleton instance
_GLOBAL_QUOTA_MANAGER: ProviderQuotaManager | None = None


def get_quota_manager() -> ProviderQuotaManager:
    global _GLOBAL_QUOTA_MANAGER
    if _GLOBAL_QUOTA_MANAGER is None:
        _GLOBAL_QUOTA_MANAGER = ProviderQuotaManager()
    return _GLOBAL_QUOTA_MANAGER


__all__ = [
    "ProviderStatus",
    "ProviderMetrics",
    "ProviderQuotaManager",
    "get_quota_manager",
]
