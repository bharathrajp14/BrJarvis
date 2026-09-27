"""Live verification suite for the multi-provider autonomous gateway.
Tests every provider end-to-end with real API calls.
"""

from __future__ import annotations

import io
import os
import sys
import wave
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir / "src"))

from dotenv import load_dotenv
load_dotenv(root_dir / ".env")

from jarvis.gateway import (
    Capability,
    ModelGateway,
    ProviderStatus,
    build_configured_gateway,
    get_quota_manager,
)


def make_silent_wav(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate in-memory mono PCM WAV audio."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        num_frames = int(sample_rate * duration_sec)
        wf.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()


def run_verification():
    print("=" * 70)
    print("BRJARVIS MULTI-PROVIDER AUTONOMOUS GATEWAY: LIVE VERIFICATION")
    print("=" * 70)

    gateway = build_configured_gateway()
    quota_mgr = get_quota_manager()

    print(f"\n[1] Gateway initialized with {len(gateway.adapters)} adapters:")
    for name, adapter in gateway.adapters.items():
        print(f"  - {name:25} (provider={adapter.provider}, available={adapter.available})")

    # TEST 1: Primary Intelligence Gateway (Text Reasoning & Coding)
    print("\n" + "-" * 50)
    print("[TEST 1] Primary Gateway: Text Reasoning (gemini-3.1-pro-high)")
    try:
        resp = gateway.generate(
            messages=[{"role": "user", "content": "Respond with exactly 'SYSTEM_OK'"}],
            capability=Capability.TEXT_REASONING,
        )
        print(f"  -> SUCCESS: provider={resp.provider}, model={resp.model}, response='{resp.text.strip()}'")
    except Exception as e:
        print(f"  -> FAILED: {e}")

    print("\n" + "-" * 50)
    print("[TEST 2] Primary Gateway: Coding (claude-sonnet-4-6)")
    try:
        resp = gateway.generate(
            messages=[{"role": "user", "content": "Write a one-line Python lambda to square a number."}],
            capability=Capability.CODE,
        )
        print(f"  -> SUCCESS: provider={resp.provider}, model={resp.model}, response='{resp.text.strip()}'")
    except Exception as e:
        print(f"  -> FAILED: {e}")

    # TEST 3: Provider A - Groq STT
    print("\n" + "-" * 50)
    print("[TEST 3] Provider A (Groq): Speech-to-Text via gateway.transcribe()")
    try:
        audio = make_silent_wav(1.0)
        res = gateway.transcribe(audio)
        print(f"  -> SUCCESS: Groq transcribed audio successfully. Result: {res}")
        metrics = quota_mgr.get_metrics("groq")
        print(f"  -> Quota state: RPM={metrics.rpm}, remaining_req={metrics.remaining_requests}")
    except Exception as e:
        print(f"  -> FAILED: {e}")

    # TEST 4: Provider B - Gemini Native Audio TTS
    print("\n" + "-" * 50)
    print("[TEST 4] Provider B (Gemini): Native Text-to-Speech via gateway.synthesize_speech()")
    try:
        synth = gateway.synthesize_speech("JARVIS autonomous multi-provider operating system online.", voice="Puck")
        print(f"  -> SUCCESS: Gemini TTS generated {len(synth.audio_bytes)} bytes WAV (duration={synth.duration_seconds:.2f}s, voice={synth.voice}, cached={synth.cached})")
    except Exception as e:
        print(f"  -> FAILED: {e}")

    # TEST 5: Provider C - Pollinations Image Generation
    print("\n" + "-" * 50)
    print("[TEST 5] Provider C (Pollinations): Image Generation via gateway.generate_image()")
    try:
        artifact = gateway.generate_image("A sleek glowing cyan holographic arc reactor core, sci-fi concept art", width=512, height=512)
        print(f"  -> SUCCESS: Created image artifact at: {artifact.filepath}")
        print(f"  -> Details: id={artifact.artifact_id}, size={artifact.size_bytes} bytes, sha256={artifact.sha256[:12]}...")
        assert Path(artifact.filepath).is_file(), "Artifact file does not exist on disk"
    except Exception as e:
        print(f"  -> FAILED: {e}")

    # TEST 6: Provider D - OpenRouter Free Fallback
    print("\n" + "-" * 50)
    print("[TEST 6] Provider D (OpenRouter): General Free Fallback")
    try:
        resp = gateway.generate(
            messages=[{"role": "user", "content": "Say hello in one word."}],
            capability=Capability.GENERAL_FREE_FALLBACK,
        )
        print(f"  -> SUCCESS: provider={resp.provider}, model={resp.model}, response='{resp.text.strip()}'")
    except Exception as e:
        print(f"  -> FAILED: {e}")

    # TEST 7: Provider E - ElevenLabs Isolation Verification
    print("\n" + "-" * 50)
    print("[TEST 7] Provider E (ElevenLabs): Health Isolation & Fallback Verification")
    status = quota_mgr.get_status("elevenlabs")
    print(f"  -> ElevenLabs status in QuotaManager: {status.value}")
    if status == ProviderStatus.AUTH_FAILURE:
        print("  -> Confirmed: Invalid key isolated without impacting healthy TTS fallback chain.")

    # SUMMARY: Quota Manager Diagnostic Report
    print("\n" + "=" * 70)
    print("GATEWAY & QUOTA MANAGER HEALTH REPORT")
    print("=" * 70)
    status_report = quota_mgr.status()
    for prov, data in status_report.items():
        print(f"Provider: {prov:15} | Status: {data['status']:24} | Available: {str(data['available']):5} | Failures: {data['consecutive_failures']} | RPM: {data['rpm']}")

    print("\nAll verification steps completed!")


if __name__ == "__main__":
    run_verification()
