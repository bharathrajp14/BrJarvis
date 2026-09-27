"""Unit tests for the multi-provider capability gateway, quota manager, and adapters."""

from __future__ import annotations

import io
import time
import wave
from pathlib import Path

import pytest

from jarvis.gateway.adapters.base import BaseAdapter, InMemoryAdapter
from jarvis.gateway.adapters.gemini_audio import GeminiAudioAdapter
from jarvis.gateway.adapters.groq_stt import GroqSTTAdapter
from jarvis.gateway.adapters.pollinations import PollinationsAdapter
from jarvis.gateway.contracts import ModelRequest, ModelResponse
from jarvis.gateway.errors import GatewayError, NoRouteAvailableError
from jarvis.gateway.model_gateway import ModelGateway
from jarvis.gateway.quota import (
    ProviderMetrics,
    ProviderQuotaManager,
    ProviderStatus,
    SlidingWindowCounter,
)
from jarvis.gateway.routing import (
    Capability,
    RoutePolicy,
    Router,
    build_canonical_policies,
)


class MockSTTAdapter(BaseAdapter):
    """Deterministic mock adapter for STT capability."""

    def __init__(self, available: bool = True, fail: bool = False):
        super().__init__(
            provider="mock_stt",
            default_model="mock-whisper",
            models=frozenset({"mock-whisper"}),
            capabilities=frozenset({"speech_to_text", "stt"}),
        )
        self._is_available = available
        self._fail = fail

    @property
    def available(self) -> bool:
        return self._is_available

    def transcribe(self, audio_source, **kwargs):
        if self._fail:
            raise RuntimeError("STT transcription failure")
        return {"text": "mock transcript", "language": "en"}

    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(text="mock transcript", provider=self.provider, model=self.default_model)

    def stream(self, request: ModelRequest):
        yield "mock transcript"


class MockTTSAdapter(BaseAdapter):
    """Deterministic mock adapter for TTS capability."""

    def __init__(self, available: bool = True, fail: bool = False):
        super().__init__(
            provider="mock_tts",
            default_model="mock-tts",
            models=frozenset({"mock-tts"}),
            capabilities=frozenset({"text_to_speech", "tts"}),
        )
        self._is_available = available
        self._fail = fail

    @property
    def available(self) -> bool:
        return self._is_available

    def synthesize_speech(self, text, **kwargs):
        if self._fail:
            raise RuntimeError("TTS synthesis failure")
        return b"RIFFmockwavdata"

    def generate(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(text="[AUDIO]", provider=self.provider, model=self.default_model)

    def stream(self, request: ModelRequest):
        yield "[AUDIO]"


def test_sliding_window_counter():
    counter = SlidingWindowCounter()
    now = 1000.0
    counter.record(5, timestamp=now - 70.0)
    counter.record(10, timestamp=now - 30.0)
    counter.record(3, timestamp=now - 5.0)

    # Within 60 seconds: should include 10 + 3 = 13
    assert counter.count_since(60.0, now=now) == 13
    # Within 120 seconds: should include 5 + 10 + 3 = 18
    assert counter.count_since(120.0, now=now) == 18


def test_quota_manager_header_parsing():
    qm = ProviderQuotaManager()
    headers = {
        "x-ratelimit-remaining-requests": "1999",
        "x-ratelimit-limit-requests": "2000",
        "x-ratelimit-remaining-tokens": "50000",
        "x-ratelimit-limit-tokens": "100000",
        "x-ratelimit-reset-requests": "45.5s",
    }
    qm.update_from_headers("test_provider", headers)
    metrics = qm.get_metrics("test_provider")

    assert metrics.remaining_requests == 1999
    assert metrics.limit_requests == 2000
    assert metrics.remaining_tokens == 50000
    assert metrics.limit_tokens == 100000
    assert metrics.reset_time_epoch is not None


def test_quota_manager_status_transitions():
    qm = ProviderQuotaManager(default_cooldown_seconds=0.1)

    # Initial status
    assert qm.get_status("prov") == ProviderStatus.UNKNOWN
    assert qm.is_available("prov") is True

    # After success
    qm.record_success("prov", tokens=150)
    assert qm.get_status("prov") == ProviderStatus.HEALTHY
    assert qm.is_available("prov") is True

    # 401 Auth failure
    class AuthError(Exception):
        status_code = 401

    qm.record_failure("prov", AuthError("Unauthorized"))
    assert qm.get_status("prov") == ProviderStatus.AUTH_FAILURE
    assert qm.is_available("prov") is False


def test_router_capability_matching_and_fallback():
    qm = ProviderQuotaManager()
    mock_stt1 = MockSTTAdapter(available=True, fail=True)
    mock_stt2 = MockSTTAdapter(available=True, fail=False)

    adapters = {
        "stt_primary": mock_stt1,
        "stt_fallback": mock_stt2,
    }
    policy = RoutePolicy(
        name="speech_to_text",
        providers=("stt_primary", "stt_fallback"),
        required_capabilities=frozenset({"speech_to_text"}),
        max_fallbacks=1,
    )
    router = Router(quota_manager=qm)
    gateway = ModelGateway(adapters, policies=[policy], router=router)

    res = gateway.transcribe(b"dummy")
    assert res["text"] == "mock transcript"
    # Verify primary failed and fallback succeeded
    assert router.state("stt_primary").failures == 1
    assert router.state("stt_fallback").successes == 1


def test_router_no_route_when_all_in_cooldown():
    qm = ProviderQuotaManager(default_cooldown_seconds=60.0)
    mock = InMemoryAdapter()
    adapters = {"mock": mock}
    policy = RoutePolicy(name="default", providers=("mock",))
    router = Router(quota_manager=qm)
    gateway = ModelGateway(adapters, policies=[policy], router=router)

    # Mark mock as failing
    router.record_failure("mock", RuntimeError("Failure"))

    with pytest.raises(NoRouteAvailableError):
        gateway.generate([{"role": "user", "content": "hi"}])


def test_gemini_audio_pcm_to_wav_format():
    # 24000 Hz, 16-bit mono, 0.5 seconds = 12000 samples = 24000 bytes
    raw_pcm = b"\x00\x00" * 12000
    wav_bytes = GeminiAudioAdapter._pcm_to_wav(raw_pcm, sample_rate=24000)

    assert len(wav_bytes) > len(raw_pcm)
    assert wav_bytes[:4] == b"RIFF"
    assert wav_bytes[8:12] == b"WAVE"

    # Verify wave header readability
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 24000
        assert wf.getnframes() == 12000


def test_pollinations_prompt_and_dimension_resolution():
    adapter = PollinationsAdapter(api_key="test_key")

    w, h = adapter._resolve_dimensions(1024, 1024, "16:9")
    assert (w, h) == (1280, 720)

    w, h = adapter._resolve_dimensions(1024, 1024, "1:1")
    assert (w, h) == (1024, 1024)

    prompt = adapter._normalize_prompt("   A   futuristic    cityscape   \n\n with neon lights  ")
    assert prompt == "A futuristic cityscape with neon lights"


def test_pollinations_magic_bytes_validation():
    # Valid PNG
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    assert PollinationsAdapter._validate_image_content(png_bytes) == "png"

    # Valid JPEG
    jpg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    assert PollinationsAdapter._validate_image_content(jpg_bytes) == "jpg"

    # Invalid bytes
    with pytest.raises(Exception):
        PollinationsAdapter._validate_image_content(b"not an image file")


def test_groq_mime_and_audio_loading(tmp_path):
    assert GroqSTTAdapter._mime_for_filename("test.wav") == "audio/wav"
    assert GroqSTTAdapter._mime_for_filename("voice.mp3") == "audio/mpeg"
    assert GroqSTTAdapter._mime_for_filename("clip.m4a") == "audio/m4a"

    sample_file = tmp_path / "test.wav"
    sample_file.write_bytes(b"dummy wav data")

    data, name = GroqSTTAdapter._load_audio(sample_file)
    assert data == b"dummy wav data"
    assert name == "test.wav"
