"""Typed gateway failures used to drive safe retry and failover."""

from __future__ import annotations


class GatewayError(Exception):
    """Base class for provider-neutral gateway errors."""


class AdapterUnavailableError(GatewayError):
    """Raised when an adapter cannot currently serve a request."""


class ProviderRequestError(GatewayError):
    """Raised when a provider request fails after normalization."""


class ProviderAuthenticationError(ProviderRequestError):
    """Raised when provider credentials are rejected."""


class ProviderRateLimitError(ProviderRequestError):
    """Raised when a provider reports quota or rate limiting."""


class ProviderResponseError(GatewayError):
    """Raised when a provider response cannot be normalized."""


class NoRouteAvailableError(GatewayError):
    """Raised when no healthy adapter can satisfy a request."""
