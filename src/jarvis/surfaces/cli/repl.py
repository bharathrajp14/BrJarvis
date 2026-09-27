"""Interactive CLI REPL surface for JARVIS."""

from __future__ import annotations

from jarvis.agent.loop import AgentLoop
from jarvis.agent.session import get_or_create_session
from jarvis.core.bootstrap import build_assistant_runtime
from jarvis.core.version import CODENAME, VERSION
from jarvis.tools.builtin import register_default_tools
from jarvis.tools.registry import get_tool_registry
from jarvis.tools.runtime import ToolRuntime


def run_cli() -> None:
    """Launch interactive terminal REPL."""
    runtime = build_assistant_runtime()
    gateway = runtime.gateway

    registry = get_tool_registry()
    if not registry.list_tools():
        register_default_tools(registry)

    tool_rt = ToolRuntime(registry=registry, default_workspace=runtime.layout.workspace_root)

    def tool_executor(tool_name: str, args: dict) -> tuple[str, bool]:
        res = tool_rt.execute(tool_name, args)
        return (res.output if res.is_success else res.error), res.is_success

    session = get_or_create_session("cli_session")
    loop = AgentLoop(session=session, gateway=gateway, tool_executor=tool_executor)

    print("\n=======================================================")
    print(f"       JARVIS {CODENAME} (v{VERSION}) — CLI Terminal       ")
    print("=======================================================")
    print("Commands: /status, /doctor, /tools, /mode <name>, /exit\n")

    while True:
        try:
            user_input = input(f"[{session.current_mode}] JARVIS > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting JARVIS CLI. Goodbye.")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in {"/exit", "/quit", "exit", "quit"}:
            print("Session terminated.")
            break

        if cmd == "/tools":
            print(registry.export_prompt_catalog())
            continue

        if cmd.startswith("/mode"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                session.current_mode = parts[1].strip()
                print(f"Switched mode to: {session.current_mode}")
            else:
                print(f"Current mode: {session.current_mode}")
            continue

        if cmd == "/doctor":
            report = runtime.doctor_report()
            print(f"Doctor Report: {report}")
            continue

        turn_result = loop.run_turn(user_input)
        print(f"\n{turn_result.response}\n")
        if turn_result.evidence:
            print(f"{turn_result.evidence}\n")
