"""Production-grade quota, rate-limit, and state machine manager for gateway providers."""

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
    """Explicit operational states for provider runtime state machine."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"
    AUTH_FAILED = "auth_failed"
    AUTH_FAILURE = "auth_failed"
    OFFLINE = "offline"
    OPEN_CIRCUIT = "open_circuit"
    HALF_OPEN = "half_open"


@dataclass(slots=True)
class SlidingWindowCounter:
    """Thread-safe minute/hour/day rolling timestamp counter."""

    timestamps: list[float] = field(default_factory=list)
    quantities: list[int] = field(default_factory=list)

    def record(self, count: int = 1, timestamp: float | None = None) -> None:
        now = time.monotonic() if timestamp is None else timestamp
        self.timestamps.append(now)
        self.quantities.append(count)
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
    """Operational health, circuit state, and quota metrics for a single provider."""

    provider: str
    status: ProviderStatus = ProviderStatus.UNKNOWN
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    consecutive_timeouts: int = 0
    last_request_time: float = 0.0
    last_success_time: float = 0.0
    last_error_time: float = 0.0
    last_error: str | None = None
    cooldown_until: float = 0.0
    latency_ema: float = 0.0  # Exponential moving average latency in seconds

    # Granular Quota Model
    requests_used: int = 0
    requests_remaining: int | None = None
    rpm_limit: int | None = None
    rpm_remaining: int | None = None
    rpd_limit: int | None = None
    rpd_remaining: int | None = None
    tpd_limit: int | None = None
    token_remaining: int | None = None
    reset_at: float | None = None  # Epoch seconds
    last_request_at: float | None = None  # Epoch seconds

    # Rolling counters for runtime tracking
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

    @property
    def remaining_requests(self) -> int | None:
        return self.requests_remaining

    @remaining_requests.setter
    def remaining_requests(self, val: int | None) -> None:
        self.requests_remaining = val

    @property
    def limit_requests(self) -> int | None:
        return self.rpm_limit

    @property
    def remaining_tokens(self) -> int | None:
        return self.token_remaining

    @property
    def limit_tokens(self) -> int | None:
        return self.tpd_limit

    @property
    def reset_time_epoch(self) -> float | None:
        return self.reset_at


class ProviderQuotaManager:
    """Central state machine, rate-limit, and quota manager for gateway providers."""

    def __init__(self, *, default_cooldown_seconds: float = 30.0, timeout_degrade_threshold: int = 2, open_circuit_threshold: int = 4) -> None:
        self.default_cooldown_seconds = max(1.0, default_cooldown_seconds)
        self.timeout_degrade_threshold = max(1, timeout_degrade_threshold)
        self.open_circuit_threshold = max(2, open_circuit_threshold)
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
            now = time.monotonic()

            # State transition: OPEN_CIRCUIT -> cooldown expired -> HALF_OPEN
            if metrics.status == ProviderStatus.OPEN_CIRCUIT:
                if now >= metrics.cooldown_until:
                    metrics.status = ProviderStatus.HALF_OPEN
                    logger.info("[QuotaManager] Provider '%s' OPEN_CIRCUIT cooldown expired -> transitioned to HALF_OPEN", provider)
                return metrics.status

            # State transition: RATE_LIMITED -> cooldown expired -> HALF_OPEN
            if metrics.status == ProviderStatus.RATE_LIMITED:
                if now >= metrics.cooldown_until:
                    metrics.status = ProviderStatus.HALF_OPEN
                return metrics.status

            return metrics.status

    def is_available(self, provider: str) -> bool:
        status = self.get_status(provider)
        # HEALTHY, UNKNOWN, DEGRADED, and HALF_OPEN (trial request) are eligible
        return status in (
            ProviderStatus.HEALTHY,
            ProviderStatus.UNKNOWN,
            ProviderStatus.DEGRADED,
            ProviderStatus.HALF_OPEN,
        )

    def record_request(
        self,
        provider: str,
        *,
        model: str | None = None,
        capability: str | None = None,
    ) -> None:
        with self._lock:
            now_mono = time.monotonic()
            now_wall = time.time()
            metrics = self.get_metrics(provider)
            metrics.last_request_time = now_mono
            metrics.last_request_at = now_wall
            metrics.requests_used += 1
            metrics.request_counter.record(1, now_mono)

    def record_success(
        self,
        provider: str,
        *,
        tokens: int = 0,
        audio_seconds: float = 0.0,
        latency_sec: float | None = None,
    ) -> None:
        with self._lock:
            now = time.monotonic()
            metrics = self.get_metrics(provider)
            metrics.consecutive_successes += 1
            metrics.consecutive_failures = 0
            metrics.consecutive_timeouts = 0
            metrics.last_success_time = now
            metrics.cooldown_until = 0.0

            # State transitions on success:
            # HALF_OPEN -> success -> HEALTHY
            # DEGRADED -> success -> HEALTHY
            if metrics.status in (ProviderStatus.HALF_OPEN, ProviderStatus.DEGRADED, ProviderStatus.UNKNOWN, ProviderStatus.RATE_LIMITED):
                logger.info("[QuotaManager] Provider '%s' recovered -> HEALTHY", provider)
                metrics.status = ProviderStatus.HEALTHY

            if latency_sec is not None and latency_sec > 0.0:
                if metrics.latency_ema == 0.0:
                    metrics.latency_ema = latency_sec
                else:
                    metrics.latency_ema = 0.8 * metrics.latency_ema + 0.2 * latency_sec

            if tokens > 0:
                metrics.token_counter.record(tokens, now)
            if audio_seconds > 0.0:
                metrics.audio_seconds_counter.record(int(math.ceil(audio_seconds)), now)

    def record_timeout(self, provider: str, error: Exception) -> ProviderStatus:
        with self._lock:
            now = time.monotonic()
            metrics = self.get_metrics(provider)
            metrics.consecutive_timeouts += 1
            metrics.consecutive_failures += 1
            metrics.consecutive_successes = 0
            metrics.last_error_time = now
            metrics.last_error = str(error)[:240]

            # HEALTHY -> repeated timeout -> DEGRADED
            if metrics.consecutive_timeouts >= self.timeout_degrade_threshold and metrics.status == ProviderStatus.HEALTHY:
                metrics.status = ProviderStatus.DEGRADED
                logger.warning("[QuotaManager] Provider '%s' timed out %d times -> DEGRADED", provider, metrics.consecutive_timeouts)

            # DEGRADED -> repeated failures -> OPEN_CIRCUIT
            if metrics.consecutive_failures >= self.open_circuit_threshold:
                metrics.status = ProviderStatus.OPEN_CIRCUIT
                metrics.cooldown_until = now + self.default_cooldown_seconds
                logger.warning("[QuotaManager] Provider '%s' exceeded failure threshold -> OPEN_CIRCUIT (cooldown %.1fs)", provider, self.default_cooldown_seconds)

            return metrics.status

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
            err_lower = err_str.lower()
            status_code = getattr(error, "status_code", getattr(error, "code", None))

            # HALF_OPEN -> failure -> OPEN_CIRCUIT (immediate trip back with exponential backoff)
            if metrics.status == ProviderStatus.HALF_OPEN:
                metrics.status = ProviderStatus.OPEN_CIRCUIT
                backoff = cooldown_override or min(300.0, self.default_cooldown_seconds * 2)
                metrics.cooldown_until = now + backoff
                logger.warning("[QuotaManager] Provider '%s' failed in HALF_OPEN trial -> OPEN_CIRCUIT (cooldown %.1fs)", provider, backoff)
                return metrics.status

            if status_code in (401, 403) or "unauthorized" in err_lower or "invalid api key" in err_lower or "invalid_api_key" in err_lower:
                metrics.status = ProviderStatus.AUTH_FAILED
                metrics.cooldown_until = now + 86400.0
            elif status_code == 429 or "rate limit" in err_lower or "too many requests" in err_lower:
                metrics.status = ProviderStatus.RATE_LIMITED
                cooldown = cooldown_override or self.default_cooldown_seconds
                metrics.cooldown_until = now + cooldown
            elif "connection refused" in err_lower or "name or service not known" in err_lower or "getaddrinfo failed" in err_lower:
                metrics.status = ProviderStatus.OFFLINE
                metrics.cooldown_until = now + self.default_cooldown_seconds
            elif "timeout" in err_lower or "timed out" in err_lower:
                return self.record_timeout(provider, error)
            else:
                # General failures: check if threshold reached to trip OPEN_CIRCUIT
                if metrics.consecutive_failures >= self.open_circuit_threshold:
                    metrics.status = ProviderStatus.OPEN_CIRCUIT
                    multiplier = min(8, 2 ** (metrics.consecutive_failures - self.open_circuit_threshold))
                    cooldown = cooldown_override or (self.default_cooldown_seconds * multiplier)
                    metrics.cooldown_until = now + cooldown
                    logger.warning("[QuotaManager] Provider '%s' hit %d failures -> OPEN_CIRCUIT (cooldown %.1fs)", provider, metrics.consecutive_failures, cooldown)
                elif metrics.status == ProviderStatus.HEALTHY and metrics.consecutive_failures >= 2:
                    metrics.status = ProviderStatus.DEGRADED
                    metrics.cooldown_until = now + (self.default_cooldown_seconds / 2)

            return metrics.status

    def update_from_headers(self, provider: str, headers: Mapping[str, str]) -> None:
        """Parse standard rate-limit and quota headers from provider HTTP responses."""
        with self._lock:
            metrics = self.get_metrics(provider)
            lower_headers = {k.lower(): v for k, v in headers.items()}

            # Requests remaining & limit
            for key in ("x-ratelimit-remaining-requests", "x-ratelimit-remaining", "ratelimit-remaining"):
                if key in lower_headers:
                    try:
                        metrics.requests_remaining = int(lower_headers[key])
                        metrics.rpm_remaining = metrics.requests_remaining
                        if metrics.requests_remaining <= 0:
                            metrics.status = ProviderStatus.RATE_LIMITED
                        break
                    except ValueError:
                        pass

            for key in ("x-ratelimit-limit-requests", "x-ratelimit-limit", "ratelimit-limit"):
                if key in lower_headers:
                    try:
                        metrics.rpm_limit = int(lower_headers[key])
                        break
                    except ValueError:
                        pass

            # Tokens remaining & limit
            for key in ("x-ratelimit-remaining-tokens",):
                if key in lower_headers:
                    try:
                        metrics.token_remaining = int(lower_headers[key])
                        if metrics.token_remaining <= 0:
                            metrics.status = ProviderStatus.RATE_LIMITED
                        break
                    except ValueError:
                        pass

            for key in ("x-ratelimit-limit-tokens",):
                if key in lower_headers:
                    try:
                        metrics.tpd_limit = int(lower_headers[key])
                        break
                    except ValueError:
                        pass

            # Reset time or Retry-After
            retry_after = lower_headers.get("retry-after")
            if retry_after:
                try:
                    delay = float(retry_after)
                    metrics.cooldown_until = time.monotonic() + delay
                    metrics.reset_at = time.time() + delay
                    metrics.status = ProviderStatus.RATE_LIMITED
                except ValueError:
                    pass

            for key in ("x-ratelimit-reset-requests", "x-ratelimit-reset"):
                if key in lower_headers:
                    val = lower_headers[key]
                    delay = self._parse_reset_string(val)
                    if delay > 0:
                        metrics.reset_at = time.time() + delay
                        if metrics.requests_remaining == 0:
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
            if ts > 1_000_000_000:
                return max(0.0, ts - time.time())
            return ts
        except ValueError:
            return 0.0

    def status(self) -> dict[str, dict[str, Any]]:
        """Explainable provider status report for observability and diagnostics."""
        with self._lock:
            out: dict[str, dict[str, Any]] = {}
            for name, m in self._providers.items():
                st = self.get_status(name)
                out[name] = {
                    "status": st.value,
                    "available": self.is_available(name),
                    "consecutive_failures": m.consecutive_failures,
                    "consecutive_successes": m.consecutive_successes,
                    "consecutive_timeouts": m.consecutive_timeouts,
                    "latency_ema_sec": round(m.latency_ema, 3) if m.latency_ema > 0 else "UNKNOWN",
                    "rpm": m.rpm,
                    "rpd": m.rpd,
                    "tpm": m.tpm,
                    "tpd": m.tpd,
                    "requests_used": m.requests_used,
                    "requests_remaining": m.requests_remaining if m.requests_remaining is not None else "UNKNOWN",
                    "rpm_limit": m.rpm_limit if m.rpm_limit is not None else "UNKNOWN",
                    "rpm_remaining": m.rpm_remaining if m.rpm_remaining is not None else "UNKNOWN",
                    "rpd_limit": m.rpd_limit if m.rpd_limit is not None else "UNKNOWN",
                    "rpd_remaining": m.rpd_remaining if m.rpd_remaining is not None else "UNKNOWN",
                    "tpd_limit": m.tpd_limit if m.tpd_limit is not None else "UNKNOWN",
                    "token_remaining": m.token_remaining if m.token_remaining is not None else "UNKNOWN",
                    "reset_at": round(m.reset_at, 1) if m.reset_at is not None else "UNKNOWN",
                    "last_request_at": round(m.last_request_at, 1) if m.last_request_at is not None else "UNKNOWN",
                    "cooldown_remaining_sec": max(0.0, round(m.cooldown_until - time.monotonic(), 1)),
                    "last_error": m.last_error,
                }
            return out

    def get_all_statuses(self) -> dict[str, dict[str, Any]]:
        """Return all provider tracking records with enum status."""
        with self._lock:
            return {
                name: {"status": self.get_status(name), "metrics": m}
                for name, m in self._providers.items()
            }


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
