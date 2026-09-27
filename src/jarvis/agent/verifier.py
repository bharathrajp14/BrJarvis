"""Physical post-condition verifiers for agent operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class VerificationResult:
    """Outcome of physical post-condition verification."""

    verified: bool
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


class FileVerifier:
    """Verifies physical filesystem state after tool execution."""

    @staticmethod
    def verify_exists(target_path: str | Path) -> VerificationResult:
        """Verify that a target file or directory exists."""
        p = Path(target_path)
        if not p.exists():
            return VerificationResult(
                verified=False,
                reason=f"Target path does not exist: {target_path}",
                details={"path": str(target_path)},
            )
        return VerificationResult(
            verified=True,
            reason=f"Target path exists: {target_path}",
            details={"path": str(target_path), "is_file": p.is_file(), "size": p.stat().st_size if p.is_file() else 0},
        )

    @staticmethod
    def verify_non_empty(target_path: str | Path) -> VerificationResult:
        """Verify that a target file exists and has size > 0 bytes."""
        p = Path(target_path)
        if not p.exists():
            return VerificationResult(
                verified=False,
                reason=f"Target file does not exist: {target_path}",
                details={"path": str(target_path)},
            )
        if not p.is_file():
            return VerificationResult(
                verified=False,
                reason=f"Target path is not a file: {target_path}",
                details={"path": str(target_path)},
            )
        size = p.stat().st_size
        if size == 0:
            return VerificationResult(
                verified=False,
                reason=f"Target file is empty (0 bytes): {target_path}",
                details={"path": str(target_path), "size": 0},
            )
        return VerificationResult(
            verified=True,
            reason=f"Target file verified ({size} bytes): {target_path}",
            details={"path": str(target_path), "size": size},
        )

    @staticmethod
    def verify_contains(target_path: str | Path, substring: str) -> VerificationResult:
        """Verify that a target file contains the specified substring."""
        p = Path(target_path)
        if not p.is_file():
            return VerificationResult(
                verified=False,
                reason=f"Target file does not exist or is not a file: {target_path}",
                details={"path": str(target_path)},
            )
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            if substring in content:
                return VerificationResult(
                    verified=True,
                    reason=f"Target file contains substring '{substring[:40]}...'",
                    details={"path": str(target_path)},
                )
            return VerificationResult(
                verified=False,
                reason=f"Target file does not contain expected substring '{substring[:40]}...'",
                details={"path": str(target_path)},
            )
        except Exception as exc:
            return VerificationResult(
                verified=False,
                reason=f"Failed to read file {target_path}: {exc}",
                details={"path": str(target_path), "error": str(exc)},
            )


class ProcessVerifier:
    """Verifies process termination states."""

    @staticmethod
    def verify_exit_code(exit_code: int, expected: int = 0) -> VerificationResult:
        """Verify process exited with the expected exit code."""
        if exit_code == expected:
            return VerificationResult(
                verified=True,
                reason=f"Process exited cleanly with code {exit_code}",
                details={"exit_code": exit_code},
            )
        return VerificationResult(
            verified=False,
            reason=f"Process exited with non-zero exit code {exit_code} (expected {expected})",
            details={"exit_code": exit_code, "expected": expected},
        )
