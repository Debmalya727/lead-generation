"""
Pydantic v2 Schemas for Enterprise Conversational CRM.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Existing session ID or null for auto-creation")
    message: str = Field(..., description="User text prompt or slash command e.g. '/research Acme'")
    company_name: Optional[str] = Field(None, description="Target company override if specified")
    context_overrides: Dict[str, Any] = Field(default_factory=dict)


class ActionCard(BaseModel):
    title: str
    description: str
    action_type: str = Field("run_workflow", description="run_workflow | open_report | export_csv | research | outreach")
    payload: Dict[str, Any] = Field(default_factory=dict)
    button_label: str = "Execute"


class ChatMessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    intent: Optional[str] = None
    confidence: float = 1.0
    entities: Dict[str, Any] = Field(default_factory=dict)
    execution_id: Optional[str] = None
    action_cards: List[ActionCard] = Field(default_factory=list)
    execution_visualization: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    is_pinned: bool = False
    is_archived: bool = False
    active_company_name: Optional[str] = None
    last_intent: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class ChatSessionListResponse(BaseModel):
    total_count: int
    items: List[ChatSessionResponse]


class ChatFeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None
    category: str = "general"


class ChatFeedbackResponse(BaseModel):
    feedback_id: str
    session_id: str
    message_id: str
    rating: int
    created_at: datetime
