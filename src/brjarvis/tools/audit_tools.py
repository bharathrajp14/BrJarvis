# tools/audit_tools.py — BR JARVIS Codebase Security & Quality Auditor Engine
"""
Codebase Auditor, Security Vulnerability Scanner, and Code Quality Suite.
"""

from __future__ import annotations

import ast
import logging
import os
import re
from pathlib import Path

from .registry import register_tool

logger = logging.getLogger(__name__)


from brjarvis.core.paths import paths


def _get_workspace_dir() -> Path:
    return paths.PROJECT_ROOT


@register_tool(
    name="audit_codebase",
    description="Perform an automated security & code quality audit on the codebase. Detects syntax errors, security vulnerabilities, hardcoded secrets, and unsafe execution patterns.",
    parameters={
        "type": "object",
        "properties": {
            "target_dir": {"type": "string", "description": "Target folder path to audit (defaults to workspace root)"}
        },
    },
)
def audit_codebase(args: dict) -> str:
    """Audit python files in workspace."""
    target_path = Path(args.get("target_dir") or _get_workspace_dir()).resolve()

    syntax_errors = []
    security_findings = []
    total_files = 0
    scanned_py = 0

    ignored_dirs = {"__pycache__", ".git", ".idea", ".vscode", "venv", ".venv", "env", ".env", "node_modules", ".gemini", "brain", ".pytest_cache", ".mypy_cache", "build", "dist"}

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            p = Path(root) / fname
            total_files += 1
            rel_str = str(p.relative_to(target_path)).replace("\\", "/")

        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            scanned_py += 1

            # 1. Check Syntax
            try:
                ast.parse(content, filename=rel_str)
            except SyntaxError as syn_err:
                syntax_errors.append(f" - {rel_str}:{syn_err.lineno} — {syn_err.msg}")

            # 2. Check Unsafe Eval/Exec
            if not rel_str.endswith("audit_tools.py"):
                if re.search(r"\beval\s*\(", content):
                    security_findings.append(f" - {rel_str} → Usage of eval()")
                if re.search(r"\bexec\s*\(", content):
                    security_findings.append(f" - {rel_str} → Usage of exec()")

            # 3. Check Hardcoded API Keys / Passwords
            if re.search(
                r"""(?:api[_-]?key|secret|password)\s*=\s*['"][a-zA-Z0-9_\-]{20,}['"]""", content, re.IGNORECASE
            ):
                security_findings.append(f" - {rel_str} → Possible hardcoded API key or secret token")

        except Exception as e:
            logger.debug("Suppressed exception: %s", e)
    status_str = "🟢 CLEAN" if not syntax_errors and not security_findings else "⚠️ ISSUES DETECTED"

    report = [
        f"🛡️ CODEBASE SECURITY & QUALITY AUDIT REPORT ({status_str})",
        f" - Scanned Python Files: {scanned_py} files",
        f" - Syntax Errors: {len(syntax_errors)}",
        f" - Security Findings: {len(security_findings)}",
    ]

    if syntax_errors:
        report.append("\n❌ SYNTAX ERRORS:")
        report.extend(syntax_errors[:5])

    if security_findings:
        report.append("\n⚠️ SECURITY & CODE QUALITY FINDINGS:")
        report.extend(security_findings[:10])

    if not syntax_errors and not security_findings:
        report.append("\n✅ All scanned Python files passed AST compilation and security pattern checks.")

    return "\n".join(report)
