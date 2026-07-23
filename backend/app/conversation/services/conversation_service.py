"""
ConversationService for Phase 12: Enterprise Conversational CRM.
"""
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from bson import ObjectId

from app.conversation.manager.conversation_manager import ConversationManager
from app.conversation.sessions.session_manager import SessionManager
from app.conversation.streaming.stream_manager import ChatStreamingManager
from app.database.mongodb.collections.agent_conversation import (
    ConversationSessionDocument,
    ConversationMessageDocument,
    ConversationFeedbackDocument,
)

logger = logging.getLogger("backend.conversation.service")


class ConversationService:
    """Service layer wrapping enterprise chat operations."""

    def __init__(self):
        self.manager = ConversationManager()
        self.session_manager = SessionManager()
        self.stream_manager = ChatStreamingManager()

    async def chat(
        self,
        owner_id: str,
        message: str,
        session_id: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Tuple[ConversationMessageDocument, ConversationSessionDocument]:
        """Process user message and return assistant response message."""
        return await self.manager.process_user_message(
            owner_id=owner_id,
            user_text=message,
            session_id=session_id,
            company_override=company_name,
        )

    async def stream_chat(
        self,
        owner_id: str,
        message: str,
        session_id: Optional[str] = None,
        company_name: Optional[str] = None,
    ):
        """Process user message and yield SSE stream events."""
        assistant_msg, session = await self.chat(owner_id, message, session_id, company_name)
        
        return self.stream_manager.stream_chat_response(
            session_id=session.session_id,
            user_message=message,
            company_name=company_name or session.active_company_name or "Target Company",
            intent=assistant_msg.intent or "company_research",
            final_markdown=assistant_msg.content,
            action_cards=assistant_msg.action_cards,
            execution_id=assistant_msg.execution_id,
        )

    async def list_sessions(self, owner_id: str, limit: int = 50, skip: int = 0) -> Tuple[List[ConversationSessionDocument], int]:
        """List conversation sessions for user."""
        return await self.session_manager.list_sessions(owner_id, limit=limit, skip=skip)

    async def get_session(self, session_id: str, owner_id: str) -> Optional[ConversationSessionDocument]:
        """Get session details."""
        return await self.session_manager.get_session(session_id, owner_id)

    async def get_history(self, session_id: str, limit: int = 50) -> List[ConversationMessageDocument]:
        """Get message history for session."""
        return await self.manager.get_history(session_id, limit=limit)

    async def delete_session(self, session_id: str, owner_id: str) -> bool:
        """Delete session."""
        return await self.session_manager.delete_session(session_id, owner_id)

    async def submit_feedback(
        self,
        owner_id: str,
        session_id: str,
        message_id: str,
        rating: int,
        comments: Optional[str] = None,
        category: str = "general",
    ) -> ConversationFeedbackDocument:
        """Submit feedback for an AI message."""
        owner_obj_id = ObjectId(owner_id) if ObjectId.is_valid(owner_id) else ObjectId()
        doc = ConversationFeedbackDocument(
            feedback_id=f"fb_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            message_id=message_id,
            owner_id=owner_obj_id,
            rating=rating,
            comments=comments,
            category=category,
            created_at=datetime.now(timezone.utc),
        )
        await doc.insert()
        return doc
