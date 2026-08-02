"""
Platform event schemas for Section 11: Event Bus Architecture.

Includes PlatformEvent base schema and 18 platform lifecycle events.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PlatformEvent(BaseModel):
    """Base Event schema emitted across the platform."""

    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    event_type: str = Field(..., description="Unique event identifier e.g. 'WorkflowStarted'")
    topic: str = Field("system", description="Routing topic e.g. 'workflows', 'agents', 'leads'")
    
    source: str = Field("backend", description="Component emitting event e.g. 'WorkflowEngine'")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)


# --- 18 Specific Lifecycle Event Classes ---

class WorkflowStartedEvent(PlatformEvent):
    event_type: str = "WorkflowStarted"
    topic: str = "workflows"

class WorkflowCompletedEvent(PlatformEvent):
    event_type: str = "WorkflowCompleted"
    topic: str = "workflows"

class WorkflowFailedEvent(PlatformEvent):
    event_type: str = "WorkflowFailed"
    topic: str = "workflows"

class AgentStartedEvent(PlatformEvent):
    event_type: str = "AgentStarted"
    topic: str = "agents"

class AgentCompletedEvent(PlatformEvent):
    event_type: str = "AgentCompleted"
    topic: str = "agents"

class ToolExecutedEvent(PlatformEvent):
    event_type: str = "ToolExecuted"
    topic: str = "tools"

class ToolFailedEvent(PlatformEvent):
    event_type: str = "ToolFailed"
    topic: str = "tools"

class ConversationStartedEvent(PlatformEvent):
    event_type: str = "ConversationStarted"
    topic: str = "conversations"

class ConversationEndedEvent(PlatformEvent):
    event_type: str = "ConversationEnded"
    topic: str = "conversations"

class ConversationUpdatedEvent(PlatformEvent):
    event_type: str = "ConversationUpdated"
    topic: str = "conversations"

class ReportGeneratedEvent(PlatformEvent):
    event_type: str = "ReportGenerated"
    topic: str = "reports"

class LeadScoredEvent(PlatformEvent):
    event_type: str = "LeadScored"
    topic: str = "leads"

class LeadDiscoveredEvent(PlatformEvent):
    event_type: str = "LeadDiscovered"
    topic: str = "leads"

class OutreachGeneratedEvent(PlatformEvent):
    event_type: str = "OutreachGenerated"
    topic: str = "outreach"

class OutreachSentEvent(PlatformEvent):
    event_type: str = "OutreachSent"
    topic: str = "outreach"

class CheckpointCreatedEvent(PlatformEvent):
    event_type: str = "CheckpointCreated"
    topic: str = "checkpoints"

class PolicyViolationEvent(PlatformEvent):
    event_type: str = "PolicyViolation"
    topic: str = "policies"

class FeatureFlagChangedEvent(PlatformEvent):
    event_type: str = "FeatureFlagChanged"
    topic: str = "platform"

class SystemHealthChangedEvent(PlatformEvent):
    event_type: str = "SystemHealthChanged"
    topic: str = "platform"

class LeadNormalizedEvent(PlatformEvent):
    event_type: str = "LeadNormalized"
    topic: str = "leads"

class LeadDuplicateDetectedEvent(PlatformEvent):
    event_type: str = "LeadDuplicateDetected"
    topic: str = "leads"

class LeadEnrichedEvent(PlatformEvent):
    event_type: str = "LeadEnriched"
    topic: str = "leads"

class LeadScoreUpdatedEvent(PlatformEvent):
    event_type: str = "LeadScoreUpdated"
    topic: str = "leads"

class LeadCRMCreatedEvent(PlatformEvent):
    event_type: str = "LeadCRMCreated"
    topic: str = "leads"

class LeadDiscoveryFailedEvent(PlatformEvent):
    event_type: str = "LeadDiscoveryFailed"
    topic: str = "leads"

class ProviderHealthChangedEvent(PlatformEvent):
    event_type: str = "ProviderHealthChanged"
    topic: str = "discovery"

