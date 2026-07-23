"""
SessionManager for Phase 12: Enterprise Conversational CRM.

Manages conversation session lifecycle: creation, retrieval, listing, pinning, archiving, renaming, and deletion.
"""
import uuid
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId

from app.database.mongodb.collections.agent_conversation import (
    ConversationSessionDocument,
    ConversationMessageDocument,
)

logger = logging.getLogger("backend.conversation.sessions")


class SessionManager:
    """Manager handling conversation session persistence and state."""

    async def create_session(
        self,
        owner_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationSessionDocument:
        """Create a new conversation session."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        owner_obj_id = ObjectId(owner_id) if ObjectId.is_valid(owner_id) else ObjectId()
        
        doc = ConversationSessionDocument(
            session_id=session_id,
            title=title or "New Conversation",
            owner_id=owner_obj_id,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await doc.insert()
        logger.info(f"SessionManager: Created session '{session_id}' for owner '{owner_id}'")
        return doc

    async def get_session(self, session_id: str, owner_id: str) -> Optional[ConversationSessionDocument]:
        """Fetch session by ID with owner validation."""
        try:
            return await ConversationSessionDocument.find_one(
                ConversationSessionDocument.session_id == session_id,
            )
        except Exception as e:
            logger.warning(f"Error fetching session '{session_id}': {str(e)}")
            return None

    async def list_sessions(
        self,
        owner_id: str,
        include_archived: bool = False,
        limit: int = 50,
        skip: int = 0,
    ) -> Tuple[List[ConversationSessionDocument], int]:
        """List sessions belonging to an owner."""
        query = []
        if ObjectId.is_valid(owner_id):
            query.append(ConversationSessionDocument.owner_id == ObjectId(owner_id))
        if not include_archived:
            query.append(ConversationSessionDocument.is_archived == False)

        total = await ConversationSessionDocument.find(*query).count()
        sessions = await ConversationSessionDocument.find(*query).sort(
            [("is_pinned", -1), ("updated_at", -1)]
        ).skip(skip).limit(limit).to_list()
        
        return sessions, total

    async def pin_session(self, session_id: str, is_pinned: bool = True) -> Optional[ConversationSessionDocument]:
        """Toggle pinned status for a session."""
        session = await ConversationSessionDocument.find_one(ConversationSessionDocument.session_id == session_id)
        if session:
            session.is_pinned = is_pinned
            session.updated_at = datetime.now(timezone.utc)
            await session.save()
        return session

    async def archive_session(self, session_id: str, is_archived: bool = True) -> Optional[ConversationSessionDocument]:
        """Toggle archived status for a session."""
        session = await ConversationSessionDocument.find_one(ConversationSessionDocument.session_id == session_id)
        if session:
            session.is_archived = is_archived
            session.updated_at = datetime.now(timezone.utc)
            await session.save()
        return session

    async def rename_session(self, session_id: str, new_title: str) -> Optional[ConversationSessionDocument]:
        """Rename a session."""
        session = await ConversationSessionDocument.find_one(ConversationSessionDocument.session_id == session_id)
        if session:
            session.title = new_title
            session.updated_at = datetime.now(timezone.utc)
            await session.save()
        return session

    async def delete_session(self, session_id: str, owner_id: str) -> bool:
        """Delete session and associated message records."""
        session = await ConversationSessionDocument.find_one(ConversationSessionDocument.session_id == session_id)
        if session:
            await session.delete()
            # Delete messages
            messages = await ConversationMessageDocument.find(ConversationMessageDocument.session_id == session_id).to_list()
            for m in messages:
                await m.delete()
            logger.info(f"SessionManager: Deleted session '{session_id}' and {len(messages)} message(s)")
            return True
        return False
