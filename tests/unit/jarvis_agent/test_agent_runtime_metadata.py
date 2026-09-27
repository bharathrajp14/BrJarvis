from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.agent import (
    AgentLoop,
    AgentSession,
    AgentTurnStatus,
    parse_tool_calls,
)
from jarvis.gateway import ModelGateway, ModelRequest, ModelResponse
from jarvis.gateway.adapters.base import BaseAdapter
from jarvis.memory import Database, TaskRepository, initialize_database
from jarvis.tools import (
    ToolContext,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
    ToolResult,
    ToolRiskLevel,
    ToolRuntime,
)


class MultiTurnFakeAdapter(BaseAdapter):
    def __init__(self, responses: list[str]) -> None:
        super().__init__(
            provider="fake",
            default_model="fake-gpt4",
            models=frozenset({"fake-gpt4"}),
            capabilities=frozenset({"chat"}),
        )
        self.responses = list(responses)
        self.call_idx = 0

    @property
    def available(self) -> bool:
        return True

    def generate(self, request: ModelRequest) -> ModelResponse:
        idx = min(self.call_idx, len(self.responses) - 1)
        resp_text = self.responses[idx]
        self.call_idx += 1
        return ModelResponse(text=resp_text, provider="fake", model="fake-gpt4")

    def stream(self, request: ModelRequest):
        yield self.generate(request).text


def test_parse_multiple_tool_calls() -> None:
    text = (
        "I will list files and check status.\n"
        '```tool_call\n{"tool": "file_list", "args": {"path": "."}}\n```\n'
        "and also\n"
        '```tool_call\n{"tool": "system_info", "args": {}}\n```'
    )
    calls = parse_tool_calls(text)
    assert len(calls) == 2
    assert calls[0][0] == "file_list"
    assert calls[0][1] == {"path": "."}
    assert calls[1][0] == "system_info"
    assert calls[1][1] == {}


def test_agent_loop_with_tool_runtime_and_task_repo(tmp_path: Path) -> None:
    # 1. Setup SQLite TaskRepository
    db = Database(tmp_path / "test_run.db")
    initialize_database(db)
    task_repo = TaskRepository(db)

    # 2. Setup ToolRuntime with a custom tool
    registry = ToolRegistry()
    test_tool = ToolDefinition(
        name="generate_report",
        description="Generates a report file",
        parameters=[ToolParameter("title", "string", "Report title", required=True)],
        risk_level=ToolRiskLevel.LOW_RISK_WRITE,
    )

    def _handler(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
        file_path = str(tmp_path / "report.md")
        Path(file_path).write_text(f"# {args['title']}\nAll systems verified.", encoding="utf-8")
        return ToolResult.ok(
            output=f"Report created at {file_path}",
            evidence="File verified on disk",
            artifacts=[file_path],
        )

    registry.register(test_tool, _handler)
    runtime = ToolRuntime(registry=registry, default_workspace=tmp_path)

    # 3. Model adapter simulating tool call then final answer
    model_adapter = MultiTurnFakeAdapter(
        [
            '```tool_call\n{"tool": "generate_report", "args": {"title": "Annual System Audit"}}\n```',
            "The report has been successfully generated and verified on disk.",
        ]
    )
    gateway = ModelGateway({"fake": model_adapter})

    # 4. Execute AgentLoop
    session = AgentSession(session_id="sess_metadata_test")
    loop = AgentLoop(
        session=session,
        gateway=gateway,
        tool_runtime=runtime,
        task_repository=task_repo,
    )

    result = loop.run_turn("Audit the current system state and save a report.")

    assert result.status == AgentTurnStatus.SUCCESS_VERIFIED
    assert result.verified is True
    assert len(result.artifacts) == 1
    assert result.artifacts[0].endswith("report.md")
    assert "Annual System Audit" in Path(result.artifacts[0]).read_text(encoding="utf-8")

    # 5. Verify Section 3 Mandated Run Metadata
    meta = result.metadata
    assert meta["run_id"].startswith("turn_")
    assert meta["task_id"].startswith("task_")
    assert meta["session_id"] == "sess_metadata_test"
    assert meta["agent_id"] == "jarvis_canonical_agent"
    assert meta["model_id"] == "fake-gpt4"
    assert meta["status"] == "success_verified"
    assert meta["current_step"] == 2
    assert meta["tool_calls"] == 1
    assert meta["verification_state"] == "VERIFIED"
    assert meta["provenance"] == "canonical_agent_loop"

    # 6. Verify task survived into SQLite
    persisted_task = task_repo.get_task(meta["task_id"])
    assert persisted_task is not None
    assert persisted_task.status.value == "completed"
    assert persisted_task.current_step == 2
