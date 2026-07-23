"""
REST API Router for Notification Center.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.database.mongodb.collections.user import User
from app.notifications.notification_center import notification_center

router = APIRouter()


class MarkReadRequest(BaseModel):
    notification_ids: List[str]


@router.get(
    "/notifications",
    summary="List User Notifications",
    description="Fetches notifications for current user.",
)
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50),
    current_user: User = Depends(get_current_user),
):
    """List notifications for current user."""
    return await notification_center.list_notifications(
        recipient_id=str(current_user.id),
        unread_only=unread_only,
        limit=limit,
    )


@router.post(
    "/notifications/read",
    summary="Mark Notifications Read",
    description="Marks notifications as read.",
)
async def mark_read(payload: MarkReadRequest, current_user: User = Depends(get_current_user)):
    """Mark notifications as read."""
    count = await notification_center.mark_as_read(
        notification_ids=payload.notification_ids,
        recipient_id=str(current_user.id),
    )
    return {"marked_count": count}
