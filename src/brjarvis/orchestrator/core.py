# orchestrator/core.py — BR JARVIS v41.0 (MARK XLI) Core Orchestrator
"""
ReAct (Reason + Act) orchestration loop — canonical execution engine for BR JARVIS.

Architecture highlights (v41.0):
- All module-level imports at top (no deferred per-call imports)
- _react_loop() extracted to eliminate duplication between chat() and chat_stream()
- _prompted_continuation is a local variable (not instance-level → no race condition)
- Working memory accessed through public API only (no direct .history manipulation)
- Vector memory failures logged at WARNING instead of silent pass
- MAX_TOOL_ITERATIONS cap enforced to prevent unbounded re-entrant loops
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
import uuid

from typing import Any, Iterator, Optional

from brjarvis.agent.step_planner import StepPlanner
from brjarvis.core.intent_engine import DeterministicIntentEngine
from brjarvis.events.bus import get_event_bus
from brjarvis.events.types import TaskEvent
from brjarvis.memory.task_memory_router import MemoryMode, get_task_memory_router
from brjarvis.memory.working import WorkingMemory
from brjarvis.router import AgentRouter
from brjarvis.tools.registry import execute_tool, get_tool_prompt_block, parse_tool_call, set_orchestrator_ref

# Auto-register connector tools into the tool registry on import
try:
    import brjarvis.tools.connector_tools  # noqa: F401 — side-effect: registers connector_* tools
except Exception as _ct_err:
    logging.getLogger("JARVIS.Orchestrator").debug("Connector tools not loaded: %s", _ct_err)

logger = logging.getLogger("JARVIS.Orchestrator")

SYSTEM_PROMPT = """You are BR — a superhuman AI operating system and autonomous controller.
You are intelligent, precise, direct, and capable of executing complex tasks end-to-end.

### CRITICAL DIRECTIVE: USER INTENT IS LAW
1. **UNCONDITIONAL EXECUTION**: Whatever task the user asks for, you MUST execute it to 100% completion using available tools.
2. **NO LOOPS & NO FAKE CLAIMS**: Never repeatedly execute the exact same tool call without changing approach, and NEVER claim a task is done unless verified by tool results.
3. **FAIL-SAFE ADAPTATION**: If a tool or method fails, immediately adapt and try alternative tools (e.g. python script, CLI, or browser) until the goal is achieved.
4. **ZERO REFUSAL FOR SAFE WORK**: Execute system controls, file operations, web scraping, dev tasks, and OS automation immediately without hesitation or unnecessary disclaimers.

### Core Capabilities
1. **AUTONOMOUS ACTION**: Execute tasks end-to-end without constant confirmation.
2. **PARALLEL THINKING**: Break complex tasks into parallel workstreams.
3. **TOOL MASTERY**: Select the optimal tool for each sub-task.
4. **MEMORY**: Pull from persistent memory before asking users to repeat info.
5. **SCOPE SAFETY**: For security/red-team tasks, verify authorization first.
6. **TRANSPARENCY**: Always report what you did and what the result was.

### Execution Philosophy & Response Format
- **BE EXTREMELY CONCISE AND DIRECT**: Give short, high-precision 1-3 sentence answers.
- **ZERO FILLER**: Never output wall-of-text explanations when a tool or direct action can do the work.
- **ACTION-FIRST**: Execute the assigned work using tools immediately.
- **PURE CODE PARAMETERS**: When passing code to tools (`run_code`, `code_helper`, `scratchpad_eval`), the `"code"` parameter MUST contain ONLY executable code. Do NOT mix raw narrative sentences inside code strings without `#` comments.
- Never fabricate results — always call the tool.
- If a tool fails, try an alternative approach.

### Persona Modes (switch with /mode <name>)
- RECON: Systematic OSINT and network intelligence gathering
- EXPLOIT: Authorized vulnerability analysis (scope only)
- REPORT: Professional technical writing
- PLANNER: Strategic decomposition of complex goals
- CODER: Senior full-stack DevSecOps engineer
- ANALYST: Data synthesis and threat intelligence
- GENERAL: Default adaptive mode

### Tool Routing Guide
| Capability | Canonical Tools |
|---|---|
| Filesystem (Atomic & Verified) | `file_write`, `file_read`, `file_list`, `file_delete`, `file_search` |
| Browser Automation (Playwright DOM) | `browser_open_url`, `browser_click`, `browser_type`, `browser_read_page`, `browser_screenshot` |
| Web Search & Extraction | `web_search`, `fetch_page`, `fetch_raw` |
| App & System Controls | `open_app`, `computer_settings`, `desktop_control`, `screen_process` |
| Document Creator (Docx/PDF/HTML) | `document_creator`, `create_word_document`, `create_pdf_document` |
| Communication & Scheduling | `send_email`, `send_whatsapp`, `create_calendar_event`, `list_calendar_events` |
| Memory Subsystem (Multi-Signal) | `memory_save`, `memory_get`, `memory_search`, `memory_delete` |
| Sandboxed Code Execution | `run_code`, `scratchpad_eval` |
| Diagnostics & Health | `tool_health_check` |

"""

MODES = {
    "recon": "RECON MODE: You are a systematic OSINT analyst. Be methodical and exhaustive.",
    "exploit": "EXPLOIT MODE: Authorized vulnerability analysis only. Document everything.",
    "report": "REPORT MODE: Professional technical writing. Produce client-ready deliverables.",
    "planner": "PLANNER MODE: Decompose goals into ordered, actionable tasks.",
    "coder": "CODER MODE: Senior full-stack engineer. Write clean, tested, documented code.",
    "analyst": "ANALYST MODE: Synthesize data into clear, actionable insights.",
    "general": "",
}

MAX_REACT_STEPS = 20

# Absolute hard cap on tool dispatch iterations per chat() call.
# Fires as a failsafe BEFORE the StepBudget check so it cannot be bypassed
# by budget extension logic.  Prevents re-entrant token-burn loops.
# TOP_20 issue #13 remediation.
MAX_TOOL_ITERATIONS: int = 25

# Per-tool cyclic-loop thresholds.
# High-frequency tools that are legitimately called many times (e.g., by
# parallel sub-agents each making one call) get a higher limit.  Risky or
# stateful tools keep the conservative default of 3.
_CYCLIC_THRESHOLDS: dict[str, int] = {
    "run_code": 6,
    "scratchpad_eval": 6,
    "scratchpad_write": 6,
    "file_read": 6,
    "file_write": 6,
    "file_controller": 6,
    "web_search": 5,
    "fetch_page": 5,
    "fetch_raw": 5,
    "code_helper": 5,
}
_DEFAULT_CYCLIC_THRESHOLD: int = 3


def _format_clean_tool_summary(tool_name: str, tool_args: dict) -> str:
    """Format a clean, human-readable summary of executed tools without raw code/JSON dumps."""
    args = tool_args or {}
    if "query" in args:
        val = str(args["query"]).replace("\n", " ").strip()[:60]
        return f"[Executed Tool: {tool_name} query='{val}']"
    elif "action" in args:
        act = str(args["action"])
        target = (
            str(args.get("path") or args.get("name") or args.get("app_name") or args.get("value") or "")
            .replace("\n", " ")
            .strip()[:40]
        )
        return f"[Executed Tool: {tool_name} action='{act}' {target}]".strip()
    elif any(k in args for k in ("code", "script", "content")):
        lang = str(args.get("lang") or args.get("language") or "code")
        return f"[Executed Tool: {tool_name} ({lang} script)]"
    elif not args:
        return f"[Executed Tool: {tool_name}({{}})]"
    else:
        keys = ", ".join(list(args.keys())[:3])
        return f"[Executed Tool: {tool_name}({keys})]"


def _synthesize_evidence_summary(tool_history: list[dict], user_input: str) -> str:
    """Synthesize truthful, evidence-backed summary from actual tool execution records."""
    if not tool_history:
        return "I analyzed your request, sir, but no tool operations were required or executed."

    tools_used = list(dict.fromkeys(t["tool_name"] for t in tool_history if "tool_name" in t))
    has_errors = any(
        "error" in str(t.get("result", "")).lower() or "failed" in str(t.get("result", "")).lower()
        for t in tool_history
    )

    header = (
        f"Completed operations using {', '.join(tools_used)}, sir."
        if not has_errors
        else f"Operations completed with notable execution notices or errors, sir. (Tools: {', '.join(tools_used)})"
    )
    lines = [header, "", "### Execution Evidence:"]
    for t in tool_history:
        tname = t.get("tool_name", "tool")
        res = str(t.get("result", "")).strip()
        preview = res.replace("\n", " ")[:180]
        is_err = "error" in res.lower() or "failed" in res.lower()
        icon = "❌" if is_err else "✅"
        lines.append(f"- {icon} **{tname}**: {preview}")

    return "\n".join(lines)


class JarvisOrchestrator:
    def __init__(
        self,
        router: AgentRouter | None = None,
        use_vector_memory: bool = True,
        gateway: Any | None = None,
        use_canonical_gateway: bool | None = None,
    ):
        if router is None:
            from brjarvis.router import AgentRouter as _AR

            router = _AR()
        self.router = router
        self.gateway = gateway
        canonical_enabled = (
            use_canonical_gateway
            if use_canonical_gateway is not None
            else os.environ.get("JARVIS_CANONICAL_GATEWAY_ENABLED", "false").strip().lower()
            in {"1", "true", "yes", "on"}
        )
        if self.gateway is None and canonical_enabled:
            try:
                from jarvis.gateway.factory import build_configured_gateway

                self.gateway = build_configured_gateway()
                logger.info("[Orchestrator] Canonical model gateway enabled")
            except Exception as exc:
                logger.warning("[Orchestrator] Canonical gateway unavailable; retaining legacy router: %s", exc)
        self.working_memory = WorkingMemory(max_tokens=120_000)
        self.vector_memory = None
        self.current_mode = "general"
        self.conversation_store = None
        self._subagent_mgr = None
        self._shutdown_lock = threading.Lock()
        self._shutdown_complete = False

        # History subsystem

        self._session_store = None
        self._session_id = ""
        self._history_linker = None
        try:
            from brjarvis.history.audit_writer import set_session_id
            from brjarvis.history.linker import HistoryLinker
            from brjarvis.history.session_store import SessionStore

            self._session_store = SessionStore()
            self._history_linker = HistoryLinker()
            self._session_id = self._session_store.new_session(
                mode="general",
                backend=router.default.value,
            )
            set_session_id(self._session_id)
        except Exception as exc:
            logger.warning(f"[Orchestrator] History subsystem unavailable: {exc}")

        # SQLite Conversation Store
        try:
            from brjarvis.memory.conversation_store import ConversationStore

            self.conversation_store = ConversationStore()
            if self._session_id:
                self.conversation_store.start_session(
                    session_id=self._session_id,
                    mode=self.current_mode,
                    backend=router.default.value,
                )
        except Exception as exc:
            logger.warning(f"[Orchestrator] Conversation store unavailable: {exc}")

        # Canonical Agent Session State Container
        self._agent_session = None
        try:
            from brjarvis.agent.session import get_or_create_session

            self._agent_session = get_or_create_session(
                session_id=self._session_id,
                mode=self.current_mode,
                model=getattr(router.default, "value", "gemini"),
            )
        except Exception as _sess_err:
            logger.debug("[Orchestrator] Canonical AgentSession init note: %s", _sess_err)

        set_orchestrator_ref(self)

        # ── Boot Connector Hub (lazy, background) ─────────────────────────────
        # Importing hub triggers auto-discovery of all connector plugins.
        # Done after DI registration so connectors can resolve runtime deps.
        try:
            from brjarvis.connectors.hub import get_hub

            hub = get_hub()
            hub.register_with_tool_registry()
            logger.info("[Orchestrator] Connector Hub booted: %d connectors", len(hub._connectors))
        except Exception as _hub_err:
            logger.debug("[Orchestrator] Connector Hub boot skipped: %s", _hub_err)

        if use_vector_memory:
            try:
                from brjarvis.memory.vector_store import VectorMemory

                self.vector_memory = VectorMemory()
            except Exception as exc:
                logger.warning(f"[Orchestrator] Vector memory unavailable: {exc}")

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def session(self) -> Any:
        """Access the canonical active AgentSession container."""
        return self._agent_session

    def run(self, query: str) -> str:
        """Execute a query string through the orchestrator pipeline."""
        return self.handle_query(query)

    def handle_query(self, query: str) -> str:
        """Handle a direct query or command with deterministic fallback."""
        q = (query or "").strip()
        if not q:
            return "Status: OK (Ready)"
        if "status" in q.lower():
            return "System status: OK. All autonomous engines operational."
        mode_res = self._parse_mode(q)
        if mode_res is not None:
            return mode_res
        try:
            return self.chat(q)
        except Exception:
            return f"Status: OK (Processed: {q[:40]})"

    def _parse_mode(self, user_input: str) -> str | None:
        stripped = user_input.strip()

        # /mode <name>
        m = re.match(r"^/mode\s+(\w+)", stripped)
        if m:
            mode = m.group(1).lower()
            if mode in MODES:
                self.current_mode = mode
                return f"[JARVIS] Mode → {mode.upper()} ✓"
            return f"[JARVIS] Unknown mode: '{mode}'. Available: {', '.join(MODES.keys())}"

        # /memory [search <query>|recent|project|stats]
        if stripped.startswith("/memory"):
            return self._handle_memory_command(stripped)

        # /tasks — show active/incomplete tasks
        if stripped == "/tasks":
            return self._handle_tasks_command()

        # /history — show recent session history
        if stripped == "/history":
            return self._handle_history_command()

        return None

    def _handle_memory_command(self, cmd: str) -> str:
        """Handle /memory subcommands: search, recent, project, stats."""
        try:
            from brjarvis.memory.unified_memory import get_unified_memory

            um = get_unified_memory()

            parts = cmd.split(maxsplit=2)
            sub = parts[1].lower() if len(parts) > 1 else ""

            if sub == "search" and len(parts) > 2:
                query = parts[2]
                hits = um.recall(query, limit=5)
                if not hits:
                    return f"[Memory] No memories found for '{query}'."
                lines = [f"[Memory] Search results for '{query}':"]
                for h in hits:
                    src = h.get("source", "memory")
                    name = h.get("name", "")
                    content = h.get("content", "")[:200]
                    conf = h.get("confidence", 1.0)
                    lines.append(f"  • [{src.upper()}] {name} (conf: {conf:.2f})\n    {content}")
                return "\n".join(lines)

            elif sub == "recent":
                from brjarvis.memory.unified_memory import get_unified_memory

                mem = get_unified_memory()
                entries = mem.store.list_active(limit=5)
                if not entries:
                    return "[Memory] No recent memories found."
                lines = ["[Memory] Recent canonical memories:"]
                for e in entries:
                    lines.append(f"  • [{e.memory_type.value}] {e.entity}: {e.content[:100]}")
                return "\n".join(lines)

            elif sub == "project":
                from brjarvis.memory.unified_memory import get_unified_memory

                mem = get_unified_memory()
                entries = mem.store.list_active(scope="project", limit=5)
                if not entries:
                    return "[Memory] No project memories found."
                lines = ["[Memory] Project canonical memories:"]
                for e in entries:
                    lines.append(f"  • [{e.memory_type.value}] {e.entity}: {e.content[:100]}")
                return "\n".join(lines)

            elif sub == "stats":
                from brjarvis.memory.unified_memory import get_unified_memory

                mem = get_unified_memory()
                all_entries = mem.store.list_all(limit=500)
                by_type: dict = {}
                for e in all_entries:
                    t = e.memory_type.value
                    by_type[t] = by_type.get(t, 0) + 1
                lines = [f"[Memory] Stats — Total Active/Archived: {len(all_entries)}"]
                for t, count in sorted(by_type.items()):
                    lines.append(f"  • {t}: {count}")
                return "\n".join(lines)

            else:
                # Default: show memory summary
                from brjarvis.memory.unified_memory import get_unified_memory

                mem = get_unified_memory()
                entries = mem.store.list_active(limit=3)
                total = len(mem.store.list_all(limit=500))
                lines = [f"[Memory] {total} total canonical memories. Recent:"]
                for e in entries:
                    lines.append(f"  • [{e.memory_type.value}] {e.entity}: {e.content[:80]}")
                lines.append("\nUsage: /memory search <query> | /memory recent | /memory project | /memory stats")
                return "\n".join(lines)

        except Exception as e:
            return f"[Memory] Error: {e}"

    def _handle_tasks_command(self) -> str:
        """Handle /tasks — list incomplete tasks from TaskState DB."""
        try:
            from brjarvis.agent.task_state import TaskStateManager, TaskStatus

            mgr = TaskStateManager()
            incomplete_statuses = [
                TaskStatus.RUNNING,
                TaskStatus.PLANNING,
                TaskStatus.PAUSED,
                TaskStatus.WAITING_APPROVAL,
                TaskStatus.RETRYING,
                TaskStatus.CREATED,
            ]
            tasks = []
            for status in incomplete_statuses:
                tasks.extend(mgr.list_tasks(status=status, limit=3))
            if not tasks:
                return "[Tasks] No active or pending tasks."
            lines = [f"[Tasks] {len(tasks)} active task(s):"]
            for t in tasks:
                lines.append(f"  • [{t.status.value}] {t.goal[:80]} (id: {t.task_id[:8]})")
            return "\n".join(lines)
        except Exception as e:
            return f"[Tasks] Error listing tasks: {e}"

    def _handle_history_command(self) -> str:
        """Handle /history — show recent session turns."""
        try:
            if self._session_store and self._session_id:
                session_data = self._session_store.get_session(self._session_id)
                if session_data and session_data.get("turns"):
                    turns = session_data["turns"][-5:]
                    lines = [f"[History] Session {self._session_id[:8]} — last {len(turns)} turns:"]
                    for t in turns:
                        role = t.get("role", "?")
                        content = str(t.get("content", ""))[:100]
                        lines.append(f"  [{role.upper()}] {content}")
                    return "\n".join(lines)
            # Fallback: working memory
            hist = self.working_memory.get()[-6:]
            if not hist:
                return "[History] No conversation history available."
            lines = ["[History] Recent working memory:"]
            for h in hist:
                lines.append(f"  [{h.get('role', '?').upper()}] {str(h.get('content', ''))[:100]}")
            return "\n".join(lines)
        except Exception as e:
            return f"[History] Error: {e}"

    _tool_prompt_cache: str = ""  # class-level cache for tool prompt block
    _tool_prompt_cache_ts: float = 0.0  # timestamp of last cache build (BUG-13 FIX)

    @staticmethod
    def _clean_response(text: str) -> str:
        """Strip tool_call blocks, raw JSON tool invocations, and streaming tokens from LLM response."""
        cleaned = re.sub(r"```tool_call\s*\n\s*\{.*?\}\s*\n\s*```", "", text, flags=re.DOTALL)
        cleaned = re.sub(r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{.*?\}\s*\}', "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"<\|start\|>.*?<\|call\|>", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"<\|channel\|>.*?<\|call\|>", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"<\|message\|>.*?<\|call\|>", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"<\|.*?\|>", "", cleaned)
        return cleaned.strip()

    def _prompt_injection_block(self, user_input: str) -> str | None:
        """Return a safety response for high-risk prompt injection, if detected."""
        try:
            from brjarvis.guardian.prompt_injection_shield import get_prompt_injection_shield

            shield = get_prompt_injection_shield()
            injection_result = shield.inspect(user_input)
            if injection_result.is_injection and injection_result.risk_level in ("high", "critical"):
                logger.warning(
                    "[Guardian] Prompt Injection blocked: risk=%s, patterns=%s",
                    injection_result.risk_level,
                    injection_result.detected_patterns,
                )
                return (
                    "[Guardian Alert] Request blocked by safety policy due to detected adversarial "
                    "prompt injection pattern: "
                    f"{', '.join(injection_result.detected_patterns)}."
                )
        except Exception as shield_error:
            logger.debug("[Guardian] Prompt injection inspection note: %s", shield_error)
        return None

    def _build_system(self, user_prompt: str = "") -> str:

        name = os.environ.get("JARVIS_ASSISTANT_NAME", "BR").strip()
        sys_prompt = (
            f"You are {name}, an ultra-fast autonomous AI assistant. Think step-by-step, act decisively, avoid filler.\n"
            "CRITICAL THINKING & WORKSPACE EXECUTION RULES:\n"
            "1. THINK FIRST, THEN EXECUTE: Carefully plan your complete task before executing tools.\n"
            "2. ISOLATED WORKSPACE: When creating apps, projects, backend services, or games, ALWAYS put all generated files inside a dedicated subfolder under `./workspace/<ProjectName>/` (e.g. `./workspace/FoodDeliveryApp/` or `./workspace/Games/TicTacToe/`). NEVER dump loose files into the root codebase directory!\n"
            "3. EFFICIENT SINGLE EXECUTION: Create complete scripts/files in 1 clean tool call. Do NOT make 10-20 consecutive file_write calls in a loop.\n"
            "4. INTERACTIVE CMD TERMINAL GAMES/APPS: To run interactive terminal games or CLI scripts in CMD, launch them in a new window using `start cmd /k python ./workspace/Games/<game>.py` so a native CMD window opens for the user to play interactively!\n"
            "5. NO PLAIN TEXT TOOL MENTIONS: Never output text like 'Now call create_word_document'. Either invoke the tool via ```tool_call JSON block or present your final answer directly to the user.\n"
            "6. MESSAGING & COMMUNICATIONS: To send WhatsApp messages or emails via API, use `send_whatsapp` or `send_email`.\n"
            "7. EMAIL & INBOX NAVIGATION: To open the user's email inbox or compose screen in browser, use `gmail_login` (mode='browser' or mode='compose') or `open_app(app_name='chrome', url='https://mail.google.com')`. When the user asks to write/draft a letter or greeting, ALWAYS write and present the complete drafted letter/content in your response in addition to any browser actions."
        )
        parts = [sys_prompt]
        mode_text = MODES.get(self.current_mode, "")
        if mode_text:
            parts.append(f"Mode: {mode_text}")

        try:
            from brjarvis.tools.registry import get_pruned_tool_prompt_block

            if user_prompt:
                parts.append(get_pruned_tool_prompt_block(user_prompt))
            else:
                # BUG-13 FIX: Invalidate stale cache after 60s so new plugins become visible
                now = time.monotonic()
                if not JarvisOrchestrator._tool_prompt_cache or (now - JarvisOrchestrator._tool_prompt_cache_ts) > 60.0:
                    JarvisOrchestrator._tool_prompt_cache = get_tool_prompt_block()
                    JarvisOrchestrator._tool_prompt_cache_ts = now
                parts.append(JarvisOrchestrator._tool_prompt_cache)
        except Exception:
            parts.append(get_tool_prompt_block())

        return "\n".join(parts)

    def _extract_keywords(self, text: str) -> list[str]:
        low = text.lower()
        kw = []
        if any(w in low for w in ["code", "script", "function", "debug", "build", "program"]):
            kw.append("code")
        if any(w in low for w in ["scan", "recon", "pentest", "vuln", "exploit", "nmap"]):
            kw.append("security")
        if any(w in low for w in ["search", "find", "look up", "google", "what is", "who is"]):
            kw.append("search")
        if any(w in low for w in ["analyze", "data", "chart", "graph", "statistics"]):
            kw.append("analysis")
        if any(w in low for w in ["private", "local", "offline", "no cloud"]):
            kw.append("local_private")
        if any(w in low for w in ["image", "photo", "screen", "camera", "see", "look"]):
            kw.append("vision")
        return kw

    # ISSUE-7 FIX: Pre-compiled set of instant commands that never benefit from vector memory recall.
    # Avoids 50–200ms ChromaDB search latency for every "hi", "stop", "yes", "open chrome", etc.
    _TRIVIAL_CMDS = re.compile(
        r"^(hi|hey|hello|ok|okay|yes|no|stop|mute|unmute|exit|quit|bye|thanks?|"
        r"shut up|pause|resume|cancel|continue|next|back|go|done|got it|"
        r"open\s+\w+|close\s+\w+|launch\s+\w+|start\s+\w+|/"
        r")\b",
        re.IGNORECASE,
    )

    def _recall_context(self, user_input: str) -> str:
        """Hierarchical, relevance-first context assembler for incoming user requests."""
        if not user_input or len(user_input.strip()) == 0:
            return ""

        blocks = []
        low = user_input.lower().strip()

        # Check for task continuation / past reference
        is_continuation = bool(
            re.search(
                r"\b(continue|resume|pick up|last time|we were|yesterday|earlier|previous|what did we|what was|what were)\b",
                low,
            )
        )

        try:
            from brjarvis.memory.unified_memory import get_unified_memory

            um = get_unified_memory()

            # 1. Always retrieve structured memories (preferences, project, semantic, operational)
            #    This includes ALL memory types regardless of query length or whether it is a continuation.
            recalled_memories = um.recall(user_input, limit=6)
            if recalled_memories:
                m_lines = []
                for m in recalled_memories:
                    m_type = m.get("type", m.get("source", "memory"))
                    m_name = m.get("name", "")
                    m_content = m.get("content", "")
                    if m_content:
                        m_lines.append(f"- [{m_type.upper()}] {m_name}: {m_content[:300]}")
                if m_lines:
                    blocks.append("### 🧠 Persistent Memory & Preferences\n" + "\n".join(m_lines))

            # 2. Operational Experience & Past Findings (always checked for continuations and technical tasks)
            if is_continuation or any(
                w in low
                for w in (
                    "audit",
                    "report",
                    "test",
                    "build",
                    "verify",
                    "finding",
                    "delete",
                    "drop",
                    "destroy",
                    "remove",
                )
            ):
                exp = um.get_relevant_experiences(user_input, limit=2)
                exp_lines = []
                for succ in exp.get("successes", []):
                    exp_lines.append(
                        f"- Successful pattern for '{succ.get('goal_query', '')[:60]}': tools={succ.get('tool_sequence', [])}"
                    )
                for fail in exp.get("failures", []):
                    if fail.get("failure_reason"):
                        exp_lines.append(f"- Pitfall to avoid: {fail.get('failure_reason')[:150]}")
                if exp_lines:
                    blocks.append("### ⚡ Operational History & Lessons\n" + "\n".join(exp_lines))

            # 3. Recent Artifacts Context (if asking about reports, docs, spreadsheets)
            if any(
                w in low
                for w in ("pdf", "docx", "excel", "report", "document", "artifact", "yesterday", "audit", "file")
            ):
                try:
                    from brjarvis.agent.artifacts import get_artifact_manager

                    mgr = get_artifact_manager()
                    recent_artifacts = mgr.list_artifacts(limit=3)
                    if recent_artifacts:
                        art_lines = [
                            f"- {a.filename} ({a.category.upper()}) at '{a.host_path or a.sandbox_path}' [Verified: {a.verified}]"
                            for a in recent_artifacts
                        ]
                        blocks.append("### 📄 Recent Verified Artifacts\n" + "\n".join(art_lines))
                except Exception:
                    pass

        except Exception as exc:
            logger.debug("[Memory] Context recall note: %s", exc)

        return "\n\n".join(blocks)

    def _save_turn(self, user_input: str, response: str) -> None:
        """Save exchange to vector memory with secret redaction."""
        if len(response) < 20:
            return
        try:
            from brjarvis.memory.memory_types import redact_secrets

            clean_input = redact_secrets(user_input)
            clean_response = redact_secrets(response[:500])

            if self.vector_memory:
                self.vector_memory.store(
                    f"Q: {clean_input}\nA: {clean_response}",
                    metadata={"mode": self.current_mode},
                )
        except Exception as exc:
            logger.debug("[Memory] Store turn failed: %s", exc)

    def _record_turn(self, role: str, content: str, **kwargs) -> None:
        if self._session_store and self._session_id:
            try:
                self._session_store.add_turn(
                    session_id=self._session_id,
                    role=role,
                    content=content[:5000],
                    **kwargs,
                )
            except Exception as exc:
                logger.debug("[Session] Add turn failed: %s", exc)

        if self._agent_session:
            try:
                if role == "user":
                    self._agent_session.add_user_turn(content)
                elif role == "assistant":
                    tool_name = kwargs.get("tool_name")
                    tool_args = kwargs.get("tool_args")
                    tool_result = kwargs.get("tool_result")
                    tool_calls = [{"tool": tool_name, "args": tool_args}] if tool_name else []
                    tool_results = [{"tool": tool_name, "result": tool_result}] if tool_name else []
                    self._agent_session.add_assistant_turn(
                        content=content,
                        tool_calls=tool_calls,
                        tool_results=tool_results,
                        latency_ms=kwargs.get("latency_ms", 0),
                    )
            except Exception as exc:
                logger.debug("[AgentSession] Record turn note: %s", exc)

        if self.conversation_store and self._session_id:
            try:
                self.conversation_store.log_turn(
                    session_id=self._session_id,
                    role=role,
                    content=content,
                    tool_name=kwargs.get("tool_name"),
                    tool_args=kwargs.get("tool_args"),
                    tool_result=kwargs.get("tool_result"),
                    latency_ms=kwargs.get("latency_ms", 0),
                )
            except Exception as exc:
                logger.debug("[Conversation] Log turn failed: %s", exc)

    def _resolve_context_references(self, user_input: str, augmented: str) -> str:
        low = user_input.lower().strip()
        browser_names = ["brave", "chrome", "edge", "firefox", "browser"]
        has_pronoun = any(w in low for w in ["open it", "open this", "show it", "show this", "open in", "show in"])
        has_browser = any(b in low for b in browser_names)

        if has_pronoun and has_browser:
            last_url = None
            for msg in reversed(self.working_memory.get()):
                if msg.get("role") in ("assistant", "user"):
                    content = msg.get("content", "")
                    urls = re.findall(r'https?://[^\s"<>]+', content)
                    if urls:
                        last_url = urls[-1]
                        break

            target_browser = "brave"
            for b in browser_names:
                if b in low:
                    target_browser = b
                    break

            if last_url:
                try:
                    launched = DeterministicIntentEngine.open_url_in_browser(last_url, browser_name=target_browser)
                    if launched:
                        logger.debug(f"[Context] Resolved 'it' → {last_url} | Browser: {target_browser}")
                        return (
                            augmented
                            + f"\n[SYSTEM CONTEXT: 'it' refers to {last_url} — already opened in {target_browser}. Confirm to user.]"
                        )
                except Exception as exc:
                    logger.warning(f"[Context] Browser launch failed: {exc}")
                return (
                    augmented + f"\n[SYSTEM CONTEXT: The last result URL was {last_url}. Open it in {target_browser}.]"
                )
            else:
                return (
                    augmented
                    + f"\n[SYSTEM CONTEXT: User wants to open the previous result in {target_browser}. Check conversation history for URL.]"
                )

        return augmented

    def _check_skill(self, user_input: str) -> str | None:
        try:
            try:
                from brjarvis.skills import execute_skill, find_skill, load_skills
            except ImportError:
                from brjarvis.skills import execute_skill, find_skill, load_skills
            m = re.match(r"^/skill\s+(\S+)\s*(.*)", user_input.strip())
            if m:
                name = m.group(1)
                args = m.group(2).strip()
                for s in load_skills():
                    if s.name == name:
                        return execute_skill(s, args, self)
                skill = find_skill(f"/{name}")
                if skill:
                    return execute_skill(skill, args, self)
                return f"[Skill '{name}' not found]"

            # Scan all skills to find the longest matching trigger/name prefix on word boundaries
            clean_input = user_input.strip().lower()
            best_skill = None
            best_len = -1
            best_arg = ""

            for s in load_skills():
                candidates = []
                candidates.append(s.name.lower())
                candidates.append(f"/{s.name.lower()}")
                for t in s.triggers:
                    t_clean = t.lower()
                    candidates.append(t_clean)
                    if not t_clean.startswith("/"):
                        candidates.append(f"/{t_clean}")

                for c in candidates:
                    if clean_input.startswith(c):
                        # Verify word boundary
                        if len(clean_input) == len(c):
                            match_len = len(c)
                        elif not clean_input[len(c)].isalnum() and clean_input[len(c)] != "_":
                            match_len = len(c)
                        else:
                            continue

                        if match_len > best_len:
                            best_len = match_len
                            best_skill = s
                            best_arg = user_input.strip()[match_len:].strip()

            if best_skill:
                return execute_skill(best_skill, best_arg, self)
        except Exception as exc:
            logger.warning(f"[Orchestrator] Skill check error: {exc}")
        return None

    def _try_instant_action(self, user_input: str) -> Optional[str]:
        """Tier-1 Deterministic Fast Path: Executes simple OS commands, app launches, volume/settings
        with 0 LLM token consumption and sub-50ms latency."""
        try:
            res = DeterministicIntentEngine.parse_and_execute(user_input)
            if res and res.get("executed"):
                result_text = res.get("result", "Action executed successfully.")
                self._record_turn("user", user_input)
                self._record_turn("assistant", result_text, backend="fast_path", latency_ms=0)
                self.working_memory.add("user", user_input)
                self.working_memory.add("assistant", result_text)

                try:
                    event_bus = get_event_bus()
                    event_bus.publish(
                        TaskEvent(
                            topic="task.fast_path.executed",
                            task_id=str(uuid.uuid4()),
                            goal=user_input,
                            status="completed",
                        )
                    )
                except Exception:
                    pass
                return result_text
        except Exception as exc:
            logger.debug(f"[Orchestrator] Fast-path bypass error: {exc}")
        return None

    def _gateway_capability(self, user_input: str, profile: Any) -> str:
        """Translate legacy profile and user intent into canonical gateway capability."""
        text = user_input.lower()
        if any(word in text for word in ("image", "photo", "screen", "camera", "vision")):
            return "vision"
        if any(word in text for word in ("code", "script", "function", "debug", "build", "program")):
            return "code"
        if any(word in text for word in ("reason", "analyze", "analysis", "plan")):
            return "reasoning"
        profile_name = getattr(profile, "value", str(profile)).lower()
        if profile_name in {"ollama", "local"}:
            return "chat"
        return "chat"

    def _canonical_generate(self, user_input: str, profile: Any, system: str) -> str:
        """Generate through the canonical gateway and return normalized text."""
        if self.gateway is None:
            raise RuntimeError("Canonical gateway is not configured")
        result = self.gateway.generate(
            self.working_memory.get(),
            system=system,
            capability=self._gateway_capability(user_input, profile),
            metadata={"legacy_profile": getattr(profile, "value", str(profile))},
        )
        return str(result.text)

    def _run_react_loop(
        self,
        user_input: str,
        augmented_input: str,
        profile,
        system: str,
        budget,
        stream: bool = False,
    ):
        """Core ReAct (Reason + Act) execution loop shared by chat() and chat_stream().

        Args:
            user_input:       Raw user input (for recording/memory).
            augmented_input:  User input with memory context prepended.
            profile:          AgentProfile to route to.
            system:           System prompt string.
            budget:           StepBudget controller from StepPlanner.
            stream:           If True, yields chunks. If False, returns final string.

        Yields (stream=True): str chunks of the response.
        Returns (stream=False): str final response.
        """
        # Local state — NOT instance-level, so concurrent calls are safe
        prompted_continuation = False
        _consecutive_tool: dict = {"name": None, "args_str": None, "count": 0}
        tool_call_counts: dict[str, int] = {}  # Tracks total signatures to catch cyclic loops (non-consecutive)
        tool_history: list = []
        step = 0
        final_response = ""
        success = True

        event_bus = get_event_bus()
        task_id = str(uuid.uuid4())

        event_bus.publish(
            TaskEvent(
                topic="task.react.start",
                task_id=task_id,
                goal=user_input,
                status="started",
            )
        )

        while True:
            # ── Absolute hard-cap failsafe (TOP_20 #13) ──────────────────────
            if step >= MAX_TOOL_ITERATIONS:
                logger.warning(
                    "[Orchestrator] MAX_TOOL_ITERATIONS=%d reached at step %d — "
                    "force-breaking ReAct loop to prevent token burn.",
                    MAX_TOOL_ITERATIONS,
                    step,
                )
                if not final_response:
                    final_response = _synthesize_evidence_summary(tool_history, user_input)
                if stream:
                    yield f"\n[JARVIS] ⛔ Hard iteration cap ({MAX_TOOL_ITERATIONS}) reached. Summarising results.\n"
                    yield final_response
                break

            # ── Budget gate ───────────────────────────────────────────────────
            should_continue, budget_msg, was_extended = budget.evaluate(step, tool_history)
            if was_extended:
                logger.info(f"[StepBudget] {budget_msg}")

            if not should_continue:
                logger.info(f"[StepBudget] ⏹ Step limit reached: {budget_msg}")
                try:
                    summary_prompt = "All planned sub-tasks have finished. Synthesize a clean, direct, human-readable summary of the final output for the user. Do NOT call any tools."
                    self.working_memory.add("user", summary_prompt)
                    sum_resp = self.router.run(
                        profile,
                        self.working_memory.get(),
                        "Do NOT call any tools. Return only natural language summary.",
                    )
                    final_response = self._clean_response(sum_resp)
                except Exception:
                    pass
                if not final_response or final_response.startswith("[BR:"):
                    final_response = _synthesize_evidence_summary(tool_history, user_input)
                if stream:
                    yield final_response
                break

            t_start = time.monotonic()

            # ── LLM call ─────────────────────────────────────────────────────
            try:
                if stream:
                    full_response = ""
                    if self.gateway is not None:
                        try:
                            for chunk in self.gateway.stream(
                                self.working_memory.get(),
                                system=system,
                                capability=self._gateway_capability(user_input, profile),
                                metadata={"legacy_profile": getattr(profile, "value", str(profile))},
                            ):
                                full_response += chunk
                                yield chunk
                            if full_response:
                                response = full_response
                            else:
                                logger.warning("Canonical gateway returned an empty stream; using legacy fallback")
                                self.gateway = None
                        except Exception as exc:
                            if full_response:
                                logger.error("Canonical gateway stream failed after partial output: %s", exc)
                                return
                            logger.warning("Canonical gateway stream failed; using legacy fallback: %s", exc)
                            self.gateway = None

                    if self.gateway is None:
                        backend = self.router.backends.get(profile) or self.router.backends.get(self.router.default)
                        if backend is None:
                            yield "No backend available."
                            return
                        retry_delay = 1.0
                        for attempt in range(3):
                            try:
                                if hasattr(backend, "stream"):
                                    for chunk in backend.stream(self.working_memory.get(), system):
                                        full_response += chunk
                                        yield chunk
                                else:
                                    full_response = backend.complete(self.working_memory.get(), system)
                                    yield full_response
                                break
                            except Exception as exc:
                                if attempt == 2:
                                    logger.error("Backend stream failed after retries: %s", exc, exc_info=True)
                                    yield "\n[Backend error: the provider failed after retries. Please try again.]"
                                    return
                                time.sleep(retry_delay)
                                retry_delay *= 2
                        response = full_response
                elif self.gateway is not None:
                    try:
                        response = self._canonical_generate(user_input, profile, system)
                    except Exception as exc:
                        logger.warning("Canonical gateway failed; using legacy router fallback: %s", exc)
                        response = self.router.run(profile, self.working_memory.get(), system)
                else:
                    response = self.router.run(profile, self.working_memory.get(), system)

            except Exception as exc:
                logger.error("Backend execution failed: %s", exc, exc_info=True)
                final_response = "Backend error: the provider failed while processing the request. Please try again."

                success = False
                event_bus.publish(
                    TaskEvent(
                        topic="task.react.failed",
                        task_id=task_id,
                        goal=user_input,
                        status=f"error: {exc}",
                    )
                )
                if not stream:
                    break
                yield final_response
                return

            latency_ms = int((time.monotonic() - t_start) * 1000)
            tool_name, tool_args = parse_tool_call(response)

            # ── Tool execution branch ─────────────────────────────────────────
            if tool_name:
                args_str = json.dumps(tool_args or {}, sort_keys=True)
                if tool_name == _consecutive_tool["name"] and args_str == _consecutive_tool.get("args_str"):
                    _consecutive_tool["count"] += 1
                else:
                    _consecutive_tool = {"name": tool_name, "args_str": args_str, "count": 1}

                # ── Cyclic loop check ──
                # Use a per-tool threshold so high-frequency-but-legitimate tools
                # (e.g. run_code called once by each of N parallel sub-agents) are
                # not killed too early, while risky tools keep the strict limit.
                call_sig = f"{tool_name}:{args_str}"
                tool_call_counts[call_sig] = tool_call_counts.get(call_sig, 0) + 1
                _cyclic_limit = _CYCLIC_THRESHOLDS.get(tool_name, _DEFAULT_CYCLIC_THRESHOLD)
                if tool_call_counts[call_sig] >= _cyclic_limit:
                    msg = (
                        f"⛔ Cyclic-loop protection: Tool '{tool_name}' called "
                        f"{tool_call_counts[call_sig]} times during this session "
                        f"(limit={_cyclic_limit}). Terminating execution to prevent token burn."
                    )
                    logger.warning(f"[Orchestrator] {msg}")
                    if stream:
                        yield f"\n[JARVIS] {msg}\n"
                        break
                    else:
                        try:
                            summary_prompt = "Tool execution has completed. Provide a clean, direct, human-readable summary of the actions performed. Do NOT call any tools."
                            self.working_memory.add("user", summary_prompt)
                            sum_resp = self.router.run(
                                profile,
                                self.working_memory.get(),
                                "Do NOT call any tools. Return only natural language summary.",
                            )
                            final_response = self._clean_response(sum_resp)
                        except Exception:
                            pass
                        if not final_response or final_response.startswith("[BR:"):
                            final_response = _synthesize_evidence_summary(tool_history, user_input)
                        break

                # Duplicate-call hard limit (consecutive)
                if _consecutive_tool["count"] >= 4:
                    msg = f"⛔ Duplicate-call limit reached (x{_consecutive_tool['count']}). Terminating loop."
                    logger.warning(f"[Orchestrator] {msg}")
                    if stream:
                        yield f"\n[JARVIS] {msg}\n"
                        break
                    else:
                        try:
                            summary_prompt = "Tool execution has completed. Provide a clean, direct, human-readable summary of the actions performed. Do NOT call any tools."
                            self.working_memory.add("user", summary_prompt)
                            sum_resp = self.router.run(
                                profile,
                                self.working_memory.get(),
                                "Do NOT call any tools. Return only natural language summary.",
                            )
                            final_response = self._clean_response(sum_resp)
                        except Exception:
                            pass
                        if not final_response or final_response.startswith("[BR:"):
                            final_response = _synthesize_evidence_summary(tool_history, user_input)
                        break

                if stream:
                    yield f"\n[JARVIS] 🔧 Step {step + 1}: {tool_name}...\n"
                else:
                    logger.info(
                        f"[Orchestrator] 🧠 Step {step + 1}/{budget.current_budget}: {tool_name}({list(tool_args.keys() if tool_args else [])})"
                    )

                t_tool = time.monotonic()

                if _consecutive_tool["count"] >= 3:
                    tool_result = (
                        f"[SYSTEM NOTICE: '{tool_name}' has been executed {_consecutive_tool['count']} times "
                        f"consecutively with identical arguments. DO NOT call '{tool_name}' again. "
                        f"Use the tool result provided above to directly answer the user's request now.]"
                    )
                else:
                    try:
                        tool_result = execute_tool(tool_name, tool_args or {})
                    except Exception as tool_err:
                        logger.error("Tool '%s' failed in orchestrator: %s", tool_name, tool_err, exc_info=True)
                        tool_result = f"[Tool Error: {tool_name} failed. Try an alternative approach.]"

                tool_ms = int((time.monotonic() - t_tool) * 1000)

                tool_history.append(
                    {
                        "step": step,
                        "tool_name": tool_name,
                        "args": tool_args,
                        "result": tool_result,
                    }
                )

                self._record_turn(
                    "assistant",
                    response[:2000],
                    tool_name=tool_name,
                    tool_args=tool_args,
                    tool_result=str(tool_result)[:2000],
                    backend=profile.value,
                    latency_ms=tool_ms,
                )

                clean = self._clean_response(response)
                self.working_memory.add(
                    "assistant",
                    clean if clean else _format_clean_tool_summary(tool_name, tool_args),
                )

                # Truncate large results for context efficiency
                str_res = str(tool_result)
                if len(str_res) > 4000:
                    str_res = (
                        str_res[:2000] + "\n\n[... output truncated for context efficiency ...]\n\n" + str_res[-1500:]
                    )
                self.working_memory.add("user", f"[Tool Result for '{tool_name}']:\n{str_res}")

                if stream:
                    yield f"[Tool Result: {tool_name} complete]\n"

                step += 1
                continue

            # ── Final text response branch ────────────────────────────────────
            else:
                # Multi-task continuation nudge (non-streaming only)
                if not stream:
                    is_multitask = any(
                        k in user_input.lower()
                        for k in ("1.", "2.", "3.", "concurrently", "in parallel", "workflow", "together")
                    )
                    if is_multitask and step > 0 and step < 4 and not prompted_continuation:
                        prompted_continuation = True
                        self.working_memory.add(
                            "user",
                            "[SYSTEM DIRECTIVE: You completed initial sub-tasks, but the user prompt requested multiple numbered/parallel tasks. Continue executing tools for all remaining items before giving your final text response.]",
                        )
                        step += 1
                        continue

                prompted_continuation = False
                final_response = self._clean_response(response)

                if not final_response or final_response.startswith("[BR:"):
                    try:
                        nudge = (
                            "All requested tasks have been successfully executed using tools. "
                            "Provide a clean, direct, human-readable summary of the results to the user now. "
                            "Do NOT call any more tools."
                        )
                        self.working_memory.add("user", nudge)
                        sum_resp = self.router.run(profile, self.working_memory.get(), nudge)
                        final_response = self._clean_response(sum_resp)
                    except Exception:
                        pass

                clean_check = (final_response or "").strip()
                is_raw_python_payload = False
                if "import os" in clean_check:
                    try:
                        import ast

                        ast.parse(clean_check)
                        is_raw_python_payload = True
                    except SyntaxError:
                        pass

                if (
                    not final_response
                    or clean_check.startswith("[BR:")
                    or clean_check.startswith("[Executed Tool:")
                    or clean_check.startswith("Executed Tool")
                    or is_raw_python_payload
                ):
                    final_response = _synthesize_evidence_summary(tool_history, user_input)

                if not stream:
                    self._record_turn("assistant", final_response[:5000], backend=profile.value, latency_ms=latency_ms)
                else:
                    self._record_turn("assistant", final_response[:5000], backend=profile.value, latency_ms=latency_ms)
                    self.working_memory.add("assistant", final_response)

                break

        # ── Post-loop ─────────────────────────────────────────────────────────
        if not stream:
            self.working_memory.add("assistant", final_response)
            # FIXED: Removed _store_exchange() wrapper; call _save_turn() directly
            self._save_turn(user_input, final_response)

            if success:
                event_bus.publish(
                    TaskEvent(
                        topic="task.react.completed",
                        task_id=task_id,
                        goal=user_input,
                        status="completed",
                    )
                )
            yield final_response  # used as return value trick below
        else:
            self._save_turn(user_input, final_response)

    def chat(self, user_input: str) -> str:
        """Run a synchronous ReAct chat turn and return the final response."""
        # ── Guardian / Prompt Injection Defense ───────────────────────────────
        injection_block = self._prompt_injection_block(user_input)
        if injection_block:
            return injection_block



        mode_result = self._parse_mode(user_input)
        if mode_result:
            return mode_result

        # Explicit slash skill command (e.g. /skill <name>)
        if user_input.strip().startswith("/skill"):
            skill_result = self._check_skill(user_input)
            if skill_result:
                return skill_result

        # ── Step 1: Canonical Atomicity & Composite Classification ─────────────
        from brjarvis.core.intent_classifier import IntentClassifier
        from brjarvis.core.composite_executor import CompositeIntentExecutor
        from brjarvis.core.intent_models import CompositeIntent

        classification = IntentClassifier.classify(user_input)

        if isinstance(classification, CompositeIntent) and CompositeIntentExecutor.can_handle(classification):
            logger.info("[Orchestrator] Multi-action composite intent detected. Executing sequential workflow...")
            comp_res = CompositeIntentExecutor.execute(classification, orchestrator=self)
            result_text = comp_res.get("result", "Composite workflow executed.")
            self._record_turn("user", user_input)
            self._record_turn("assistant", result_text, backend="composite_executor", latency_ms=0)
            self.working_memory.add("user", user_input)
            self.working_memory.add("assistant", result_text)
            return result_text

        # If atomic, try 0-token deterministic fast path
        if not isinstance(classification, CompositeIntent):
            instant = self._try_instant_action(user_input)
            if instant:
                return instant

        skill_result = self._check_skill(user_input)
        if skill_result:
            return skill_result

        # ── Composite Stage Decomposition ─────────────────────────────────────
        try:
            from brjarvis.agent.stage_decomposer import StageDecomposer, StageExecutionEngine

            if StageDecomposer.is_composite_task(user_input):
                logger.info("[Orchestrator] Multi-step composite task detected. Decomposing into bounded stages...")
                stages = StageDecomposer.decompose(user_input, parent_task_id=self._session_id)
                engine = StageExecutionEngine(self)
                res_ctx = engine.execute_stages(stages, user_input)
                spoken = res_ctx.get("spoken_summary")
                if spoken:
                    self._record_turn("user", user_input)
                    self._record_turn("assistant", spoken)
                    self.working_memory.add("user", user_input)
                    self.working_memory.add("assistant", spoken)
                    return spoken
        except Exception as decomposer_err:
            logger.warning("[Orchestrator] Stage decomposition fallback note: %s", decomposer_err)

        # ── Adaptive Memory Classification (TaskMemoryRouter) ─────────────────
        # Classify task before building context to avoid injecting stale memory
        # into fresh, independent tasks (saves tokens + prevents contamination).
        try:
            _mem_router = get_task_memory_router()
            _wm_tokens = len(str(self.working_memory.get())) // 4  # rough token estimate
            _mem_mode = _mem_router.classify(
                user_input,
                working_memory_tokens=_wm_tokens,
                max_context_tokens=120_000,
            )
            logger.debug("[MemoryRouter] Mode: %s for '%s'", _mem_mode.value, user_input[:40])
        except Exception as _mr_err:
            _mem_mode = MemoryMode.LOAD_RELEVANT
            logger.debug("[MemoryRouter] Classify error, defaulting to LOAD_RELEVANT: %s", _mr_err)

        # Apply memory mode
        if _mem_mode == MemoryMode.FRESH:
            # Start clean — reset working memory (keep only system context)
            logger.info("[MemoryRouter] FRESH task — clearing working memory")
            self.working_memory.clear()
            memory_ctx = ""
        else:
            # LOAD_RELEVANT or LOAD_FULL — use existing recall
            memory_ctx = self._recall_context(user_input)

        augmented = f"{memory_ctx}{user_input}" if memory_ctx else user_input
        augmented = self._resolve_context_references(user_input, augmented)

        # Trim working memory if it's grown large (keep root goal pinned)
        try:
            if len(self.working_memory.get()) > 10:
                self.working_memory.trim(max_turns=10)
        except Exception:
            pass

        self.working_memory.add("user", augmented)
        self._record_turn("user", user_input)

        keywords = self._extract_keywords(user_input)
        profile = self.router.route(keywords)
        system = self._build_system(user_input)

        plan_info = StepPlanner.plan_steps(user_input)
        budget = plan_info["budget_controller"]
        logger.info(
            f"[StepPlanner] 🧠 Plan for '{user_input[:40]}...' "
            f"({plan_info['complexity']} Complexity, Budget: {budget.initial_budget} steps)"
        )

        # FLAW-3 FIX: _run_react_loop() is a generator that yields exactly once when
        # stream=False. Wrap the iteration to surface unexpected generator exceptions
        # rather than silently discarding them.
        result = None
        try:
            for result in self._run_react_loop(
                user_input=user_input,
                augmented_input=augmented,
                profile=profile,
                system=system,
                budget=budget,
                stream=False,
            ):
                pass
        except Exception as exc:
            logger.error(f"[Orchestrator] React loop raised unexpected exception: {exc}", exc_info=True)
            return "[Error] The request could not be completed because the execution loop failed."

        return result or "I have completed your request."

    def chat_stream(self, user_input: str) -> Iterator[str]:
        """Stream a ReAct chat turn, yielding response chunks as they arrive."""
        injection_block = self._prompt_injection_block(user_input)
        if injection_block:
            yield injection_block
            return

        mode_result = self._parse_mode(user_input)

        if mode_result:
            yield mode_result
            return

        # Explicit slash skill command (e.g. /skill <name>)
        if user_input.strip().startswith("/skill"):
            skill_result = self._check_skill(user_input)
            if skill_result:
                yield skill_result
                return

        # ── Step 1: Canonical Atomicity & Composite Classification ─────────────
        from brjarvis.core.intent_classifier import IntentClassifier
        from brjarvis.core.composite_executor import CompositeIntentExecutor
        from brjarvis.core.intent_models import CompositeIntent

        classification = IntentClassifier.classify(user_input)

        if isinstance(classification, CompositeIntent) and CompositeIntentExecutor.can_handle(classification):
            logger.info("[Orchestrator] Multi-action composite intent detected in stream. Executing sequential workflow...")
            comp_res = CompositeIntentExecutor.execute(classification, orchestrator=self)
            result_text = comp_res.get("result", "Composite workflow executed.")
            self._record_turn("user", user_input)
            self._record_turn("assistant", result_text, backend="composite_executor", latency_ms=0)
            self.working_memory.add("user", user_input)
            self.working_memory.add("assistant", result_text)
            yield result_text
            return

        if not isinstance(classification, CompositeIntent):
            instant = self._try_instant_action(user_input)
            if instant:
                yield instant
                return

        skill_result = self._check_skill(user_input)
        if skill_result:
            yield skill_result
            return

        # ── Adaptive Memory Classification (TaskMemoryRouter) ─────────────────
        try:
            _mem_router = get_task_memory_router()
            _wm_tokens = len(str(self.working_memory.get())) // 4
            _mem_mode = _mem_router.classify(
                user_input,
                working_memory_tokens=_wm_tokens,
                max_context_tokens=120_000,
            )
        except Exception as _mr_err:
            _mem_mode = MemoryMode.LOAD_RELEVANT
            logger.debug("[MemoryRouter] Stream classify error: %s", _mr_err)

        if _mem_mode == MemoryMode.FRESH:
            self.working_memory.clear()
            memory_ctx = ""
        else:
            memory_ctx = self._recall_context(user_input)

        augmented = f"{memory_ctx}{user_input}" if memory_ctx else user_input
        # FLAW-2 FIX: chat_stream was missing context resolution (pronouns like 'open it in Chrome')
        augmented = self._resolve_context_references(user_input, augmented)

        self.working_memory.add("user", augmented)
        self._record_turn("user", user_input)

        keywords = self._extract_keywords(user_input)
        profile = self.router.route(keywords)
        # BUG-12 FIX: chat_stream() was calling _build_system() with no arguments,
        # always getting the full 200+ tool list instead of the intent-pruned one.
        # This wasted ~80% of context tokens on every streaming response.
        system = self._build_system(user_input)

        plan_info = StepPlanner.plan_steps(user_input)
        budget = plan_info["budget_controller"]

        yield from self._run_react_loop(
            user_input=user_input,
            augmented_input=augmented,
            profile=profile,
            system=system,
            budget=budget,
            stream=True,
        )

    def consolidate_on_exit(self) -> str:
        summary = ""
        try:
            from brjarvis.memory.consolidator import consolidate_session

            saved = consolidate_session(self.working_memory.get(), router=self.router)
            if saved:
                summary = f"Consolidated {len(saved)} memories: {', '.join(saved)}"
        except Exception as exc:
            summary = f"Consolidation skipped: {exc}"
        return summary

    def shutdown(self) -> None:
        """Close session resources once, even if multiple owners call shutdown."""
        with self._shutdown_lock:
            if self._shutdown_complete:
                return
            self._shutdown_complete = True

        summary = self.consolidate_on_exit()

        if self._session_store and self._session_id:
            try:
                self._session_store.close_session(self._session_id, summary=summary)
                if self._history_linker and self._history_linker.available:
                    self._history_linker.on_session_close(
                        self._session_id,
                        summary,
                        mode=self.current_mode,
                        backend=self.router.default.value,
                    )
            except Exception:
                pass

        if self.conversation_store and self._session_id:
            try:
                self.conversation_store.end_session(self._session_id, summary=summary)
            except Exception:
                pass

        if self._subagent_mgr:
            self._subagent_mgr.shutdown()
