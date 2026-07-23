"""
RequestContext for Phase 12.5: Enterprise Platform Hardening.

Carries request scoped metadata, user identity, organization, session, correlation ID, and permissions.
"""
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RequestContext:
    """Dataclass storing unified request-scoped execution context."""

    user_id: Optional[str] = None
    org_id: Optional[str] = "default_org"
    role: str = "Owner"
    permissions: List[str] = field(default_factory=lambda: ["*"])
    
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    
    correlation_id: str = field(default_factory=lambda: f"corr_{uuid.uuid4().hex[:12]}")
    client_type: str = "web"  # web | rest | chat | voice | mobile | sdk | extension
    
    locale: str = "en_US"
    timezone: str = "UTC"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert RequestContext to serializable dictionary."""
        return {
            "user_id": self.user_id,
            "org_id": self.org_id,
            "role": self.role,
            "permissions": self.permissions,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "workflow_id": self.workflow_id,
            "correlation_id": self.correlation_id,
            "client_type": self.client_type,
            "locale": self.locale,
            "timezone": self.timezone,
            "metadata": self.metadata,
        }
