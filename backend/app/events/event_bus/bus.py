"""
EventBus implementation for Section 11: Event Bus Architecture.

Loosely coupled asynchronous Publish/Subscribe event bus for platform event dispatch.
"""
import inspect
import asyncio
import logging
from typing import Dict, List, Callable, Awaitable, Any, Set, Optional
from collections import defaultdict

from app.events.schemas.events import PlatformEvent

logger = logging.getLogger("backend.events.bus")

HandlerType = Callable[[PlatformEvent], Awaitable[None]]


class EventBus:
    """Centralized, asynchronous Publish/Subscribe Event Bus."""

    _instance: Optional["EventBus"] = None
    
    def __init__(self):
        self._subscribers: Dict[str, List[HandlerType]] = defaultdict(list)
        self._wildcard_subscribers: List[HandlerType] = []
        self._history: List[PlatformEvent] = []

    @classmethod
    def get_instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, topic_or_event_type: str, handler: HandlerType) -> None:
        """Subscribe an async handler function to a topic or specific event_type."""
        if topic_or_event_type == "*":
            self._wildcard_subscribers.append(handler)
        else:
            self._subscribers[topic_or_event_type].append(handler)
        logger.debug(f"EventBus: Subscribed handler '{handler.__name__}' to '{topic_or_event_type}'")

    def unsubscribe(self, topic_or_event_type: str, handler: HandlerType) -> None:
        """Unsubscribe handler."""
        if topic_or_event_type == "*":
            if handler in self._wildcard_subscribers:
                self._wildcard_subscribers.remove(handler)
        else:
            if handler in self._subscribers[topic_or_event_type]:
                self._subscribers[topic_or_event_type].remove(handler)

    async def publish(self, event: PlatformEvent) -> None:
        """Publish a PlatformEvent to all matched subscribers asynchronously."""
        self._history.append(event)
        if len(self._history) > 1000:
            self._history.pop(0)

        logger.info(f"EventBus: Published event '{event.event_type}' (ID: '{event.event_id}', Topic: '{event.topic}')")

        handlers_to_call: Set[HandlerType] = set()

        # Match by specific event_type
        handlers_to_call.update(self._subscribers.get(event.event_type, []))
        # Match by topic
        handlers_to_call.update(self._subscribers.get(event.topic, []))
        # Match wildcards
        handlers_to_call.update(self._wildcard_subscribers)

        for handler in handlers_to_call:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"EventBus handler '{handler.__name__}' error processing '{event.event_type}': {str(e)}")

    def get_history(self, limit: int = 50) -> List[PlatformEvent]:
        """Fetch recent published events."""
        return self._history[-limit:]


# Global singleton instance
event_bus = EventBus.get_instance()
