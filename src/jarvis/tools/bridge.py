"""Bridge adapter connecting brjarvis tools to the canonical jarvis ToolRegistry."""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from typing import Any

from .contracts import (
    ToolContext,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    ToolRiskLevel,
)
from .registry import ToolRegistry, get_tool_registry

logger = logging.getLogger("jarvis.tools.bridge")


def map_legacy_risk_level(
    raw_risk: str | None,
    is_read_only: bool = False,
    name: str = "",
    category: str = "",
) -> ToolRiskLevel:
    """Map legacy string / enum risk levels and category cues to canonical ToolRiskLevel."""
    if is_read_only or raw_risk == "read_only":
        return ToolRiskLevel.READ_ONLY

    raw = (raw_risk or "").lower().strip()
    name_lower = name.lower()
    cat_lower = category.lower()

    if any(k in name_lower for k in ("delete", "destroy", "drop", "purge", "trash")) or raw == "destructive":
        return ToolRiskLevel.DESTRUCTIVE

    if (
        any(k in name_lower for k in ("token", "secret", "credential", "auth", "key", "password"))
        or raw == "credential_access"
    ):
        return ToolRiskLevel.CREDENTIAL_ACCESS

    if (
        any(k in name_lower for k in ("shutdown", "reboot", "kill", "restart", "system_control"))
        or raw == "system_control"
    ):
        return ToolRiskLevel.SYSTEM_CONTROL

    if (
        any(k in name_lower for k in ("email", "telegram", "whatsapp", "sms", "tweet", "message"))
        or cat_lower == "communication"
        or raw == "external_communication"
    ):
        return ToolRiskLevel.EXTERNAL_COMMUNICATION

    if raw == "critical":
        return ToolRiskLevel.DESTRUCTIVE
    if raw == "high":
        return ToolRiskLevel.HIGH_RISK_WRITE
    if raw in {"low", "low_risk_write", "medium"}:
        return ToolRiskLevel.LOW_RISK_WRITE

    return ToolRiskLevel.LOW_RISK_WRITE


def parse_json_schema_parameters(parameters: dict[str, Any] | None) -> list[ToolParameter]:
    """Parse JSON schema dict into structured ToolParameter list."""
    if not parameters or not isinstance(parameters, dict):
        return []

    properties = parameters.get("properties", {})
    if not isinstance(properties, dict):
        return []

    required_set = set(parameters.get("required", [])) if isinstance(parameters.get("required"), list) else set()
    result: list[ToolParameter] = []

    for param_name, spec in properties.items():
        if not isinstance(spec, dict):
            result.append(
                ToolParameter(
                    name=param_name,
                    type_name="string",
                    description="",
                    required=param_name in required_set,
                    default=None,
                )
            )
            continue

        result.append(
            ToolParameter(
                name=param_name,
                type_name=str(spec.get("type", "string")),
                description=str(spec.get("description", "")),
                required=param_name in required_set,
                default=spec.get("default"),
            )
        )

    return result


class LegacyToolBridge:
    """Adapter bridging legacy brjarvis tool implementations into canonical jarvis ToolRegistry."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or get_tool_registry()

    def bridge_tool(self, name: str) -> ToolDefinition | None:
        """Inspect and register a legacy tool by name into the canonical registry."""
        try:
            from brjarvis.tools.registry import (
                TOOL_REGISTRY,
                TOOL_SCHEMAS,
                _import_plugins,
                execute_tool_raw,
            )
            from brjarvis.tools.runtime import get_canonical_tool_runtime
        except ImportError as exc:
            logger.warning("brjarvis tools subsystem is unavailable for bridging: %s", exc)
            return None

        # 1. Trigger plugin discovery if tool is not yet loaded
        if name not in TOOL_REGISTRY:
            try:
                _import_plugins(full=False)
            except Exception as exc:
                logger.debug("Core plugin import notice: %s", exc)

        # 2. Check if registered in ToolRuntime catalog or TOOL_REGISTRY
        br_runtime = get_canonical_tool_runtime()
        legacy_defn = br_runtime.get_tool_definition(name)
        raw_handler = TOOL_REGISTRY.get(name)

        if legacy_defn is None and raw_handler is None:
            logger.debug("Tool '%s' not found in brjarvis catalog or registry.", name)
            return None

        # 3. Extract metadata
        schema = next((s for s in TOOL_SCHEMAS if s.get("name") == name), {})
        desc = (
            getattr(legacy_defn, "description", None)
            or schema.get("description")
            or getattr(raw_handler, "__doc__", "")
            or f"Legacy tool {name}"
        ).strip()

        params_schema = getattr(legacy_defn, "parameters", None) or schema.get("parameters") or {}
        parameters = parse_json_schema_parameters(params_schema)

        raw_risk = getattr(legacy_defn, "risk_level", None)
        raw_risk_val = raw_risk.value if hasattr(raw_risk, "value") else str(raw_risk or "")
        is_read_only = bool(getattr(legacy_defn, "is_read_only", False) or schema.get("is_read_only", False))
        category = str(getattr(getattr(legacy_defn, "category", None), "value", schema.get("category", "")))

        risk_level = map_legacy_risk_level(
            raw_risk=raw_risk_val,
            is_read_only=is_read_only,
            name=name,
            category=category,
        )

        canonical_defn = ToolDefinition(
            name=name,
            description=desc,
            parameters=parameters,
            risk_level=risk_level,
            capabilities=frozenset({category} if category else set()),
        )

        # 4. Construct execution wrapper
        def wrapped_handler(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
            t0 = time.monotonic()
            try:
                legacy_res = execute_tool_raw(
                    name=name,
                    args=args,
                    task_id=ctx.task_id,
                    step_id=ctx.correlation_id,
                    confirmed=ctx.approved,
                )

                elapsed = int((time.monotonic() - t0) * 1000)

                # Case A: brjarvis.tools.tool_result.ToolResult
                if hasattr(legacy_res, "is_success"):
                    if legacy_res.is_success:
                        output_val = legacy_res.data
                        if output_val is None:
                            output_val = getattr(legacy_res, "output", None)
                        if output_val is None:
                            output_val = legacy_res.message or "Success"

                        raw_artifacts = getattr(legacy_res, "artifacts", [])
                        extracted_artifacts: list[str] = []
                        if isinstance(raw_artifacts, list):
                            for art in raw_artifacts:
                                if isinstance(art, str):
                                    extracted_artifacts.append(art)
                                elif isinstance(art, dict) and "path" in art:
                                    extracted_artifacts.append(str(art["path"]))
                                elif isinstance(art, dict) and "file" in art:
                                    extracted_artifacts.append(str(art["file"]))

                        return ToolResult.ok(
                            output=output_val,
                            evidence=str(legacy_res.evidence or output_val)[:300],
                            artifacts=extracted_artifacts,
                            execution_ms=max(elapsed, int(getattr(legacy_res, "execution_ms", 0))),
                            metadata=getattr(legacy_res, "metadata", {}),
                        )
                    else:
                        err_msg = legacy_res.message or str(getattr(legacy_res, "error_code", "Execution error"))
                        return ToolResult.err(
                            error=err_msg,
                            evidence=str(legacy_res.evidence or err_msg)[:300],
                            execution_ms=max(elapsed, int(getattr(legacy_res, "execution_ms", 0))),
                            metadata=getattr(legacy_res, "metadata", {}),
                        )

                # Case B: dict response
                if isinstance(legacy_res, dict):
                    if legacy_res.get("status") in {"error", "failed"} or "error" in legacy_res:
                        err_msg = str(legacy_res.get("error") or legacy_res.get("message") or "Unknown error")
                        return ToolResult.err(
                            error=err_msg,
                            evidence=f"Error in {name}: {err_msg}",
                            execution_ms=elapsed,
                            metadata=legacy_res,
                        )
                    return ToolResult.ok(
                        output=legacy_res,
                        evidence=f"Success response from {name}",
                        execution_ms=elapsed,
                        metadata=legacy_res,
                    )

                # Case C: generic primitive / string
                return ToolResult.ok(
                    output=legacy_res,
                    evidence=f"Result from {name}: {str(legacy_res)[:150]}",
                    execution_ms=elapsed,
                )

            except Exception as exc:
                elapsed = int((time.monotonic() - t0) * 1000)
                logger.error("Legacy bridge error for tool '%s': %s", name, exc, exc_info=True)
                return ToolResult.err(
                    error=f"Bridged execution failed: {type(exc).__name__} ({str(exc)[:120]})",
                    evidence=f"Tool error in {name}",
                    execution_ms=elapsed,
                )

        self.registry.register(canonical_defn, wrapped_handler)
        logger.debug("Successfully bridged legacy tool '%s' [%s]", name, risk_level.value)
        return canonical_defn

    def bridge_tools(self, names: Sequence[str]) -> list[ToolDefinition]:
        """Bridge a list of tools by name."""
        bridged: list[ToolDefinition] = []
        for name in names:
            defn = self.bridge_tool(name)
            if defn is not None:
                bridged.append(defn)
        return bridged

    def bridge_all(self, full_import: bool = False) -> list[ToolDefinition]:
        """Bridge all registered tools from brjarvis registry into canonical registry."""
        try:
            from brjarvis.tools.registry import TOOL_REGISTRY, _import_plugins

            _import_plugins(full=full_import)
            names = list(TOOL_REGISTRY.keys())
        except Exception as exc:
            logger.warning("Could not discover all legacy tools: %s", exc)
            return []

        return self.bridge_tools(names)


def bridge_legacy_tools(
    registry: ToolRegistry | None = None,
    names: Sequence[str] | None = None,
    full_import: bool = False,
) -> list[ToolDefinition]:
    """Convenience function to bridge legacy tools into the specified or global ToolRegistry."""
    bridge = LegacyToolBridge(registry=registry)
    if names is not None:
        return bridge.bridge_tools(names)
    return bridge.bridge_all(full_import=full_import)
