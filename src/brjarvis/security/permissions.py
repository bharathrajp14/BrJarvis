"""Permission policy & deterministic security engine for BR JARVIS.

Enforces deterministic 6-tuple policy evaluation:
(User, Device, Application, Resource, Action, Risk) -> ActionDecision

Preserves historical top-level permissions interface for backwards compatibility:
- ALLOW_ALL permits tools except explicit deny-list entries.
- CONFIRM_DESTRUCTIVE prompts for confirmation on destructive tools.
- CONFIRM_ALL only permits safe read-only tools in ALWAYS_ALLOWED.
- DENY_ALL blocks everything except explicit allow-list entries.
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, FrozenSet, Optional, Set, Union

from brjarvis.security.path_policy import (
    CRITICAL_RESOURCE_DENYLIST as SEC_CRITICAL_DENYLIST,
)
from brjarvis.security.path_policy import (
    PathTier as SecPathTier,
)
from brjarvis.security.path_policy import (
    get_path_policy,
)
from brjarvis.security.policy_engine import (
    PermissionMode as SecPermissionMode,
)
from brjarvis.security.policy_engine import (
    PolicyContext as SecPolicyContext,
)
from brjarvis.security.policy_engine import (
    PolicyEngine,
)

logger = logging.getLogger("JARVIS.Permissions")


class PermissionMode(str, Enum):
    ALLOW_ALL = "allow_all"
    CONFIRM_DESTRUCTIVE = "confirm_destructive"
    CONFIRM_ALL = "confirm_all"
    DENY_ALL = "deny_all"


def _normalize_mode(mode: Any) -> PermissionMode:
    """Normalize a mode string, enum, or None; default to confirmation for side effects."""
    if not mode:
        env_val = os.environ.get("JARVIS_PERMISSION_MODE")
        if env_val:
            val = env_val.strip().lower()
            if val in ("auto", "allow_all", "allow", "off", "none", "yolo", "allowall"):
                return PermissionMode.ALLOW_ALL
            elif val in ("confirm_all", "all"):
                return PermissionMode.CONFIRM_ALL
            elif val in ("deny", "deny_all"):
                return PermissionMode.DENY_ALL
            elif val in ("confirm_destructive", "confirm", "plan", "accept_edits"):
                return PermissionMode.CONFIRM_DESTRUCTIVE
        return PermissionMode.CONFIRM_DESTRUCTIVE
    if isinstance(mode, PermissionMode):
        return mode
    val = str(mode).strip().lower()
    if val in ("auto", "allow_all", "allow", "off", "none", "yolo", "allowall"):
        return PermissionMode.ALLOW_ALL
    elif val in ("confirm_all", "all"):
        return PermissionMode.CONFIRM_ALL
    elif val in ("deny", "deny_all"):
        return PermissionMode.DENY_ALL
    elif val in ("confirm_destructive", "confirm", "plan", "accept_edits"):
        return PermissionMode.CONFIRM_DESTRUCTIVE
    try:
        return PermissionMode(val)
    except Exception:
        return PermissionMode.CONFIRM_DESTRUCTIVE


DESTRUCTIVE_TOOLS: Set[str] = {
    "run_code",
    "file_delete",
    "process_kill",
    "delete_file",
    "kill_process",
    "force_kill_process",
    "run_powershell",
    "run_bash",
}


class ActionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    CONFIRM = "confirm"
    ALLOW_FOR_SESSION = "allow_for_session"
    ALLOW_FOR_DEVICE = "allow_for_device"
    ALLOW_FOR_APPLICATION = "allow_for_application"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


PolicyContext = SecPolicyContext

ALWAYS_ALLOWED: FrozenSet[str] = frozenset(
    {
        "get_system_status",
        "get_workspace_tree",
        "list_directory",
        "read_file",
        "grep_search",
        "find_by_name",
        "fetch_url",
        "web_search",
        "take_screenshot",
        "get_cursor_position",
        "list_windows",
        "get_active_window",
        "get_window_bounds",
        "get_accessibility_tree",
        "ocr_screen",
        "locate_on_screen",
        "query_memory",
        "get_recent_context",
        "list_tools",
        "doctor",
        "system_health",
    }
)

ALWAYS_CONFIRM: FrozenSet[str] = frozenset(
    {
        "delete_file",
        "force_kill_process",
        "kill_process",
        "run_powershell",
        "run_bash",
        "write_file",
        "modify_file",
        "system_shutdown",
        "system_restart",
        "press_key_combination",
        "mouse_click",
        "mouse_drag",
    }
)

CRITICAL_RESOURCE_DENYLIST: FrozenSet[str] = SEC_CRITICAL_DENYLIST


class PermissionPolicy:
    """Historical permissions interface wrapping deterministic PolicyEngine."""

    def __init__(
        self,
        mode: Optional[Union[PermissionMode, str]] = None,
        deny_names: Optional[FrozenSet[str]] = None,
        allow_names: Optional[FrozenSet[str]] = None,
    ):
        init_mode = _normalize_mode(mode)
        self._engine: PolicyEngine = PolicyEngine(
            mode=SecPermissionMode(init_mode.value),
            deny_names=deny_names,
            allow_names=allow_names,
        )

    @property
    def mode(self) -> PermissionMode:
        return PermissionMode(self._engine.mode.value)

    @mode.setter
    def mode(self, val: Union[PermissionMode, str]) -> None:
        self.set_mode(val)

    def set_mode(self, mode: Union[PermissionMode, str]) -> None:
        norm = _normalize_mode(mode)
        self._engine.set_mode(SecPermissionMode(norm.value))
        os.environ["JARVIS_PERMISSION_MODE"] = norm.value.upper()

    def evaluate(self, ctx: PolicyContext) -> ActionDecision:
        dec = self._engine.evaluate(ctx)
        return ActionDecision(dec.value)

    def check(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> bool:
        if tool_name in (
            "DEFAULT",
            "READ_ONLY",
            "none",
            "",
            "file_read",
            "file_list",
            "read_file",
            "get_window_bounds",
        ):
            return True
        return self._engine.check(tool_name, args)

    def request_confirmation(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> bool:
        return self._engine.request_confirmation(tool_name, args)


def _build_global_policy(mode: Optional[Union[PermissionMode, str]] = None) -> PermissionPolicy:
    return PermissionPolicy(mode=mode)


PERMISSIONS: PermissionPolicy = PermissionPolicy()


def check_permission(tool_name: str, args: Optional[Dict[str, Any]] = None) -> bool:
    return PERMISSIONS.check(tool_name, args)


def request_confirmation(tool_name: str, args: Optional[Dict[str, Any]] = None) -> bool:
    return PERMISSIONS.request_confirmation(tool_name, args)


def evaluate_action_policy(
    action: str,
    resource: str = "",
    device: str = "pc_primary",
    application: str = "system",
    user: str = "default_user",
    risk: RiskLevel = RiskLevel.LOW,
    args: Optional[Dict[str, Any]] = None,
) -> ActionDecision:
    """Public helper to evaluate a full 6-tuple policy decision."""
    try:
        ctx = PolicyContext(
            user=user,
            device=device,
            application=application,
            resource=resource,
            action=action,
            risk=risk,
            metadata=args or {},
        )
        return PERMISSIONS.evaluate(ctx)
    except Exception as exc:
        logger.error("evaluate_action_policy failed closed (DENY): %s", exc)
        return ActionDecision.DENY


class PathTier(Enum):
    TIER_0_WORKSPACE = 0
    TIER_1_USER_PROFILE = 1
    TIER_2_CRITICAL_SECRETS = 2


TIER_2_PATTERNS = CRITICAL_RESOURCE_DENYLIST


class PathPolicy:
    """Evaluates file paths against Tier 0 (Workspace), Tier 1 (Profile), Tier 2 (Critical/Secrets)."""

    @classmethod
    def get_tier(cls, path_input: Union[str, Path]) -> PathTier:
        sec_policy = get_path_policy()
        sec_tier = sec_policy.get_tier(path_input)
        if sec_tier == SecPathTier.TIER_2_CRITICAL_SECRETS:
            return PathTier.TIER_2_CRITICAL_SECRETS
        elif sec_tier == SecPathTier.TIER_0_WORKSPACE:
            return PathTier.TIER_0_WORKSPACE
        return PathTier.TIER_1_USER_PROFILE

    @classmethod
    def allow_cloud_context(cls, path_input: Union[str, Path]) -> bool:
        """Return True if path is safe to send to cloud LLMs (Tier 0 or Tier 1). Return False for Tier 2."""
        try:
            return get_path_policy().allow_cloud_context(path_input)
        except Exception:
            return False


def cloud_context_exclusion_check(path_input: Union[str, Path]) -> bool:
    """Helper function to verify if file path is permitted in cloud prompt payload."""
    return PathPolicy.allow_cloud_context(path_input)


def _load_scope_defaults() -> Dict[str, Any]:
    """Helper to return default scope settings."""
    env_mode = os.environ.get("JARVIS_PERMISSION_MODE", "").strip().lower()
    if env_mode in ("auto", "allow_all", "allow", "off", "none", "yolo", "allowall"):
        return {
            "workspace_only": False,
            "allow_terminal": True,
            "allow_web": True,
            "allow_system_commands": True,
        }
    return {
        "workspace_only": True,
        "allow_terminal": False,
        "allow_web": True,
        "allow_system_commands": False,
    }
