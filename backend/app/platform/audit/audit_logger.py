"""
AuditLogger for Phase 12.5: Enterprise Platform Hardening.

Persists structured audit events to MongoDB audit_logs collection for compliance.
"""
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.database.mongodb.collections.platform import AuditLogDocument
from app.platform.context.request_context import RequestContext

logger = logging.getLogger("backend.platform.audit")


class AuditLogger:
    """Centralized Audit Logging system."""

    async def log_event(
        self,
        event_type: str,
        resource_type: str,
        actor_id: str = "System",
        resource_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        ip_address: Optional[str] = None,
        context: Optional[RequestContext] = None,
    ) -> AuditLogDocument:
        """Log an immutable audit trail record."""
        audit_id = f"aud_{uuid.uuid4().hex[:12]}"
        
        act_id = actor_id
        corr_id = correlation_id
        if context:
            if context.user_id:
                act_id = context.user_id
            if context.correlation_id:
                corr_id = context.correlation_id

        doc = AuditLogDocument(
            audit_id=audit_id,
            event_type=event_type,
            actor_id=act_id,
            correlation_id=corr_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            status=status,
            timestamp=datetime.now(timezone.utc),
        )
        try:
            await doc.insert()
            logger.info(f"AuditLogger logged event '{event_type}' (ID: '{audit_id}', correlation: '{corr_id}')")
        except Exception as e:
            logger.warning(f"Failed to insert AuditLogDocument: {str(e)}")
        return doc

    async def list_audit_logs(
        self,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> tuple[List[AuditLogDocument], int]:
        """Fetch audit log records paginated."""
        query = []
        if event_type:
            query.append(AuditLogDocument.event_type == event_type)
        if actor_id:
            query.append(AuditLogDocument.actor_id == actor_id)

        total = await AuditLogDocument.find(*query).count()
        docs = await AuditLogDocument.find(*query).sort("-timestamp").skip(skip).limit(limit).to_list()
        return docs, total
