# tests/unit/test_canonical_agent_loop.py — Unit Tests for Canonical AgentLoop
from __future__ import annotations

from types import SimpleNamespace

from brjarvis.agent.agent_loop import AgentLoop, AgentTurnStatus
from brjarvis.agent.session import AgentSession

from brjarvis.events.bus import get_event_bus


class MockRouter:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0

    def run(self, profile, history, system_prompt):
        resp = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return resp


class FailingRouter:
    def run(self, profile, history, system_prompt):
        raise TimeoutError("provider deadline exceeded")


class MockGateway:
    def __init__(self, text: str = "canonical response") -> None:
        self.text = text
        self.calls = []

    def generate(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        return SimpleNamespace(text=self.text)


class TestCanonicalAgentLoop:

    """Test suite for AgentLoop execution, verification, and event emission."""

    def test_canonical_gateway_is_used_before_legacy_router(self, monkeypatch):
        sess = AgentSession(session_id="test-loop-canonical-gateway")
        gateway = MockGateway()
        loop = AgentLoop(session=sess, gateway=gateway)
        loop.discover_context = lambda _prompt: ""
        monkeypatch.setattr("brjarvis.agent.agent_loop.DeterministicIntentEngine.parse_and_execute", lambda _text: None)

        result = loop.run_turn("build a gateway integration", router=MockRouter(["legacy response"]))

        assert result == "canonical response"
        assert len(gateway.calls) == 1
        assert gateway.calls[0][1]["capability"] == "code"

    def test_fast_path_execution(self):

        sess = AgentSession(session_id="test-loop-fast")
        loop = AgentLoop(session=sess)

        # "open chrome" or volume commands trigger fast path
        res = loop.run_turn("volume up")
        assert res is not None
        assert len(sess.turns) >= 2
        assert sess.turns[-1].role == "assistant"

    def test_react_turn_with_tool_call(self):
        sess = AgentSession(session_id="test-loop-react")
        loop = AgentLoop(session=sess)

        # Mock router that calls file_read then gives response
        mock_router = MockRouter(
            [
                '```tool_call\n{"tool": "file_read", "args": {"path": "readme.md"}}\n```',
                "I read the readme file and found project details.",
            ]
        )

        events_received = []
        bus = get_event_bus()

        def _handler(ev):
            events_received.append(ev.topic)

        bus.subscribe("agent.*", _handler)
        bus.subscribe("tool.*", _handler)
        bus.subscribe("verification.*", _handler)

        res = loop.run_turn("Read the readme file", router=mock_router)

        assert "read the readme" in res.lower() or "completed" in res.lower() or len(res) > 0
        assert len(sess.tool_history) >= 1
        assert sess.tool_history[0]["tool_name"] == "file_read"
        assert len(sess.turns) == 2

        # Verify event stream
        assert "agent.started" in events_received
        assert "agent.completed" in events_received
        assert "tool.started" in events_received

    def test_action_verification(self, tmp_path):
        sess = AgentSession(session_id="test-loop-ver")
        loop = AgentLoop(session=sess)

        test_file = tmp_path / "verified_output.txt"
        test_file.write_text("JARVIS verified content", encoding="utf-8")

        verified, evidence = loop.verify_action("file_write", {"path": str(test_file)}, "Created")
        assert verified is True
        assert "verified" in evidence.lower() or "created" in evidence.lower()

        # Non-existent file
        verified_missing, err_msg = loop.verify_action("file_write", {"path": str(tmp_path / "missing.txt")}, "Created")
        assert verified_missing is False
        assert "does not exist" in err_msg.lower() or "failed" in err_msg.lower()

    def test_backend_failure_emits_failed_terminal_result(self):
        sess = AgentSession(session_id="test-loop-backend-failure")
        loop = AgentLoop(session=sess)
        events_received = []
        bus = get_event_bus()

        def _handler(ev):
            events_received.append(ev.topic)

        bus.subscribe("agent.*", _handler)
        result = loop.run_turn_result("Perform a complex provider task", router=FailingRouter())

        assert result.status == AgentTurnStatus.FAILED
        assert result.verified is False
        assert "provider deadline exceeded" in result.error
        assert "agent.failed" in events_received
        assert "agent.completed" not in events_received
        assert sess.active_task_id is None
