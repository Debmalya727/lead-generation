"""
Beanie MongoDB Document collections for Phase 13.8: Conversational Voice Agents.
Adds 3 collections: voice_agent_personas, voice_agent_sessions, voice_agent_turns.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class VoiceAgentPersonaDocument(Document):
    """Stores voice agent persona configurations and system prompts."""

    persona_id: str = Field(..., description="Unique persona ID")
    name: str = Field(...)
    role: str = Field("Sales SDR", description="Sales SDR | Solutions Architect | Customer Support")
    description: str = Field(...)

    tts_provider: str = Field("elevenlabs")
    tts_voice_id: str = Field("21m00Tcm4TlvDq8ikWAM")
    speed: float = Field(1.0)
    pitch: float = Field(1.0)

    system_prompt: str = Field(...)
    available_tools: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_agent_personas"
        indexes = [
            [("persona_id", 1)],
            [("role", 1)],
        ]


class VoiceAgentSessionDocument(Document):
    """Tracks active conversational voice agent session state and context."""

    session_id: str = Field(..., description="Unique voice agent session ID")
    persona_id: str = Field(...)
    user_id: str = Field(...)
    lead_id: Optional[str] = None

    status: str = Field("active", description="active | handed_off | closed")
    human_handoff_status: str = Field("none", description="none | requested | transferred")
    turn_count: int = Field(0)

    short_term_memory: List[Dict[str, Any]] = Field(default_factory=list)
    vector_memory_synced: bool = Field(True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_agent_sessions"
        indexes = [
            [("session_id", 1)],
            [("user_id", 1)],
            [("status", 1)],
        ]


class VoiceAgentTurnDocument(Document):
    """Stores individual multi-turn voice dialogue turns and tool execution logs."""

    turn_id: str = Field(..., description="Unique dialogue turn ID")
    session_id: str = Field(...)
    turn_index: int = Field(0)

    user_transcript: str = Field(...)
    agent_response_text: str = Field(...)
    agent_response_audio_url: Optional[str] = None

    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    execution_result: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(0.96)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "voice_agent_turns"
        indexes = [
            [("turn_id", 1)],
            [("session_id", 1)],
            [("turn_index", 1)],
        ]
