"""
EventPublisher helper for publishing platform lifecycle events to EventBus.
"""
import logging
from typing import Dict, Any, Optional

from app.events.event_bus.bus import event_bus
from app.events.schemas.events import PlatformEvent

logger = logging.getLogger("backend.events.publisher")


class EventPublisher:
    """Helper publisher class for publishing platform events."""

    @classmethod
    async def publish_event(
        cls,
        event_cls: type,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> PlatformEvent:
        """Instantiate and publish a PlatformEvent."""
        event_obj = event_cls(
            user_id=user_id,
            correlation_id=correlation_id,
            payload=payload or {},
        )
        await event_bus.publish(event_obj)
        return event_obj
