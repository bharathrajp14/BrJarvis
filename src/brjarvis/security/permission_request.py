# security/permission_request.py — Canonical Permission Request & Decision Engine
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set

from brjarvis.events.bus import get_event_bus
from brjarvis.events.types import PermissionEvent


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PermissionDecision(str, Enum):
    ALLOW_ONCE = "allow_once"
    ALLOW_SESSION = "allow_session"
    ALLOW_TOOL = "allow_tool"
    ALLOW_TARGET = "allow_target"
    DENY = "deny"
    CANCEL = "cancel"


# Tool classifications by inherent risk
CRITICAL_TOOLS: Set[str] = {
    "file_delete",
    "mobile_delete_files",
    "system_cleanup",
    "system_optimizer",
    "process_kill",
    "computer_settings",
}

HIGH_RISK_TOOLS: Set[str] = {
    "file_write",
    "run_code",
    "scratchpad_eval",
    "run_automation_workflow",
    "execute_system_automation",
    "send_email",
    "send_whatsapp",
    "mobile_send_message",
    "application_submit",
    "submit_job_application",
    "career_application_submit",
    "career_offer_confirm",
    "career_spreadsheet_sync",
}

MEDIUM_RISK_TOOLS: Set[str] = {
    "browser_click",
    "browser_type",
    "create_calendar_event",
    "document_creator",
    "create_word_document",
    "create_pdf_document",
    "create_excel_document",
    "git_commit",
    "git_push",
}

LOW_RISK_TOOLS: Set[str] = {
    "web_search",
    "fetch_page",
    "fetch_raw",
    "browser_open_url",
    "browser_read_page",
    "browser_screenshot",
    "fast_file_search",
    "grep_search",
    "file_search",
}

SAFE_TOOLS: Set[str] = {
    "file_read",
    "file_list",
    "help",
    "status",
    "doctor",
    "system_health",
    "memory_get",
    "memory_search",
    "memory_list",
    "list_tools",
    "get_system_status",
    "get_workspace_tree",
}


@dataclass
class PermissionRequest:
    """First-class permission request presented to user or evaluated by policy."""

    request_id: str = field(default_factory=lambda: f"perm-{uuid.uuid4().hex[:8]}")
    session_id: str = "default"
    task_id: str = "default"
    tool: str = ""
    action: str = ""
    target: str = ""
    arguments_summary: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    reason: str = ""
    consequence: str = ""
    scope: str = "single_action"
    timestamp: float = field(default_factory=time.time)
    status: str = "pending"  # pending, granted, denied, cancelled
    decision: Optional[PermissionDecision] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "tool": self.tool,
            "action": self.action,
            "target": self.target,
            "arguments_summary": self.arguments_summary,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else str(self.risk_level),
            "reason": self.reason,
            "consequence": self.consequence,
            "scope": self.scope,
            "timestamp": self.timestamp,
            "status": self.status,
            "decision": self.decision.value if self.decision else None,
            "parameters": self.parameters,
        }

    def resolve(self, decision: PermissionDecision) -> None:
        """Resolve the permission request with a decision."""
        self.decision = decision
        if decision in (
            PermissionDecision.ALLOW_ONCE,
            PermissionDecision.ALLOW_SESSION,
            PermissionDecision.ALLOW_TOOL,
            PermissionDecision.ALLOW_TARGET,
        ):
            self.status = "granted"
        elif decision == PermissionDecision.CANCEL:
            self.status = "cancelled"
        else:
            self.status = "denied"

        # Emit permission lifecycle event
        try:
            get_event_bus().publish(
                PermissionEvent(
                    topic=f"permission.{self.status}",
                    request_id=self.request_id,
                    session_id=self.session_id,
                    task_id=self.task_id,
                    tool_name=self.tool,
                    action=self.action,
                    target=self.target,
                    risk_level=self.risk_level.value
                    if isinstance(self.risk_level, RiskLevel)
                    else str(self.risk_level),
                    decision=self.status,
                    reason=self.reason,
                )
            )
        except Exception:
            pass


class PermissionManager:
    """Manages session-level approval cache and evaluates incoming requests."""

    def __init__(self):
        self._session_allowed_tools: Dict[str, Set[str]] = {}  # session_id -> {tool_names}
        self._session_allowed_targets: Dict[str, Set[str]] = {}  # session_id -> {target_paths/urls}
        self._session_allow_all: Set[str] = set()  # session_ids where allow_session is active
        self._interactive_resolver: Optional[Callable[[PermissionRequest], PermissionDecision]] = None

    def set_interactive_resolver(self, resolver: Callable[[PermissionRequest], PermissionDecision]) -> None:
        """Set UI callback to interactively prompt user for permission decision."""
        self._interactive_resolver = resolver

    def classify_risk(self, tool_name: str, args: Dict[str, Any]) -> RiskLevel:
        """Classify operation risk level based on tool characteristics and arguments."""
        clean_name = tool_name.strip().lower()
        if clean_name in CRITICAL_TOOLS:
            return RiskLevel.CRITICAL
        if clean_name in HIGH_RISK_TOOLS:
            return RiskLevel.HIGH
        if clean_name in MEDIUM_RISK_TOOLS:
            return RiskLevel.MEDIUM
        if clean_name in LOW_RISK_TOOLS:
            return RiskLevel.LOW
        if clean_name in SAFE_TOOLS:
            return RiskLevel.SAFE

        # Dynamic heuristics based on arguments
        target = str(args.get("path") or args.get("command") or args.get("code") or "").lower()
        if any(w in target for w in ("rm -rf", "drop", "delete", "format", "system32", "sudo")):
            return RiskLevel.CRITICAL
        if "write" in clean_name or "edit" in clean_name or "modify" in clean_name:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def create_request(
        self,
        tool: str,
        args: Dict[str, Any],
        session_id: str = "default",
        task_id: str = "default",
        reason: str = "",
    ) -> PermissionRequest:
        """Construct a detailed PermissionRequest."""
        risk = self.classify_risk(tool, args)
        target = str(args.get("path") or args.get("url") or args.get("app_name") or args.get("recipient") or "")
        action = str(args.get("action") or tool)

        # Summarize arguments compactly
        arg_keys = list(args.keys())
        if len(arg_keys) <= 3:
            arg_sum = ", ".join(f"{k}={repr(v)[:30]}" for k, v in args.items())
        else:
            arg_sum = f"{len(arg_keys)} parameters ({', '.join(arg_keys[:3])}...)"

        # Formulate consequence
        if risk == RiskLevel.CRITICAL:
            consequence = f"Permanent modification or deletion of system/file resources at '{target or tool}'."
        elif risk == RiskLevel.HIGH:
            consequence = f"Execution of code or external message/file modification affecting '{target or tool}'."
        elif risk == RiskLevel.MEDIUM:
            consequence = f"State change or interaction with external service/application '{target or tool}'."
        else:
            consequence = f"Read or search operation on '{target or tool}'."

        req = PermissionRequest(
            session_id=session_id,
            task_id=task_id,
            tool=tool,
            action=action,
            target=target,
            arguments_summary=arg_sum,
            risk_level=risk,
            reason=reason or f"Execute tool '{tool}' with assigned risk level {risk.value}.",
            consequence=consequence,
            parameters=args,
        )

        # Publish request event
        try:
            get_event_bus().publish(
                PermissionEvent(
                    topic="permission.requested",
                    request_id=req.request_id,
                    session_id=session_id,
                    task_id=task_id,
                    tool_name=tool,
                    action=action,
                    target=target,
                    risk_level=risk.value,
                    decision="pending",
                    reason=req.reason,
                )
            )
        except Exception:
            pass

        return req

    def is_pre_approved(self, session_id: str, tool: str, target: str = "") -> bool:
        """Check if action is already covered by a session-level approval decision or global allow_all policy."""
        import os
        from brjarvis.security.permissions import PERMISSIONS, PermissionMode

        env_mode = os.environ.get("JARVIS_PERMISSION_MODE", "").strip().lower()
        if (
            PERMISSIONS.mode == PermissionMode.ALLOW_ALL
            or env_mode in ("auto", "allow_all", "allow", "off", "none", "yolo", "allowall")
        ):
            return True

        if session_id in self._session_allow_all:
            return True
        if session_id in self._session_allowed_tools and tool in self._session_allowed_tools[session_id]:
            return True
        if (
            target
            and session_id in self._session_allowed_targets
            and target in self._session_allowed_targets[session_id]
        ):
            return True
        return False

    def record_decision(self, session_id: str, req: PermissionRequest, decision: PermissionDecision) -> None:
        """Record granted session-level permission scopes."""
        req.resolve(decision)
        if decision == PermissionDecision.ALLOW_SESSION:
            self._session_allow_all.add(session_id)
        elif decision == PermissionDecision.ALLOW_TOOL:
            if session_id not in self._session_allowed_tools:
                self._session_allowed_tools[session_id] = set()
            self._session_allowed_tools[session_id].add(req.tool)
        elif decision == PermissionDecision.ALLOW_TARGET and req.target:
            if session_id not in self._session_allowed_targets:
                self._session_allowed_targets[session_id] = set()
            self._session_allowed_targets[session_id].add(req.target)


# Global singleton
_GLOBAL_PERMISSION_MANAGER: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    global _GLOBAL_PERMISSION_MANAGER
    if _GLOBAL_PERMISSION_MANAGER is None:
        _GLOBAL_PERMISSION_MANAGER = PermissionManager()
    return _GLOBAL_PERMISSION_MANAGER
