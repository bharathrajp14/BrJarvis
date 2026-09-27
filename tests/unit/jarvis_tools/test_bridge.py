from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.tools import (
    LegacyToolBridge,
    ToolContext,
    ToolRegistry,
    ToolRiskLevel,
    ToolRuntime,
    bridge_legacy_tools,
)
from jarvis.tools.bridge import map_legacy_risk_level, parse_json_schema_parameters


def test_map_legacy_risk_level() -> None:
    assert map_legacy_risk_level("low", is_read_only=True) == ToolRiskLevel.READ_ONLY
    assert map_legacy_risk_level("read_only") == ToolRiskLevel.READ_ONLY
    assert map_legacy_risk_level("low", is_read_only=False) == ToolRiskLevel.LOW_RISK_WRITE
    assert map_legacy_risk_level("medium") == ToolRiskLevel.LOW_RISK_WRITE
    assert map_legacy_risk_level("high") == ToolRiskLevel.HIGH_RISK_WRITE
    assert map_legacy_risk_level("critical") == ToolRiskLevel.DESTRUCTIVE

    # Name-based risk cues
    assert map_legacy_risk_level("high", name="delete_file") == ToolRiskLevel.DESTRUCTIVE
    assert map_legacy_risk_level("high", name="purge_cache") == ToolRiskLevel.DESTRUCTIVE
    assert map_legacy_risk_level("high", name="get_auth_token") == ToolRiskLevel.CREDENTIAL_ACCESS
    assert map_legacy_risk_level("high", name="send_telegram_msg") == ToolRiskLevel.EXTERNAL_COMMUNICATION
    assert map_legacy_risk_level("high", name="kill_process") == ToolRiskLevel.SYSTEM_CONTROL


def test_parse_json_schema_parameters() -> None:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target file path"},
            "count": {"type": "integer", "description": "Item count", "default": 10},
        },
        "required": ["path"],
    }
    params = parse_json_schema_parameters(schema)
    assert len(params) == 2

    p_map = {p.name: p for p in params}
    assert p_map["path"].required is True
    assert p_map["path"].type_name == "string"
    assert p_map["path"].description == "Target file path"

    assert p_map["count"].required is False
    assert p_map["count"].type_name == "integer"
    assert p_map["count"].default == 10

    # Handles empty / None
    assert parse_json_schema_parameters(None) == []
    assert parse_json_schema_parameters({}) == []


def test_bridge_legacy_file_tool(tmp_path: Path) -> None:
    registry = ToolRegistry()
    bridge = LegacyToolBridge(registry=registry)

    defn = bridge.bridge_tool("file_list")
    assert defn is not None
    assert defn.name == "file_list"
    assert defn.risk_level == ToolRiskLevel.READ_ONLY

    # Execute through canonical runtime
    runtime = ToolRuntime(registry=registry, default_workspace=tmp_path)
    ctx = ToolContext(workspace_dir=tmp_path, task_id="task-test-bridge")

    res = runtime.execute("file_list", {"path": "."}, context=ctx)
    assert res.is_success is True
    assert isinstance(res.output, list)
    assert len(res.evidence) > 0
    assert res.execution_ms >= 0


def test_bridge_error_containment(tmp_path: Path) -> None:
    from brjarvis.tools.registry import register_tool

    # Register an intentionally failing tool into brjarvis
    @register_tool(
        name="test_crashing_tool",
        description="A tool that throws an unexpected error",
        parameters={
            "type": "object",
            "properties": {"arg": {"type": "string"}},
            "required": [],
        },
        risk_level="low",
    )
    def _crash_tool(args: dict) -> Any:
        raise ValueError("Simulated unexpected crash in legacy tool")

    registry = ToolRegistry()
    bridge = LegacyToolBridge(registry=registry)

    defn = bridge.bridge_tool("test_crashing_tool")
    assert defn is not None

    runtime = ToolRuntime(registry=registry, default_workspace=tmp_path)
    res = runtime.execute("test_crashing_tool", {})
    assert res.is_success is False
    assert "Simulated unexpected crash" in res.error or "Tool execution failed" in res.error
    assert res.execution_ms >= 0


def test_bridge_tools_batch() -> None:
    registry = ToolRegistry()
    bridged = bridge_legacy_tools(registry=registry, names=["file_read", "file_list"])
    assert len(bridged) == 2
    names = [d.name for d in bridged]
    assert "file_read" in names
    assert "file_list" in names
    assert registry.get("file_read") is not None
    assert registry.get("file_list") is not None
