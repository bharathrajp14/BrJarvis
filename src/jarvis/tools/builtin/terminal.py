"""Subprocess terminal execution with timeout bounds and working directory containment."""

from __future__ import annotations

import subprocess
import time
from typing import Any

from jarvis.tools.contracts import (
    ToolContext,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    ToolRiskLevel,
)
from jarvis.tools.registry import ToolRegistry


def handle_run_command(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    """Execute a shell command within the workspace directory with timeout limits."""
    command = args.get("command", "").strip()
    if not command:
        return ToolResult.err("No command specified.")

    timeout_sec = max(1, min(int(args.get("timeout_seconds", 30)), 120))
    t0 = time.monotonic()

    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(ctx.workspace_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
        )
        elapsed = int((time.monotonic() - t0) * 1000)

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        combined = stdout
        if stderr:
            combined = f"{stdout}\n[stderr]\n{stderr}" if stdout else stderr

        evidence = (
            f"Command exited with code {proc.returncode} in {elapsed}ms. "
            f"Output preview: {combined[:120].replace(chr(10), ' ')}"
        )

        metadata = {
            "returncode": proc.returncode,
            "stdout": stdout[:4000],
            "stderr": stderr[:2000],
            "command": command,
        }

        if proc.returncode == 0:
            return ToolResult.ok(output=combined, evidence=evidence, execution_ms=elapsed, metadata=metadata)
        return ToolResult.err(
            error=f"Command failed with exit code {proc.returncode}: {stderr or stdout}",
            evidence=evidence,
            execution_ms=elapsed,
            metadata=metadata,
        )

    except subprocess.TimeoutExpired:
        elapsed = int((time.monotonic() - t0) * 1000)
        return ToolResult.err(
            error=f"Command timed out after {timeout_sec} seconds: {command}",
            evidence=f"Timeout expired after {timeout_sec}s",
            execution_ms=elapsed,
        )
    except Exception as exc:
        elapsed = int((time.monotonic() - t0) * 1000)
        return ToolResult.err(
            error=f"Command execution failed: {exc}",
            evidence=f"Subprocess failure: {exc}",
            execution_ms=elapsed,
        )


def register_terminal_tools(registry: ToolRegistry) -> None:
    """Register terminal execution tools into the provided registry."""
    registry.register(
        ToolDefinition(
            name="run_command",
            description="Execute a shell command with timeout bounds inside the project directory.",
            parameters=[
                ToolParameter("command", "string", "Shell command to run", required=True),
                ToolParameter(
                    "timeout_seconds", "integer", "Max execution time in seconds", required=False, default=30
                ),
            ],
            risk_level=ToolRiskLevel.HIGH,
            capabilities=frozenset({"terminal", "process"}),
        ),
        handle_run_command,
    )
