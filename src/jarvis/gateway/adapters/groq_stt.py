"""Groq Speech-to-Text provider adapter with streaming support, chunking, and quota awareness."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, BinaryIO

import httpx

from ..contracts import ModelRequest, ModelResponse
from ..errors import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from ..quota import ProviderQuotaManager, get_quota_manager
from .base import BaseAdapter

logger = logging.getLogger("jarvis.gateway.groq")

# Groq max payload limit is 25MB
MAX_AUDIO_CHUNK_BYTES = 24 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"}


class GroqSTTAdapter(BaseAdapter):
    """Adapter for Groq's high-speed cloud speech-to-text models."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        default_model: str = "whisper-large-v3-turbo",
        models: frozenset[str] | None = None,
        base_url: str = "https://api.groq.com/openai/v1",
        timeout: float = 30.0,
        max_retries: int = 2,
        quota_manager: ProviderQuotaManager | None = None,
    ) -> None:
        model_set = models or frozenset({"whisper-large-v3-turbo", "whisper-large-v3"})
        super().__init__(
            provider="groq",
            default_model=default_model,
            models=model_set,
            capabilities=frozenset({"stt", "speech_to_text", "transcription"}),
        )
        self._api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self._api_key:
            env_file = Path(__file__).resolve().parents[4] / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("GROQ_API_KEY="):
                        self._api_key = line.partition("=")[2].strip().strip('"').strip("'")
                        break

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._quota_manager = quota_manager or get_quota_manager()

    @property
    def available(self) -> bool:
        return bool(self._api_key) and self._quota_manager.is_available(self.provider)

    def supports(self, model: str | None, capability: str | None = None) -> bool:
        if not self.available:
            return False
        if model and self._models and model not in self._models:
            return False
        if capability and capability.lower() not in self._capabilities:
            return False
        return True

    def transcribe(
        self,
        audio_source: str | Path | bytes | BinaryIO,
        *,
        model: str | None = None,
        language: str | None = None,
        prompt: str | None = None,
        temperature: float = 0.0,
        response_format: str = "json",
        timestamps: bool = False,
    ) -> dict[str, Any]:
        """Transcribe audio to text with rate-limit tracking and retries."""
        self._require_available()
        chosen_model = model or self.default_model
        if chosen_model not in self._models:
            chosen_model = self.default_model

        audio_bytes, filename = self._load_audio(audio_source)
        if len(audio_bytes) > MAX_AUDIO_CHUNK_BYTES:
            return self._transcribe_chunked(
                audio_bytes,
                filename=filename,
                model=chosen_model,
                language=language,
                prompt=prompt,
            )

        return self._execute_transcription(
            audio_bytes,
            filename=filename,
            model=chosen_model,
            language=language,
            prompt=prompt,
            temperature=temperature,
            response_format="verbose_json" if timestamps else response_format,
            timestamps=timestamps,
        )

    def _execute_transcription(
        self,
        audio_bytes: bytes,
        *,
        filename: str,
        model: str,
        language: str | None = None,
        prompt: str | None = None,
        temperature: float = 0.0,
        response_format: str = "json",
        timestamps: bool = False,
    ) -> dict[str, Any]:
        url = f"{self._base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self._api_key}"}

        fields: dict[str, Any] = {
            "model": model,
            "temperature": str(temperature),
            "response_format": response_format,
        }
        if language:
            fields["language"] = language
        if prompt:
            fields["prompt"] = prompt
        if timestamps and response_format == "verbose_json":
            fields["timestamp_granularities[]"] = "segment"

        self._quota_manager.record_request(self.provider, model=model, capability="speech_to_text")

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                files = {"file": (filename, audio_bytes, self._mime_for_filename(filename))}
                with httpx.Client(timeout=self._timeout) as client:
                    resp = client.post(url, headers=headers, data=fields, files=files)

                # Store rate-limit headers in quota manager
                self._quota_manager.update_from_headers(self.provider, resp.headers)

                if resp.status_code == 200:
                    data = resp.json()
                    self._quota_manager.record_success(self.provider)
                    return data

                if resp.status_code in (401, 403):
                    err = ProviderAuthenticationError(f"Groq authentication failed: {resp.text[:200]}")
                    self._quota_manager.record_failure(self.provider, err)
                    raise err

                if resp.status_code == 429:
                    err = ProviderRateLimitError(f"Groq STT rate limited: {resp.text[:200]}")
                    self._quota_manager.record_failure(self.provider, err)
                    if attempt < self._max_retries:
                        time.sleep(1.0 * (attempt + 1))
                        continue
                    raise err

                err = ProviderRequestError(f"Groq STT error {resp.status_code}: {resp.text[:200]}")
                self._quota_manager.record_failure(self.provider, err)
                raise err

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_error = net_err
                self._quota_manager.record_failure(self.provider, net_err)
                if attempt < self._max_retries:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                break
            except Exception as e:
                last_error = e
                break

        raise ProviderRequestError(f"Groq transcription failed: {last_error}") from last_error

    def _transcribe_chunked(
        self,
        audio_bytes: bytes,
        *,
        filename: str,
        model: str,
        language: str | None = None,
        prompt: str | None = None,
    ) -> dict[str, Any]:
        """Simple chunking for oversized audio files."""
        chunks = [
            audio_bytes[i : i + MAX_AUDIO_CHUNK_BYTES]
            for i in range(0, len(audio_bytes), MAX_AUDIO_CHUNK_BYTES)
        ]
        transcripts: list[str] = []
        for i, chunk in enumerate(chunks):
            chunk_filename = f"part_{i}_{filename}"
            result = self._execute_transcription(
                chunk,
                filename=chunk_filename,
                model=model,
                language=language,
                prompt=prompt if i == 0 else f"{prompt or ''} Continuing transcript...",
            )
            transcripts.append(result.get("text", ""))

        return {"text": " ".join(transcripts).strip()}

    @staticmethod
    def _load_audio(source: str | Path | bytes | BinaryIO) -> tuple[bytes, str]:
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.is_file():
                raise FileNotFoundError(f"Audio file not found: {path}")
            return path.read_bytes(), path.name
        if isinstance(source, bytes):
            return source, "audio.wav"
        if hasattr(source, "read"):
            data = source.read()
            name = getattr(source, "name", "audio.wav")
            return data, Path(name).name
        raise ValueError(f"Unsupported audio source type: {type(source)}")

    @staticmethod
    def _mime_for_filename(filename: str) -> str:
        ext = Path(filename).suffix.lower()
        mimes = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/m4a",
            ".ogg": "audio/ogg",
            ".webm": "audio/webm",
            ".flac": "audio/flac",
        }
        return mimes.get(ext, "application/octet-stream")

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Adapts text messages or audio metadata into transcription."""
        self._require_available()
        audio_bytes = request.metadata.get("audio_bytes")
        audio_path = request.metadata.get("audio_path")
        if not audio_bytes and not audio_path:
            raise ProviderRequestError("GroqSTTAdapter requires 'audio_bytes' or 'audio_path' in metadata")
        source = audio_bytes or audio_path
        language = request.metadata.get("language")
        prompt = request.metadata.get("prompt")
        timestamps = bool(request.metadata.get("timestamps", False))

        result = self.transcribe(
            source,
            model=request.model or self.default_model,
            language=language,
            prompt=prompt,
            timestamps=timestamps,
        )
        text = str(result.get("text", ""))
        return ModelResponse(
            text=text,
            provider=self.provider,
            model=request.model or self.default_model,
            finish_reason="stop",
            raw=result,
        )

    def stream(self, request: ModelRequest) -> Iterator[str]:
        response = self.generate(request)
        yield response.text


__all__ = ["GroqSTTAdapter"]
