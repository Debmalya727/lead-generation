"""
BaseMeetingAdapter — Abstract Base Class for Video Conferencing Meeting Adapters.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MeetingMetadata(BaseModel):
    meeting_id: str
    title: str
    platform: str
    attendees: List[str] = Field(default_factory=list)
    status: str = "connected"


class BaseMeetingAdapter(ABC):
    """ABC for video conferencing platform adapters (Google Meet, Teams, Zoom)."""

    def __init__(self, meeting_url: str, bot_name: str = "LeadForgeAI Assistant"):
        self.meeting_url = meeting_url
        self.bot_name = bot_name

    @property
    @abstractmethod
    def platform_id(self) -> str:
        """Platform string ID."""
        ...

    @abstractmethod
    async def connect_meeting(self) -> MeetingMetadata:
        """Connect bot to video conferencing session."""
        ...

    @abstractmethod
    async def disconnect_meeting(self) -> bool:
        """Disconnect bot from session."""
        ...
