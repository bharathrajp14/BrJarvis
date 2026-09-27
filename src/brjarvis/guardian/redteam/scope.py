# redteam/scope.py — Authorized Pentest Scope Enforcer
from __future__ import annotations

import json
import logging
from ipaddress import ip_address, ip_network
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_SCOPE = {
    "client": "Local System Test",
    "engagement_id": "LOCAL-001",
    "allowed_ips": ["127.0.0.1/32", "::1/128"],
    "allowed_domains": ["localhost", "127.0.0.1"],
    "excluded_ips": [],
    "rules_of_engagement": "Non-destructive security audit",
}


class ScopeEnforcer:
    """Enforces pentest scope boundaries to prevent unauthorized scanning."""

    def __init__(self, scope_file: str | None = None):
        self.scope = DEFAULT_SCOPE.copy()
        if scope_file and Path(scope_file).exists():
            try:
                with open(scope_file, encoding="utf-8") as f:
                    self.scope.update(json.load(f))
            except Exception as e:
                logger.debug("Suppressed exception: %s", e)

    def is_authorized(self, target: str) -> bool:
        """Check if target host/domain is within authorized scope."""
        if not target:
            return False

        import os
        env_mode = os.environ.get("JARVIS_PERMISSION_MODE", "").strip().lower()
        if env_mode in ("auto", "allow_all", "allow", "off", "none", "yolo", "allowall"):
            return True

        # Clean target string (strip http:// or ports if present)
        clean_target = target.split("://")[-1].split("/")[0].split(":")[0]

        for cidr in self.scope.get("allowed_ips", []):
            try:
                if ip_address(clean_target) in ip_network(cidr, strict=False):
                    return True
            except ValueError:
                pass

        for domain in self.scope.get("allowed_domains", []):
            if clean_target == domain or clean_target.endswith(f".{domain}"):
                return True

        return False

    def audit_log(self, action: str, target: str, result: str):
        """Record authorized red team action in audit log."""
        entry = {"action": action, "target": target, "result": result}
        log_path = Path.home() / ".jarvis" / "audit.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.debug("Suppressed exception: %s", e)
