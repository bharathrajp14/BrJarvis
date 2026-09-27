"""Workspace-contained filesystem operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.tools.contracts import (
    ToolContext,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    ToolRiskLevel,
)
from jarvis.tools.registry import ToolRegistry


def _resolve_safe_path(base_dir: Path, requested_path: str | Path) -> Path:
    """Resolve and enforce that the requested path resides within base_dir."""
    p = Path(requested_path)
    if not p.is_absolute():
        p = (base_dir / p).resolve()
    else:
        p = p.resolve()

    try:
        p.relative_to(base_dir.resolve())
    except ValueError:
        raise PermissionError(f"Access denied: path '{requested_path}' escapes workspace '{base_dir}'")

    return p


def handle_file_read(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    """Read contents of a file within the workspace."""
    raw_path = args.get("path", "")
    max_bytes = int(args.get("max_bytes", 65536))
    try:
        safe_path = _resolve_safe_path(ctx.workspace_dir, raw_path)
        if not safe_path.exists():
            return ToolResult.err(f"File not found: {raw_path}")
        if not safe_path.is_file():
            return ToolResult.err(f"Path is not a regular file: {raw_path}")

        size = safe_path.stat().st_size
        text = safe_path.read_text(encoding="utf-8", errors="replace")[:max_bytes]
        evidence = f"Read {len(text)} characters from {raw_path} (total size: {size} bytes)"
        return ToolResult.ok(output=text, evidence=evidence, artifacts=[str(safe_path)])
    except PermissionError as pe:
        return ToolResult.err(str(pe))
    except Exception as exc:
        return ToolResult.err(f"Failed to read file: {exc}")


def handle_file_write(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    """Write text content to a file within the workspace."""
    raw_path = args.get("path", "")
    content = args.get("content", "")
    try:
        safe_path = _resolve_safe_path(ctx.workspace_dir, raw_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        evidence = f"Wrote {len(content)} characters to {raw_path}"
        return ToolResult.ok(output=f"Successfully wrote {raw_path}", evidence=evidence, artifacts=[str(safe_path)])
    except PermissionError as pe:
        return ToolResult.err(str(pe))
    except Exception as exc:
        return ToolResult.err(f"Failed to write file: {exc}")


def handle_file_list(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    """List entries inside a workspace directory."""
    raw_path = args.get("path", ".")
    try:
        safe_path = _resolve_safe_path(ctx.workspace_dir, raw_path)
        if not safe_path.exists():
            return ToolResult.err(f"Directory not found: {raw_path}")
        if not safe_path.is_dir():
            return ToolResult.err(f"Path is not a directory: {raw_path}")

        items: list[dict[str, Any]] = []
        for entry in safe_path.iterdir():
            items.append(
                {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else None,
                }
            )

        evidence = f"Listed {len(items)} items in {raw_path}"
        return ToolResult.ok(output=items, evidence=evidence)
    except PermissionError as pe:
        return ToolResult.err(str(pe))
    except Exception as exc:
        return ToolResult.err(f"Failed to list directory: {exc}")


def register_fs_tools(registry: ToolRegistry) -> None:
    """Register filesystem tools into the provided registry."""
    registry.register(
        ToolDefinition(
            name="file_read",
            description="Read text content from a file inside the project workspace.",
            parameters=[
                ToolParameter("path", "string", "Relative path to the file to read", required=True),
                ToolParameter("max_bytes", "integer", "Maximum bytes to read", required=False, default=65536),
            ],
            risk_level=ToolRiskLevel.LOW,
            capabilities=frozenset({"fs", "read"}),
        ),
        handle_file_read,
    )

    registry.register(
        ToolDefinition(
            name="file_write",
            description="Write text content to a file inside the project workspace.",
            parameters=[
                ToolParameter("path", "string", "Relative path to the destination file", required=True),
                ToolParameter("content", "string", "Text content to write", required=True),
            ],
            risk_level=ToolRiskLevel.MEDIUM,
            capabilities=frozenset({"fs", "write"}),
        ),
        handle_file_write,
    )

    registry.register(
        ToolDefinition(
            name="file_list",
            description="List files and directories within a workspace path.",
            parameters=[
                ToolParameter(
                    "path", "string", "Relative directory path (default: current)", required=False, default="."
                ),
            ],
            risk_level=ToolRiskLevel.LOW,
            capabilities=frozenset({"fs", "read"}),
        ),
        handle_file_list,
    )
