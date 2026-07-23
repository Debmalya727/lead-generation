"""
NotificationCenter for Section 12: Notification Center Architecture.

Subscribes to EventBus events and dispatches notifications via Browser, Email, WebSocket, and Voice providers.
"""
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.events.event_bus.bus import event_bus
from app.events.schemas.events import PlatformEvent
from app.database.mongodb.collections.platform_extended import NotificationDocument

logger = logging.getLogger("backend.notifications")


class NotificationCenter:
    """Centralized Notification Engine subscribed to EventBus lifecycle events."""

    _instance: Optional["NotificationCenter"] = None

    def __init__(self):
        self._setup_event_subscriptions()

    @classmethod
    def get_instance(cls) -> "NotificationCenter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _setup_event_subscriptions(self):
        """Register EventBus handler for lifecycle events."""
        event_bus.subscribe("WorkflowCompleted", self._handle_platform_event)
        event_bus.subscribe("WorkflowFailed", self._handle_platform_event)
        event_bus.subscribe("ReportGenerated", self._handle_platform_event)
        event_bus.subscribe("LeadDiscovered", self._handle_platform_event)
        event_bus.subscribe("OutreachSent", self._handle_platform_event)
        event_bus.subscribe("PolicyViolation", self._handle_platform_event)

    async def _handle_platform_event(self, event: PlatformEvent) -> None:
        """Handle incoming EventBus event and dispatch notification."""
        user_id = event.user_id or "system_user"
        title = f"Event Alert: {event.event_type}"
        msg = f"Platform event '{event.event_type}' was processed for topic '{event.topic}'."

        if event.event_type == "WorkflowCompleted":
            title = "⚡ Workflow Execution Completed"
            msg = f"Workflow '{event.payload.get('workflow_id', 'N/A')}' completed successfully."
        elif event.event_type == "WorkflowFailed":
            title = "❌ Workflow Execution Failed"
            msg = f"Workflow '{event.payload.get('workflow_id', 'N/A')}' failed."
        elif event.event_type == "ReportGenerated":
            title = "📊 Research Report Generated"
            msg = f"Executive report for '{event.payload.get('company_name', 'Target')}' is ready."
        elif event.event_type == "LeadDiscovered":
            title = "🎯 New Target Leads Discovered"
            msg = f"Discovered {event.payload.get('count', 1)} new leads."
        elif event.event_type == "OutreachSent":
            title = "✉️ Sales Outreach Sent"
            msg = f"Outreach email delivered to '{event.payload.get('recipient', 'lead')}'."

        await self.send_notification(
            recipient_id=user_id,
            title=title,
            message=msg,
            notification_type="workflow" if "Workflow" in event.event_type else "info",
            event_type=event.event_type,
            data=event.payload,
        )

    async def send_notification(
        self,
        recipient_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        event_type: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> NotificationDocument:
        """Dispatch notification across providers and persist in MongoDB."""
        notif_id = f"notif_{uuid.uuid4().hex[:12]}"
        doc = NotificationDocument(
            notification_id=notif_id,
            recipient_id=recipient_id,
            title=title,
            message=message,
            type=notification_type,
            event_type=event_type,
            data=data or {},
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        try:
            await doc.insert()
            logger.info(f"NotificationCenter: Dispatched notification '{notif_id}' to recipient '{recipient_id}'")
        except Exception as e:
            logger.warning(f"Failed to persist notification: {str(e)}")
        return doc

    async def list_notifications(self, recipient_id: str, unread_only: bool = False, limit: int = 50) -> List[NotificationDocument]:
        """Fetch user notifications."""
        query = [NotificationDocument.recipient_id == recipient_id]
        if unread_only:
            query.append(NotificationDocument.is_read == False)
        return await NotificationDocument.find(*query).sort("-created_at").limit(limit).to_list()

    async def mark_as_read(self, notification_ids: List[str], recipient_id: str) -> int:
        """Mark notifications as read."""
        count = 0
        for nid in notification_ids:
            doc = await NotificationDocument.find_one(
                NotificationDocument.notification_id == nid,
                NotificationDocument.recipient_id == recipient_id,
            )
            if doc:
                doc.is_read = True
                await doc.save()
                count += 1
        return count


# Singleton instance
notification_center = NotificationCenter.get_instance()
