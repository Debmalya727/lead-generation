"""
REST API Router for Enterprise Conversational CRM.
"""
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, get_conversation_service
from app.database.mongodb.collections.user import User
from app.conversation.services.conversation_service import ConversationService
from app.conversation.models.conversation import (
    ChatRequest,
    ChatMessageResponse,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatFeedbackRequest,
    ChatFeedbackResponse,
)

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Chat Message",
    description="Processes natural language or slash commands via Intent Engine, Conversation Planner, and Workflow Engine.",
)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    """Process user chat message."""
    msg_doc, session = await service.chat(
        owner_id=str(current_user.id),
        message=payload.message,
        session_id=payload.session_id,
        company_name=payload.company_name,
    )
    return msg_doc


@router.post(
    "/chat/stream",
    summary="Stream Chat Response (SSE)",
    description="Streams real-time thinking, planning, and execution stages via Server-Sent Events (SSE).",
)
async def stream_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    """Stream chat response as Server-Sent Events."""
    generator = await service.stream_chat(
        owner_id=str(current_user.id),
        message=payload.message,
        session_id=payload.session_id,
        company_name=payload.company_name,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@router.get(
    "/chat/sessions",
    response_model=ChatSessionListResponse,
    summary="List Chat Sessions",
)
async def list_sessions(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    """List conversation sessions for authenticated user."""
    items, total = await service.list_sessions(owner_id=str(current_user.id), limit=limit, skip=skip)
    return ChatSessionListResponse(
        total_count=total,
        items=[ChatSessionResponse(**s.model_dump()) for s in items],
    )


@router.get(
    "/chat/history",
    response_model=List[ChatMessageResponse],
    summary="Get Message History",
)
async def get_history(
    session_id: str = Query(..., description="Target session ID"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    """Fetch chronological message history for a session."""
    return await service.get_history(session_id=session_id, limit=limit)


@router.get(
    "/chat/session/{session_id}",
    response_model=ChatSessionResponse,
    summary="Get Session Details",
)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    """Get session details."""
    session = await service.get_session(session_id, str(current_user.id))
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session '{session_id}' not found.")
    return session


@router.delete(
    "/chat/session/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Session",
)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    """Delete a conversation session and history."""
    success = await service.delete_session(session_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session '{session_id}' not found.")
    return {"status": "deleted", "session_id": session_id}


@router.post(
    "/chat/feedback",
    response_model=ChatFeedbackResponse,
    summary="Submit Message Feedback",
)
async def submit_feedback(
    payload: ChatFeedbackRequest,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    """Submit user feedback for an AI assistant message."""
    fb = await service.submit_feedback(
        owner_id=str(current_user.id),
        session_id=payload.session_id,
        message_id=payload.message_id,
        rating=payload.rating,
        comments=payload.comments,
        category=payload.category,
    )
    return fb
