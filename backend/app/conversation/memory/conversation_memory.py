"""
ConversationMemoryManager for Phase 12: Enterprise Conversational CRM.

Manages active company context, filter memory, recent workflows, and active reports across user sessions.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from bson import ObjectId

from app.database.mongodb.collections.agent_conversation import ConversationMemoryDocument

logger = logging.getLogger("backend.conversation.memory")


class ConversationMemoryManager:
    """Manager handling conversation context memory persistence."""

    async def get_memory(self, session_id: str, owner_id: str) -> ConversationMemoryDocument:
        """Fetch or create conversation memory document for session."""
        doc = await ConversationMemoryDocument.find_one(
            ConversationMemoryDocument.session_id == session_id,
        )
        if not doc:
            owner_obj_id = ObjectId(owner_id) if ObjectId.is_valid(owner_id) else ObjectId()
            doc = ConversationMemoryDocument(
                memory_id=f"mem_{session_id}",
                session_id=session_id,
                owner_id=owner_obj_id,
                current_company=None,
                previous_filters={},
                recent_workflows=[],
                active_reports=[],
                persistent_context={},
                updated_at=datetime.now(timezone.utc),
            )
            await doc.insert()
        return doc

    async def update_memory(
        self,
        session_id: str,
        owner_id: str,
        current_company: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
        report_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> ConversationMemoryDocument:
        """Update active memory state."""
        mem = await self.get_memory(session_id, owner_id)

        if current_company:
            mem.current_company = current_company

        if filters:
            mem.previous_filters.update(filters)

        if workflow_id:
            if workflow_id not in mem.recent_workflows:
                mem.recent_workflows.insert(0, workflow_id)
                mem.recent_workflows = mem.recent_workflows[:10]  # Keep 10

        if report_id:
            if report_id not in mem.active_reports:
                mem.active_reports.insert(0, report_id)
                mem.active_reports = mem.active_reports[:10]

        if context_data:
            mem.persistent_context.update(context_data)

        mem.updated_at = datetime.now(timezone.utc)
        await mem.save()
        logger.info(f"ConversationMemoryManager: Updated memory for session '{session_id}' (company='{mem.current_company}')")
        return mem

    async def clear_memory(self, session_id: str, owner_id: str) -> None:
        """Clear memory state for session."""
        mem = await self.get_memory(session_id, owner_id)
        mem.current_company = None
        mem.previous_filters = {}
        mem.recent_workflows = []
        mem.active_reports = []
        mem.persistent_context = {}
        mem.updated_at = datetime.now(timezone.utc)
        await mem.save()
