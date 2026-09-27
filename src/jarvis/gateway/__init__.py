"""Canonical provider gateway for the BrJarvis rebuild."""

from .contracts import Message, ModelRequest, ModelResponse, ProviderAdapter, ToolDefinition
from .errors import (
    AdapterUnavailableError,
    GatewayError,
    NoRouteAvailableError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
)
from .factory import build_configured_gateway
from .model_gateway import ModelGateway
from .quota import ProviderMetrics, ProviderQuotaManager, ProviderStatus, get_quota_manager
from .routing import Capability, CircuitState, RouteDecision, RoutePolicy, Router, build_canonical_policies

__all__ = [
    "ModelGateway",
    "build_configured_gateway",
    "ModelRequest",
    "ModelResponse",
    "Message",
    "ToolDefinition",
    "ProviderAdapter",
    "Capability",
    "RouteDecision",
    "RoutePolicy",
    "CircuitState",
    "Router",
    "build_canonical_policies",
    "ProviderStatus",
    "ProviderMetrics",
    "ProviderQuotaManager",
    "get_quota_manager",
    "GatewayError",
    "AdapterUnavailableError",
    "NoRouteAvailableError",
    "ProviderAuthenticationError",
    "ProviderRateLimitError",
    "ProviderRequestError",
    "ProviderResponseError",
]
