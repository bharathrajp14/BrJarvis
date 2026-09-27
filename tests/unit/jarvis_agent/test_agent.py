from __future__ import annotations

from pathlib import Path

from jarvis.agent import (
    AgentLoop,
    AgentSession,
    AgentTurnStatus,
    DecisionEngine,
    ExecutionLedger,
    FileVerifier,
    LedgerEntry,
    LedgerStatus,
    ProcessVerifier,
    TaskState,
    TaskStatus,
    clean_response_text,
    parse_tool_call,
)
from jarvis.gateway import (
    ModelGateway,
    ModelRequest,
    ModelResponse,
)
from jarvis.gateway.adapters.base import BaseAdapter


class FakeModelAdapter(BaseAdapter):
    def __init__(self, responses: list[str]) -> None:
        super().__init__(
            provider="fake",
            default_model="fake-model",
            models=frozenset({"fake-model"}),
            capabilities=frozenset({"chat"}),
        )
        self.responses = list(responses)
        self.call_count = 0

    @property
    def available(self) -> bool:
        return True

    def generate(self, request: ModelRequest) -> ModelResponse:
        resp = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return ModelResponse(text=resp, provider="fake", model="fake-model")

    def stream(self, request: ModelRequest):
        yield self.generate(request).text


def test_task_state_revision_and_transitions() -> None:
    state = TaskState(task_id="task_123", user_request="Build new feature")
    assert state.revision == 0
    assert state.status == TaskStatus.CREATED

    state.advance_step({"detail": "inspecting codebase"})
    assert state.current_step == 1

    state.transition(TaskStatus.RUNNING, "Starting execution")
    assert state.status == TaskStatus.RUNNING

    cp = state.create_checkpoint("before_tools")
    assert cp["checkpoint_id"] == "cp_1"

    d = state.to_dict()
    restored = TaskState.from_dict(d)
    assert restored.task_id == "task_123"
    assert restored.status == TaskStatus.RUNNING
    assert restored.current_step == 1
    assert len(restored.checkpoints) == 1


def test_execution_ledger_evidence_report() -> None:
    ledger = ExecutionLedger()
    entry1 = LedgerEntry(
        task_id="t1",
        step_id="step_1",
        tool_name="file_read",
        status=LedgerStatus.SUCCESS,
        evidence="Read 42 lines",
        verification_status=LedgerStatus.SUCCESS,
    )
    entry2 = LedgerEntry(
        task_id="t1",
        step_id="step_2",
        tool_name="file_write",
        status=LedgerStatus.FAILED,
        evidence="Permission denied",
        verification_status=LedgerStatus.FAILED,
    )
    ledger.append(entry1)
    ledger.append(entry2)

    assert ledger.step_is_verified("t1", "step_1") is True
    assert ledger.step_is_verified("t1", "step_2") is False

    report = ledger.build_evidence_report("t1")
    assert "✓ **step_1** (`file_read`)" in report
    assert "✗ **step_2** (`file_write`)" in report


def test_decision_engine_receipts_and_guards() -> None:
    engine = DecisionEngine()
    dec = engine.record_decision(
        question="Which database to use?",
        goal="Thread-safe persistent storage",
        selected_option="SQLite WAL",
        rejected_options=["Multi-file JSON", "Uncoordinated SQLite instances"],
        evidence="ACID guarantees and concurrent reader performance",
    )

    receipt = dec.to_receipt()
    assert receipt["selected_option"] == "SQLite WAL"
    assert "Multi-file JSON" in receipt["rejected_options"]

    valid, _ = engine.validate_action_against_decisions("Set up SQLite WAL database")
    assert valid is True

    invalid, reason = engine.validate_action_against_decisions("Use Multi-file JSON for storage")
    assert invalid is False
    assert "conflicts with Decision" in reason


def test_verifiers(tmp_path: Path) -> None:
    test_file = tmp_path / "hello.txt"
    assert FileVerifier.verify_exists(test_file).verified is False

    test_file.write_text("Hello, JARVIS!", encoding="utf-8")
    assert FileVerifier.verify_exists(test_file).verified is True
    assert FileVerifier.verify_non_empty(test_file).verified is True
    assert FileVerifier.verify_contains(test_file, "Hello").verified is True
    assert FileVerifier.verify_contains(test_file, "Goodbye").verified is False

    assert ProcessVerifier.verify_exit_code(0).verified is True
    assert ProcessVerifier.verify_exit_code(1).verified is False


def test_tool_call_parsing_and_sanitization() -> None:
    fenced = """I will read the file now.
```tool_call
{"tool": "file_read", "args": {"path": "main.py"}}
```
Waiting for result."""
    name, args = parse_tool_call(fenced)
    assert name == "file_read"
    assert args == {"path": "main.py"}
    assert "file_read" not in clean_response_text(fenced)

    inline = '{"tool": "calculate", "args": {"x": 5}}'
    name2, args2 = parse_tool_call(inline)
    assert name2 == "calculate"
    assert args2 == {"x": 5}


def test_agent_loop_deterministic_status() -> None:
    loop = AgentLoop()
    result = loop.run_turn("status")
    assert result.status == AgentTurnStatus.SUCCESS_VERIFIED
    assert "System status: OK" in result.response


def test_agent_loop_with_tool_execution() -> None:
    # Model returns a tool call on turn 1, then a final text on turn 2
    tool_call_response = '```tool_call\n{"tool": "file_read", "args": {"path": "config.yaml"}}\n```'
    final_response = "The file was successfully read and contains port 8000."

    adapter = FakeModelAdapter([tool_call_response, final_response])
    gateway = ModelGateway({"fake": adapter})

    def mock_executor(tool: str, args: dict) -> tuple[str, bool]:
        return f"Contents of {args.get('path')}: port=8000", True

    sess = AgentSession()
    loop = AgentLoop(session=sess, gateway=gateway, tool_executor=mock_executor)

    res = loop.run_turn("Read the configuration file")

    assert res.status == AgentTurnStatus.SUCCESS_VERIFIED
    assert "port 8000" in res.response
    assert res.tool_failures == 0
    assert "file_read" in res.evidence
    assert len(sess.history) >= 3  # user, tool, assistant
