"""
Beanie MongoDB Document collections for Phase 12: Enterprise Conversational CRM.

Collections:
- ConversationSessionDocument (conversation_sessions)
- ConversationMessageDocument (conversation_messages)
- ConversationMemoryDocument (conversation_memory)
- ConversationFeedbackDocument (conversation_feedback)
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class ConversationSessionDocument(Document):
    """Document tracking a conversation session."""

    session_id: str = Field(..., description="Unique session identifier e.g. sess_123")
    title: str = Field("New Conversation", description="Session title")
    owner_id: PydanticObjectId = Field(..., description="User ID owner")
    
    is_pinned: bool = Field(False)
    is_archived: bool = Field(False)
    
    active_company_name: Optional[str] = None
    active_workflow_id: Optional[str] = None
    last_intent: Optional[str] = None
    
    message_count: int = Field(0, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversation_sessions"
        indexes = [
            [("session_id", 1)],
            [("owner_id", 1), ("is_archived", 1), ("updated_at", -1)],
            [("created_at", -1)],
        ]


class ConversationMessageDocument(Document):
    """Document tracking an individual chat message in a session."""

    message_id: str = Field(..., description="Unique message ID e.g. msg_123")
    session_id: str = Field(..., description="Parent session ID")
    owner_id: PydanticObjectId = Field(..., description="User ID owner")
    
    role: str = Field(..., description="user | assistant | system")
    content: str = Field(..., description="Raw text or markdown content")
    
    intent: Optional[str] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    
    execution_id: Optional[str] = Field(None, description="Linked WorkflowExecution ID if executed")
    action_cards: List[Dict[str, Any]] = Field(default_factory=list)
    execution_visualization: Dict[str, Any] = Field(default_factory=dict)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversation_messages"
        indexes = [
            [("session_id", 1), ("timestamp", 1)],
            [("message_id", 1)],
            [("owner_id", 1)],
        ]


class ConversationMemoryDocument(Document):
    """Document persisting conversational state memory for context retention."""

    memory_id: str = Field(..., description="Unique memory ID")
    session_id: str = Field(..., description="Parent session ID")
    owner_id: PydanticObjectId = Field(..., description="User ID owner")
    
    current_company: Optional[str] = None
    previous_filters: Dict[str, Any] = Field(default_factory=dict)
    recent_workflows: List[str] = Field(default_factory=list)
    active_reports: List[str] = Field(default_factory=list)
    
    persistent_context: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversation_memory"
        indexes = [
            [("session_id", 1)],
            [("owner_id", 1)],
        ]


class ConversationFeedbackDocument(Document):
    """Document storing user feedback ratings & notes on AI responses."""

    feedback_id: str = Field(..., description="Unique feedback record ID")
    session_id: str = Field(..., description="Parent session ID")
    message_id: str = Field(..., description="Target message ID")
    owner_id: PydanticObjectId = Field(..., description="User ID owner")
    
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating or 1/-1 thumb rating")
    comments: Optional[str] = None
    category: str = Field("general", description="accuracy | helpfulness | formatting | speed")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversation_feedback"
        indexes = [
            [("session_id", 1)],
            [("message_id", 1)],
            [("owner_id", 1)],
        ]
