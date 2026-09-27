"""Dedicated Gemini Native Audio provider adapter for TTS and Live voice sessions."""

from __future__ import annotations

import hashlib
import io
import logging
import os
import time
import wave
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..contracts import ModelRequest, ModelResponse
from ..errors import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from ..quota import ProviderQuotaManager, get_quota_manager
from .base import BaseAdapter

logger = logging.getLogger("jarvis.gateway.gemini_audio")

# Valid TTS models supported by Google AI Studio
VALID_TTS_MODELS = {
    "gemini-3.8-flash-lite-tts",
    "gemini-3.8-flash-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts",
}

DEFAULT_SAMPLE_RATE = 24000
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH = 2  # 16-bit PCM


@dataclass(frozen=True, slots=True)
class AudioSynthesisResult:
    """Normalized result returned from Gemini Native TTS."""

    audio_bytes: bytes
    format: str
    sample_rate: int
    duration_seconds: float
    model: str
    voice: str
    cached: bool = False


class GeminiAudioAdapter(BaseAdapter):
    """Native Gemini Audio adapter communicating directly with Google AI Studio."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        default_model: str = "gemini-3.8-flash-lite-tts",
        models: frozenset[str] | None = None,
        default_voice: str = "Puck",
        cache_dir: str | Path | None = None,
        timeout: float = 25.0,
        quota_manager: ProviderQuotaManager | None = None,
    ) -> None:
        model_set = models or frozenset(VALID_TTS_MODELS)
        super().__init__(
            provider="gemini_audio",
            default_model=default_model,
            models=model_set,
            capabilities=frozenset({"tts", "text_to_speech", "voice", "audio"}),
        )
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            env_file = Path(__file__).resolve().parents[4] / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        self._api_key = line.partition("=")[2].strip().strip('"').strip("'")
                        break

        self.default_voice = default_voice
        self._timeout = timeout
        self._quota_manager = quota_manager or get_quota_manager()
        self._cache_dir = Path(cache_dir or Path(__file__).resolve().parents[4] / "data" / "cache" / "gemini_tts")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._client: Any | None = None
        self._init_client()

    def _init_client(self) -> None:
        if not self._api_key:
            return
        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
        except Exception as exc:
            logger.warning("[GeminiAudio] Failed to initialize google-genai Client: %s", exc)
            self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None and self._quota_manager.is_available(self.provider)

    def supports(self, model: str | None, capability: str | None = None) -> bool:
        if not self.available:
            return False
        if model and self._models and model not in self._models:
            return False
        if capability and capability.lower() not in self._capabilities:
            return False
        return True

    def synthesize_speech(
        self,
        text: str,
        *,
        model: str | None = None,
        voice: str | None = None,
        use_cache: bool = True,
    ) -> AudioSynthesisResult:
        """Synthesize text into WAV audio using Google AI Studio native TTS."""
        self._require_available()
        text_clean = text.strip()
        if not text_clean:
            raise ValueError("Text to synthesize cannot be empty")

        chosen_model = model or self.default_model
        if chosen_model not in self._models:
            chosen_model = self.default_model
        chosen_voice = voice or self.default_voice

        # 1. Check audio cache
        cache_key = hashlib.sha256(f"{chosen_model}:{chosen_voice}:{text_clean}".encode("utf-8")).hexdigest()
        cache_file = self._cache_dir / f"{cache_key}.wav"
        if use_cache and cache_file.exists():
            data = cache_file.read_bytes()
            duration = len(data) / (DEFAULT_SAMPLE_RATE * DEFAULT_SAMPLE_WIDTH * DEFAULT_CHANNELS)
            return AudioSynthesisResult(
                audio_bytes=data,
                format="wav",
                sample_rate=DEFAULT_SAMPLE_RATE,
                duration_seconds=duration,
                model=chosen_model,
                voice=chosen_voice,
                cached=True,
            )

        # 2. Call Google GenAI SDK
        from google.genai import types

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=chosen_voice)
                )
            ),
        )

        self._quota_manager.record_request(self.provider, model=chosen_model, capability="text_to_speech")
        start_time = time.monotonic()

        try:
            response = self._client.models.generate_content(
                model=chosen_model,
                contents=text_clean,
                config=config,
            )

            # Extract raw PCM bytes
            raw_pcm: bytes | None = None
            if response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        inline_data = getattr(part, "inline_data", None)
                        if inline_data and inline_data.data:
                            raw_pcm = inline_data.data
                            break

            if not raw_pcm:
                raise ProviderRequestError(f"Gemini native audio model '{chosen_model}' did not return audio data")

            # Convert PCM to standard RIFF WAV
            wav_bytes = self._pcm_to_wav(raw_pcm, sample_rate=DEFAULT_SAMPLE_RATE)
            duration = len(raw_pcm) / (DEFAULT_SAMPLE_RATE * DEFAULT_SAMPLE_WIDTH * DEFAULT_CHANNELS)

            # Store in cache
            if use_cache:
                try:
                    cache_file.write_bytes(wav_bytes)
                except Exception as cache_err:
                    logger.debug("[GeminiAudio] Failed to write cache: %s", cache_err)

            self._quota_manager.record_success(self.provider, audio_seconds=duration)
            logger.info(
                "[GeminiAudio] Synthesized %.2fs audio in %.2fs using %s (%s)",
                duration,
                time.monotonic() - start_time,
                chosen_model,
                chosen_voice,
            )

            return AudioSynthesisResult(
                audio_bytes=wav_bytes,
                format="wav",
                sample_rate=DEFAULT_SAMPLE_RATE,
                duration_seconds=duration,
                model=chosen_model,
                voice=chosen_voice,
                cached=False,
            )

        except Exception as exc:
            status_code = getattr(exc, "status_code", getattr(exc, "code", None))
            exc_str = str(exc)
            if status_code in (401, 403) or "unauthorized" in exc_str.lower() or "api_key" in exc_str.lower():
                err = ProviderAuthenticationError(f"Gemini API auth failure: {exc_str[:200]}")
            elif status_code == 429 or "resource_exhausted" in exc_str.lower() or "quota" in exc_str.lower():
                err = ProviderRateLimitError(f"Gemini audio rate limit: {exc_str[:200]}")
            else:
                err = ProviderRequestError(f"Gemini audio request failed: {exc_str[:200]}")

            self._quota_manager.record_failure(self.provider, err)
            raise err from exc

    @staticmethod
    def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
        """Wrap raw linear PCM audio into a valid standard RIFF WAV file."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(DEFAULT_CHANNELS)
            wf.setsampwidth(DEFAULT_SAMPLE_WIDTH)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        return buf.getvalue()

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Adapts request to generate speech."""
        self._require_available()
        text = request.messages[-1].get("content", "") if request.messages else ""
        if isinstance(text, list):
            text = " ".join(item.get("text", "") for item in text if isinstance(item, dict))
        voice = request.metadata.get("voice", self.default_voice)
        res = self.synthesize_speech(str(text), model=request.model or self.default_model, voice=voice)
        return ModelResponse(
            text=f"[AUDIO: {len(res.audio_bytes)} bytes, duration={res.duration_seconds:.2f}s, voice={res.voice}]",
            provider=self.provider,
            model=request.model or self.default_model,
            finish_reason="stop",
            raw=res,
        )

    def stream(self, request: ModelRequest) -> Iterator[str]:
        resp = self.generate(request)
        yield resp.text


__all__ = ["GeminiAudioAdapter", "AudioSynthesisResult", "VALID_TTS_MODELS"]
