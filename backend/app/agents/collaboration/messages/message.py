"""
AgentMessage Data Model for Multi-Agent Collaboration Engine.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """Structured message object passed between agents."""

    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    conversation_id: str = Field(default_factory=lambda: f"conv_{uuid.uuid4().hex[:12]}")
    job_id: str = Field(..., description="Associated AgentJob ID")
    task_id: Optional[str] = Field(None, description="Associated task node ID")
    
    from_agent: str = Field(..., description="Sender agent ID")
    to_agent: str = Field(..., description="Recipient agent ID or 'broadcast'/'group'")
    message_type: str = Field("point_to_point", description="point_to_point | broadcast | delegation | proposal | conflict | consensus | status")
    
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured message body")
    confidence: int = Field(100, ge=0, le=100)
    status: str = Field("sent", description="sent | delivered | processed | failed")
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
