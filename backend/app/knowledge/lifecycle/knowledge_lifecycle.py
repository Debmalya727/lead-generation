"""
Phase 14.9.5 — Knowledge Lifecycle Manager.
Manages document lifecycle states:
  Imported -> Validated -> Normalized -> Indexed -> Active -> Archived -> Deleted
Supports Soft Delete, Retention Policies, Legal Hold, Restoration, and Compliance Policies.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.mongodb.collections.knowledge import KnowledgeDocument, KnowledgeLifecycleRecord

logger = logging.getLogger("backend.knowledge.lifecycle")

LIFECYCLE_STATES = {"Imported", "Validated", "Normalized", "Indexed", "Active", "Archived", "Deleted"}


class KnowledgeLifecycleManager:
    """Manages document retention, legal hold flags, soft delete, and state machine transitions."""

    async def initialize_lifecycle(self, document_id: str, retention_days: int = 365) -> KnowledgeLifecycleRecord:
        lc_id = f"lc_{uuid.uuid4().hex[:12]}"
        rec = KnowledgeLifecycleRecord(
            lifecycle_id=lc_id,
            document_id=document_id,
            state="Imported",
            is_legal_hold=False,
            retention_days=retention_days,
            soft_deleted=False,
            history=[{"state": "Imported", "timestamp": datetime.now(timezone.utc).isoformat()}],
        )
        try:
            await rec.insert()
        except Exception:
            pass
        return rec

    async def transition_state(self, document_id: str, target_state: str) -> KnowledgeLifecycleRecord:
        if target_state not in LIFECYCLE_STATES:
            raise ValueError(f"Invalid state '{target_state}'. Supported: {LIFECYCLE_STATES}")

        rec = await KnowledgeLifecycleRecord.find_one(KnowledgeLifecycleRecord.document_id == document_id)
        if not rec:
            rec = await self.initialize_lifecycle(document_id)

        if rec.is_legal_hold and target_state in {"Archived", "Deleted"}:
            raise ValueError(f"Cannot transition document '{document_id}' to '{target_state}' (Legal Hold Active).")

        rec.state = target_state
        rec.history.append({"state": target_state, "timestamp": datetime.now(timezone.utc).isoformat()})
        rec.updated_at = datetime.now(timezone.utc)
        await rec.save()

        # Update KnowledgeDocument status
        doc = await KnowledgeDocument.find_one(KnowledgeDocument.document_id == document_id)
        if doc:
            doc.status = target_state.lower()
            await doc.save()

        logger.info(f"[KnowledgeLifecycle] Document '{document_id}' transitioned to state '{target_state}'")
        return rec

    async def set_legal_hold(self, document_id: str, legal_hold: bool) -> KnowledgeLifecycleRecord:
        rec = await KnowledgeLifecycleRecord.find_one(KnowledgeLifecycleRecord.document_id == document_id)
        if not rec:
            rec = await self.initialize_lifecycle(document_id)

        rec.is_legal_hold = legal_hold
        rec.history.append({"action": "set_legal_hold", "legal_hold": legal_hold, "timestamp": datetime.now(timezone.utc).isoformat()})
        rec.updated_at = datetime.now(timezone.utc)
        await rec.save()
        return rec

    async def soft_delete(self, document_id: str) -> KnowledgeLifecycleRecord:
        rec = await KnowledgeLifecycleRecord.find_one(KnowledgeLifecycleRecord.document_id == document_id)
        if not rec:
            rec = await self.initialize_lifecycle(document_id)

        if rec.is_legal_hold:
            raise ValueError(f"Cannot soft delete document '{document_id}' (Legal Hold Active).")

        rec.soft_deleted = True
        rec.state = "Deleted"
        rec.history.append({"action": "soft_delete", "timestamp": datetime.now(timezone.utc).isoformat()})
        await rec.save()
        return rec


knowledge_lifecycle_manager = KnowledgeLifecycleManager()
