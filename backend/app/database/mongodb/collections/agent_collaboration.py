"""
Beanie MongoDB Document collections for Phase 11 — Milestone 3: Multi-Agent Collaboration Engine.

Collections:
- AgentMessageDocument (Agent-to-agent structured message logs)
- AgentArtifactDocument (Shared versioned artifact repository)
- AgentConsensusDocument (Consensus decisions and conflict resolution records)
- AgentCollaborationDocument (Job-level collaboration state, metrics, & active conversations)
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class AgentMessageDocument(Document):
    """Document storing structured agent-to-agent message logs."""

    message_id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Conversation thread identifier")
    job_id: str = Field(..., description="Associated AgentJob ID")
    task_id: Optional[str] = Field(None, description="Optional task node ID")
    
    from_agent: str = Field(..., description="Sender agent ID")
    to_agent: str = Field(..., description="Recipient agent ID or 'broadcast'/'group'")
    message_type: str = Field("point_to_point", description="point_to_point | broadcast | delegation | proposal | conflict | consensus | status")
    
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message data payload")
    confidence: int = Field(100, ge=0, le=100)
    status: str = Field("delivered", description="sent | delivered | processed | failed")
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_messages"
        indexes = [
            [("job_id", 1), ("conversation_id", 1)],
            [("job_id", 1), ("timestamp", -1)],
            [("from_agent", 1), ("to_agent", 1)],
            [("message_id", 1)],
        ]


class AgentArtifactDocument(Document):
    """Document storing versioned shared artifacts created or reused by agents."""

    artifact_id: str = Field(..., description="Unique artifact identifier")
    job_id: str = Field(..., description="Associated AgentJob ID")
    task_id: Optional[str] = Field(None, description="Creating task node ID")
    owner_agent: str = Field(..., description="Agent ID that produced the artifact")
    
    artifact_type: str = Field(..., description="research | memory | strategy | outreach | review | executive | custom")
    title: str = Field("Agent Artifact", description="Human-readable title")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content: Dict[str, Any] = Field(default_factory=dict, description="Structured artifact content body")
    
    confidence: int = Field(85, ge=0, le=100)
    version: int = Field(1, ge=1)
    parent_version_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_artifacts"
        indexes = [
            [("job_id", 1), ("artifact_type", 1)],
            [("job_id", 1), ("owner_agent", 1)],
            [("artifact_id", 1)],
            [("created_at", -1)],
        ]


class AgentConsensusDocument(Document):
    """Document storing consensus decisions and conflict resolutions."""

    consensus_id: str = Field(..., description="Unique consensus resolution ID")
    job_id: str = Field(..., description="Associated AgentJob ID")
    task_id: Optional[str] = Field(None, description="Target task node ID")
    
    topic: str = Field(..., description="Subject of consensus or conflict (e.g. 'company_funding')")
    proposals: List[Dict[str, Any]] = Field(default_factory=list, description="Agent proposals with confidence scores")
    
    strategy_used: str = Field("highest_confidence", description="highest_confidence | weighted_confidence | majority_vote | llm_arbitration | human_approval")
    resolved_output: Dict[str, Any] = Field(default_factory=dict, description="Winning or synthesized consensus payload")
    winning_agent: Optional[str] = Field(None, description="Winning agent ID if applicable")
    
    confidence: int = Field(85, ge=0, le=100)
    is_conflict: bool = Field(False, description="Whether this consensus resolved an explicit contradiction")
    conflict_details: Optional[Dict[str, Any]] = None
    
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_consensus"
        indexes = [
            [("job_id", 1), ("topic", 1)],
            [("job_id", 1), ("resolved_at", -1)],
            [("consensus_id", 1)],
        ]


class AgentCollaborationDocument(Document):
    """Document storing overall job collaboration state, metrics, and active conversations."""

    collaboration_id: str = Field(..., description="Unique collaboration session ID")
    job_id: str = Field(..., description="Associated AgentJob ID")
    owner_id: PydanticObjectId
    
    active_conversations: List[str] = Field(default_factory=list)
    delegation_count: int = Field(0, ge=0)
    conflict_count: int = Field(0, ge=0)
    consensus_count: int = Field(0, ge=0)
    message_count: int = Field(0, ge=0)
    artifact_count: int = Field(0, ge=0)
    
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_collaboration"
        indexes = [
            [("job_id", 1)],
            [("owner_id", 1), ("created_at", -1)],
        ]
