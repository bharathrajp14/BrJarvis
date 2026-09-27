"""CLI doctor and diagnostic commands for gateway providers without exposing secrets."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from .factory import build_configured_gateway
from .quota import get_quota_manager


def handle_providers_cli(subcommand: str = "health") -> int:
    """Entry point for `brjarvis providers [test|health|models|quotas]`."""
    console = Console()
    cmd = subcommand.lower().strip()

    if cmd in ("test", "smoke"):
        return _run_providers_test(console)
    elif cmd in ("health", "status"):
        return _run_providers_health(console)
    elif cmd in ("models", "catalogue", "catalog"):
        return _run_providers_models(console)
    elif cmd in ("quotas", "limits"):
        return _run_providers_quotas(console)
    else:
        console.print(f"[bold red]Unknown provider command:[/bold red] '{subcommand}'")
        console.print("Valid subcommands: [cyan]test, health, models, quotas[/cyan]")
        return 1


def _run_providers_health(console: Console) -> int:
    quota_mgr = get_quota_manager()
    gateway = build_configured_gateway()
    status_report = quota_mgr.status()

    table = Table(title="BRJARVIS Provider Health & Operational State")
    table.add_column("Provider", style="bold cyan")
    table.add_column("Status", style="bold")
    table.add_column("Available", justify="center")
    table.add_column("Failures", justify="right")
    table.add_column("Successes", justify="right")
    table.add_column("Cooldown (s)", justify="right")
    table.add_column("Last Error", style="dim")

    for provider_name, adapter in gateway.adapters.items():
        st = status_report.get(provider_name, {})
        status_val = st.get("status", "unknown")
        color = "green" if status_val == "healthy" else ("yellow" if status_val in ("unknown", "degraded", "half_open") else "red")
        avail_str = "[green]YES[/green]" if st.get("available", adapter.available) else "[red]NO[/red]"

        err = str(st.get("last_error") or "")[:40]
        cooldown = str(st.get("cooldown_remaining_sec", 0.0))

        table.add_row(
            provider_name,
            f"[{color}]{status_val}[/{color}]",
            avail_str,
            str(st.get("consecutive_failures", 0)),
            str(st.get("consecutive_successes", 0)),
            cooldown,
            err,
        )

    console.print(table)
    return 0


def _run_providers_models(console: Console) -> int:
    gateway = build_configured_gateway()

    table = Table(title="BRJARVIS Active Model Catalogue by Provider")
    table.add_column("Provider", style="bold cyan")
    table.add_column("Default Model", style="green")
    table.add_column("Available Models", style="white")
    table.add_column("Capabilities", style="dim")

    for provider_name, adapter in gateway.adapters.items():
        models_str = ", ".join(sorted(adapter.models)) if adapter.models else adapter.default_model
        if len(models_str) > 60:
            models_str = models_str[:57] + "..."
        caps_str = ", ".join(sorted(adapter.capabilities))

        table.add_row(
            provider_name,
            adapter.default_model,
            models_str,
            caps_str,
        )

    console.print(table)
    return 0


def _run_providers_quotas(console: Console) -> int:
    quota_mgr = get_quota_manager()
    gateway = build_configured_gateway()
    # Ensure metrics exist for all providers
    for p in gateway.adapters:
        quota_mgr.get_metrics(p)
    status_report = quota_mgr.status()

    table = Table(title="BRJARVIS Granular Quota & Sliding Rate Limits")
    table.add_column("Provider", style="bold cyan")
    table.add_column("Requests Used", justify="right")
    table.add_column("Requests Rem.", justify="right")
    table.add_column("RPM (1m)", justify="right")
    table.add_column("RPD (24h)", justify="right")
    table.add_column("TPM (1m)", justify="right")
    table.add_column("Reset At", justify="right")

    for provider_name in gateway.adapters:
        st = status_report.get(provider_name, {})
        table.add_row(
            provider_name,
            str(st.get("requests_used", 0)),
            str(st.get("requests_remaining", "UNKNOWN")),
            str(st.get("rpm", 0)),
            str(st.get("rpd", 0)),
            str(st.get("tpm", 0)),
            str(st.get("reset_at", "UNKNOWN")),
        )

    console.print(table)
    return 0


def _run_providers_test(console: Console) -> int:
    from .routing import Capability
    gateway = build_configured_gateway()

    console.print("[bold yellow]Executing safe live smoke tests across configured providers...[/bold yellow]\n")
    results_table = Table(title="Live Provider Smoke Test Results")
    results_table.add_column("Provider", style="bold cyan")
    results_table.add_column("Capability", style="white")
    results_table.add_column("Model Tested", style="white")
    results_table.add_column("Status", style="bold")
    results_table.add_column("Latency", justify="right")
    results_table.add_column("Details", style="dim")

    # 1. Proxy Text Reasoning
    t0 = console.get_time()
    try:
        resp = gateway.generate(
            messages=[{"role": "user", "content": "Respond with 'TEST_OK'"}],
            capability=Capability.TEXT_REASONING,
        )
        dur = console.get_time() - t0
        results_table.add_row("proxy", "TEXT_REASONING", resp.model, "[green]PASS[/green]", f"{dur:.2f}s", resp.text.strip()[:30])
    except Exception as e:
        results_table.add_row("proxy", "TEXT_REASONING", "unknown", "[red]FAIL[/red]", "-", str(e)[:30])

    # 2. OpenRouter Free Fallback
    t0 = console.get_time()
    try:
        resp = gateway.generate(
            messages=[{"role": "user", "content": "ping"}],
            capability=Capability.GENERAL_FREE_FALLBACK,
        )
        dur = console.get_time() - t0
        results_table.add_row("openrouter", "GENERAL_FREE_FALLBACK", resp.model, "[green]PASS[/green]", f"{dur:.2f}s", resp.text.strip()[:30])
    except Exception as e:
        results_table.add_row("openrouter", "GENERAL_FREE_FALLBACK", "unknown", "[red]FAIL[/red]", "-", str(e)[:30])

    # 3. Gemini Audio TTS
    t0 = console.get_time()
    try:
        synth = gateway.synthesize_speech("Provider test.", voice="Puck", use_cache=True)
        dur = console.get_time() - t0
        results_table.add_row("gemini_audio", "TEXT_TO_SPEECH", getattr(synth, "model", "gemini-tts"), "[green]PASS[/green]", f"{dur:.2f}s", f"{len(synth.audio_bytes)}B audio")
    except Exception as e:
        results_table.add_row("gemini_audio", "TEXT_TO_SPEECH", "unknown", "[red]FAIL[/red]", "-", str(e)[:30])

    # 4. ElevenLabs Truthful Verification
    elevenlabs = gateway.adapters.get("elevenlabs")
    if elevenlabs:
        try:
            audio = elevenlabs.synthesize_speech("Test")
            results_table.add_row("elevenlabs", "TEXT_TO_SPEECH", elevenlabs.default_model, "[green]PASS[/green]", "-", f"{len(audio)}B audio")
        except Exception:
            results_table.add_row("elevenlabs", "TEXT_TO_SPEECH", elevenlabs.default_model, "[yellow]UNAVAILABLE[/yellow]", "-", "Auth/Access restricted")

    console.print(results_table)
    return 0


__all__ = ["handle_providers_cli"]
