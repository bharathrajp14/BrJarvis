"""OpenRouter provider adapter for free-tier reasoning, coding, and vision fallback."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterator
from pathlib import Path

import httpx

from ..contracts import ModelRequest, ModelResponse
from ..quota import ProviderQuotaManager, get_quota_manager
from .openai import OpenAIAdapter

logger = logging.getLogger("jarvis.gateway.openrouter")


class OpenRouterAdapter(OpenAIAdapter):
    """Adapter for OpenRouter free and fallback reasoning/vision models."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "openrouter/free",
        models: frozenset[str] | None = None,
        timeout: float = 35.0,
        quota_manager: ProviderQuotaManager | None = None,
    ) -> None:
        self._openrouter_api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self._openrouter_api_key:
            env_file = Path(__file__).resolve().parents[4] / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("OPENROUTER_API_KEY="):
                        self._openrouter_api_key = line.partition("=")[2].strip().strip('"').strip("'")
                        break

        super().__init__(
            provider="openrouter",
            model=default_model,
            api_key=self._openrouter_api_key,
            base_url=base_url,
            models=models or frozenset({"openrouter/free"}),
            # Text reasoning, coding, and multimodal vision INPUT only (NO image generation output)
            capabilities=frozenset({"chat", "code", "reasoning", "vision", "image_understanding", "general_free_fallback"}),
        )
        self._timeout = timeout
        self._quota_manager = quota_manager or get_quota_manager()
        self._discovered_free_models: list[str] = []
        self._last_discovery_time: float = 0.0

    @property
    def available(self) -> bool:
        return bool(self._openrouter_api_key) and self._quota_manager.is_available(self.provider)

    def discover_free_models(self, force: bool = False) -> list[str]:
        """Dynamically query /models catalog to find currently active free models."""
        now = time.monotonic()
        if not force and self._discovered_free_models and (now - self._last_discovery_time) < 3600.0:
            return self._discovered_free_models

        url = f"{self._base_url}/models"
        headers = {"Authorization": f"Bearer {self._openrouter_api_key}"}
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                self._quota_manager.update_from_headers(self.provider, resp.headers)

            if resp.status_code == 200:
                data = resp.json().get("data", [])
                free_list: list[str] = []
                for m in data:
                    model_id = str(m.get("id", ""))
                    pricing = m.get("pricing", {})
                    # Look for free pricing or :free suffix
                    if model_id.endswith(":free") or (
                        str(pricing.get("prompt", "1")) == "0" and str(pricing.get("completion", "1")) == "0"
                    ):
                        free_list.append(model_id)

                if free_list:
                    # Put openrouter/free first if present
                    if "openrouter/free" in free_list:
                        free_list.remove("openrouter/free")
                        free_list.insert(0, "openrouter/free")
                    else:
                        free_list.insert(0, "openrouter/free")

                    self._discovered_free_models = free_list
                    self._models = frozenset(free_list)
                    self._last_discovery_time = now
                    logger.info("[OpenRouter] Discovered %d free models: %s", len(free_list), free_list[:5])
                    return free_list

        except Exception as exc:
            logger.warning("[OpenRouter] Free model discovery failed: %s", exc)

        fallback = ["openrouter/free"]
        self._discovered_free_models = fallback
        self._models = frozenset(fallback)
        return fallback

    def generate(self, request: ModelRequest) -> ModelResponse:
        self._require_available()
        # Ensure we have active models discovered
        if not self._discovered_free_models:
            self.discover_free_models()

        model_name = request.model or self.default_model
        # If model is not set or not in discovered models, use best free candidate
        if not model_name or (model_name != "openrouter/free" and model_name not in self._models):
            model_name = self._discovered_free_models[0] if self._discovered_free_models else "openrouter/free"

        self._quota_manager.record_request(self.provider, model=model_name, capability="general_free_fallback")
        try:
            response = super().generate(request.with_model(model_name))
            tokens = sum(response.usage.values()) if response.usage else 0
            self._quota_manager.record_success(self.provider, tokens=tokens)
            return response
        except Exception as exc:
            self._quota_manager.record_failure(self.provider, exc)
            raise

    def stream(self, request: ModelRequest) -> Iterator[str]:
        self._require_available()
        if not self._discovered_free_models:
            self.discover_free_models()

        model_name = request.model or self.default_model
        if not model_name or (model_name != "openrouter/free" and model_name not in self._models):
            model_name = self._discovered_free_models[0] if self._discovered_free_models else "openrouter/free"

        self._quota_manager.record_request(self.provider, model=model_name, capability="general_free_fallback")
        try:
            for chunk in super().stream(request.with_model(model_name)):
                yield chunk
            self._quota_manager.record_success(self.provider)
        except Exception as exc:
            self._quota_manager.record_failure(self.provider, exc)
            raise


__all__ = ["OpenRouterAdapter"]
