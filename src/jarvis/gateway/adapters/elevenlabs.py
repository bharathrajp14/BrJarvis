"""ElevenLabs provider adapter for optional premium TTS fallback."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from pathlib import Path

import httpx

from ..contracts import ModelRequest, ModelResponse
from ..errors import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from ..quota import ProviderQuotaManager, ProviderStatus, get_quota_manager
from .base import BaseAdapter

logger = logging.getLogger("jarvis.gateway.elevenlabs")

# Common default voice: Rachel
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
DEFAULT_MODEL_ID = "eleven_turbo_v2_5"


class ElevenLabsAdapter(BaseAdapter):
    """Optional premium TTS provider adapter with immediate auth-failure isolation."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.elevenlabs.io/v1",
        default_voice_id: str = DEFAULT_VOICE_ID,
        default_model: str = DEFAULT_MODEL_ID,
        timeout: float = 20.0,
        quota_manager: ProviderQuotaManager | None = None,
    ) -> None:
        super().__init__(
            provider="elevenlabs",
            default_model=default_model,
            models=frozenset({"eleven_turbo_v2_5", "eleven_multilingual_v2", "eleven_monolingual_v1"}),
            capabilities=frozenset({"tts", "text_to_speech"}),
        )
        self._api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        if not self._api_key:
            env_file = Path(__file__).resolve().parents[4] / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("ELEVENLABS_API_KEY="):
                        self._api_key = line.partition("=")[2].strip().strip('"').strip("'")
                        break

        self.default_voice_id = default_voice_id
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._quota_manager = quota_manager or get_quota_manager()

    @property
    def available(self) -> bool:
        if not self._api_key:
            return False
        # If marked as auth failure or in cooldown, do not attempt
        status = self._quota_manager.get_status(self.provider)
        return status not in (ProviderStatus.AUTH_FAILURE, ProviderStatus.DISABLED, ProviderStatus.RATE_LIMITED, ProviderStatus.QUOTA_EXHAUSTED)

    def synthesize_speech(
        self,
        text: str,
        *,
        voice_id: str | None = None,
        model_id: str | None = None,
    ) -> bytes:
        """Synthesize text using ElevenLabs REST endpoint."""
        self._require_available()
        text_clean = text.strip()
        if not text_clean:
            raise ValueError("Text to synthesize cannot be empty")

        voice = voice_id or self.default_voice_id
        model = model_id or self.default_model

        url = f"{self._base_url}/text-to-speech/{voice}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text_clean,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        self._quota_manager.record_request(self.provider, model=model, capability="text_to_speech")
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
                self._quota_manager.update_from_headers(self.provider, resp.headers)

            if resp.status_code == 200 and len(resp.content) > 100:
                self._quota_manager.record_success(self.provider)
                return resp.content

            if resp.status_code in (401, 403):
                err = ProviderAuthenticationError(f"ElevenLabs invalid API key / unauthorized: {resp.text[:150]}")
                self._quota_manager.record_failure(self.provider, err)
                raise err

            if resp.status_code == 429:
                err = ProviderRateLimitError(f"ElevenLabs rate limit: {resp.text[:150]}")
                self._quota_manager.record_failure(self.provider, err)
                raise err

            err = ProviderRequestError(f"ElevenLabs error {resp.status_code}: {resp.text[:150]}")
            self._quota_manager.record_failure(self.provider, err)
            raise err

        except (ProviderAuthenticationError, ProviderRateLimitError, ProviderRequestError):
            raise
        except Exception as exc:
            err = ProviderRequestError(f"ElevenLabs connection failure: {exc}")
            self._quota_manager.record_failure(self.provider, err)
            raise err from exc

    def generate(self, request: ModelRequest) -> ModelResponse:
        self._require_available()
        text = request.messages[-1].get("content", "") if request.messages else ""
        if isinstance(text, list):
            text = " ".join(item.get("text", "") for item in text if isinstance(item, dict))

        voice_id = request.metadata.get("voice_id", self.default_voice_id)
        audio_bytes = self.synthesize_speech(str(text), voice_id=voice_id, model_id=request.model or self.default_model)
        return ModelResponse(
            text=f"[ELEVENLABS AUDIO: {len(audio_bytes)} bytes]",
            provider=self.provider,
            model=request.model or self.default_model,
            finish_reason="stop",
            raw=audio_bytes,
        )

    def stream(self, request: ModelRequest) -> Iterator[str]:
        resp = self.generate(request)
        yield resp.text


__all__ = ["ElevenLabsAdapter"]
