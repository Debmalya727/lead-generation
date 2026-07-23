"""
RBACEngine for Phase 12.5: Enterprise Platform Hardening.

Manages role definitions, permission mappings, and authorization policy checks.
"""
import logging
from typing import List, Dict, Set, Optional

from app.platform.context.request_context import RequestContext

logger = logging.getLogger("backend.platform.rbac")


class RBACEngine:
    """Engine enforcing Role-Based Access Control policies."""

    ROLE_PERMISSIONS: Dict[str, Set[str]] = {
        "Owner": {"*"},
        "Admin": {"workflow:execute", "workflow:cancel", "tool:execute", "conversation:delete", "system:settings"},
        "Manager": {"workflow:execute", "workflow:cancel", "tool:execute", "conversation:delete"},
        "Sales": {"workflow:execute", "tool:execute"},
        "Viewer": {"read_only"},
    }

    @classmethod
    def has_permission(cls, role: str, required_permission: str) -> bool:
        """Check if role holds required permission."""
        assigned = cls.ROLE_PERMISSIONS.get(role, set())
        if "*" in assigned or required_permission in assigned:
            return True
        return False

    @classmethod
    def authorize(cls, context: RequestContext, required_permission: str) -> bool:
        """Authorize a RequestContext against a required permission constraint."""
        if "*" in context.permissions:
            return True

        if cls.has_permission(context.role, required_permission):
            return True

        if required_permission in context.permissions:
            return True

        logger.warning(f"RBAC Enforcement Denied: Role '{context.role}' lacks permission '{required_permission}' for correlation ID '{context.correlation_id}'")
        return False
