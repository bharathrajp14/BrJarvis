from __future__ import annotations

from pathlib import Path

from jarvis.tools import (
    ToolContext,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
    ToolResult,
    ToolRiskLevel,
    ToolRuntime,
    register_default_tools,
)


def test_tool_result_contracts() -> None:
    ok_res = ToolResult.ok("payload", evidence="completed successfully")
    assert ok_res.is_success is True
    assert ok_res.output == "payload"
    assert ok_res.error == ""

    err_res = ToolResult.err("disk failure")
    assert err_res.is_success is False
    assert "disk failure" in err_res.error
    assert err_res.output is None


def test_tool_registry_and_prompt_catalog() -> None:
    registry = ToolRegistry()
    defn = ToolDefinition(
        name="test_echo",
        description="Echo input text",
        parameters=[ToolParameter("message", "string", "Text to echo", required=True)],
        risk_level=ToolRiskLevel.LOW,
    )

    def handler(ctx: ToolContext, args: dict) -> ToolResult:
        return ToolResult.ok(args.get("message"))

    registry.register(defn, handler)
    assert len(registry.list_tools()) == 1
    entry = registry.get("test_echo")
    assert entry is not None
    assert entry[0].name == "test_echo"

    catalog = registry.export_prompt_catalog()
    assert "test_echo" in catalog
    assert "Echo input text" in catalog


def test_tool_runtime_execution_and_error_containment(tmp_path: Path) -> None:
    registry = ToolRegistry()
    runtime = ToolRuntime(registry=registry, default_workspace=tmp_path)

    # Tool not found
    res = runtime.execute("non_existent_tool", {})
    assert res.is_success is False
    assert "not recognized" in res.error

    # Missing required argument
    defn = ToolDefinition(
        name="divide",
        description="Divide numbers",
        parameters=[
            ToolParameter("a", "number", "numerator", required=True),
            ToolParameter("b", "number", "denominator", required=True),
        ],
    )

    def divide_handler(ctx: ToolContext, args: dict) -> ToolResult:
        denom = float(args["b"])
        if denom == 0:
            return ToolResult.err("Division by zero")
        return ToolResult.ok(float(args["a"]) / denom)

    registry.register(defn, divide_handler)

    missing_res = runtime.execute("divide", {"a": 10})
    assert missing_res.is_success is False
    assert "Missing required arguments" in missing_res.error

    # Normal success
    ok_res = runtime.execute("divide", {"a": 10, "b": 2})
    assert ok_res.is_success is True
    assert ok_res.output == 5.0

    # Handler error containment
    div_zero_res = runtime.execute("divide", {"a": 10, "b": 0})
    assert div_zero_res.is_success is False
    assert "Division by zero" in div_zero_res.error


def test_builtin_fs_tools(tmp_path: Path) -> None:
    registry = ToolRegistry()
    register_default_tools(registry)
    runtime = ToolRuntime(registry=registry, default_workspace=tmp_path)
    ctx = ToolContext(workspace_dir=tmp_path)

    # 1. Write file
    write_res = runtime.execute(
        "file_write",
        {"path": "sub/hello.txt", "content": "Hello Jarvis!"},
        context=ctx,
    )
    assert write_res.is_success is True

    # 2. Read file
    read_res = runtime.execute(
        "file_read",
        {"path": "sub/hello.txt"},
        context=ctx,
    )
    assert read_res.is_success is True
    assert read_res.output == "Hello Jarvis!"

    # 3. List directory
    list_res = runtime.execute(
        "file_list",
        {"path": "sub"},
        context=ctx,
    )
    assert list_res.is_success is True
    items = list_res.output
    assert len(items) == 1
    assert items[0]["name"] == "hello.txt"

    # 4. Path traversal escape rejection
    escape_res = runtime.execute(
        "file_read",
        {"path": "../../../outside.txt"},
        context=ctx,
    )
    assert escape_res.is_success is False
    assert "escapes workspace" in escape_res.error


def test_builtin_system_status(tmp_path: Path) -> None:
    registry = ToolRegistry()
    register_default_tools(registry)
    runtime = ToolRuntime(registry=registry, default_workspace=tmp_path)

    res = runtime.execute("system_status", {})
    assert res.is_success is True
    assert "platform" in res.output
    assert "python_version" in res.output
