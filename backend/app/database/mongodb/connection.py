import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

logger = logging.getLogger("backend.database")

from app.database.mongodb.collections.user import User
from app.database.mongodb.collections.lead import Lead
from app.database.mongodb.collections.job import ScrapeJob
from app.database.mongodb.collections.intelligence import CompanyIntelligence
from app.database.mongodb.collections.lead_score import LeadScore
from app.database.mongodb.collections.outreach import (
    EmailAccount,
    EmailTemplate,
    Campaign,
    CampaignStep,
    CampaignRecipient,
    EmailEvent,
    EmailAnalytics,
)
from app.database.mongodb.collections.sales_intelligence import SalesIntelligenceReport
from app.database.mongodb.collections.research import ResearchReport
from app.database.mongodb.collections.vector_index import VectorChunk
from app.database.mongodb.collections.agent_runtime import AgentJob, AgentEvent
from app.database.mongodb.collections.executive_report import ExecutiveReport
from app.database.mongodb.collections.agent_collaboration import (
    AgentMessageDocument,
    AgentArtifactDocument,
    AgentConsensusDocument,
    AgentCollaborationDocument,
)
from app.database.mongodb.collections.agent_workflow import (
    WorkflowTemplateDocument,
    WorkflowExecutionDocument,
    WorkflowStepDocument,
    WorkflowCheckpointDocument,
    ToolExecutionDocument,
    WorkflowPolicyDocument,
)
from app.database.mongodb.collections.agent_conversation import (
    ConversationSessionDocument,
    ConversationMessageDocument,
    ConversationMemoryDocument,
    ConversationFeedbackDocument,
)
from app.database.mongodb.collections.platform import (
    AuditLogDocument,
    FeatureFlagDocument,
    SystemMetricDocument,
    RequestTraceDocument,
)
from app.database.mongodb.collections.platform_extended import (
    ScheduledJobDocument,
    JobHistoryDocument,
    InstalledPluginDocument,
    PluginSettingsDocument,
    NotificationDocument,
)
from app.database.mongodb.collections.ai_gateway import (
    AIRequestDocument,
    AIResponseDocument,
    ModelRegistryDocument,
    ProviderRegistryDocument,
    PromptTemplateDocument,
    PromptVersionDocument,
    TokenUsageDocument,
    CostUsageDocument,
    EmbeddingCacheDocument,
)
from app.database.mongodb.collections.ai_gateway_extended import (
    AIPolicyDocument,
    CapabilityRegistryDocument,
    AISessionDocument,
    PromptRegistryDocument,
    PromptApprovalDocument,
    ModelBenchmarkDocument,
    BenchmarkHistoryDocument,
    GuardrailLogDocument,
    EvaluationRunDocument,
    EvaluationScoreDocument,
    AIMemoryDocument,
    WorkflowArtifactDocument,
)
from app.database.mongodb.collections.ai_orchestrator import (
    AIWorkflowDocument,
    AIWorkflowRunDocument,
    AIWorkflowNodeDocument,
    AIWorkflowEdgeDocument,
    AIExecutionPlanDocument,
    AIPipelineTemplateDocument,
    AIQueueDocument,
    AIDeadLetterQueueDocument,
    ProviderHealthDocument,
    ResourceMetricsDocument,
)
from app.database.mongodb.collections.voice_infrastructure import (
    VoiceSessionDocument,
    VoiceStreamDocument,
    VoiceBufferDocument,
    VoiceMetricsDocument,
    VoiceEventDocument,
    VoiceDeviceDocument,
)
from app.database.mongodb.collections.speech_gateway import (
    SpeechRequestDocument,
    SpeechResponseDocument,
    SpeechSessionDocument,
    SpeechProviderDocument,
    SpeechModelDocument,
    SpeechCostDocument,
    SpeechBenchmarkDocument,
)
from app.database.mongodb.collections.tts_gateway import (
    TTSRequestDocument,
    TTSAudioOutputDocument,
    TTSVoiceProfileDocument,
    TTSProviderDocument,
    TTSModelDocument,
    TTSCostDocument,
    TTSCacheDocument,
    TTSBenchmarkDocument,
)
from app.database.mongodb.collections.bidirectional_voice import (
    BidirectionalSessionDocument,
    BidirectionalTurnDocument,
    BidirectionalMetricsDocument,
)
from app.database.mongodb.collections.voice_commands import (
    VoiceCommandLogDocument,
    VoiceConfirmationDocument,
)
from app.database.mongodb.collections.voice_meetings import (
    VoiceMeetingDocument,
    VoiceMeetingSegmentDocument,
    VoiceMeetingActionItemDocument,
    VoiceMeetingSummaryDocument,
)
from app.database.mongodb.collections.voice_agents import (
    VoiceAgentPersonaDocument,
    VoiceAgentSessionDocument,
    VoiceAgentTurnDocument,
)
from app.database.mongodb.collections.telephony import (
    TelephonyCallDocument,
    TelephonyRecordingDocument,
    TelephonyQueueEventDocument,
    TelephonyCallSummaryDocument,
)
from app.database.mongodb.collections.voice_analytics import (
    VoiceAnalyticsEventDocument,
    VoiceAnalyticsSessionDocument,
    VoiceAnalyticsDailyDocument,
    VoiceAnalyticsAlertDocument,
    VoiceAnalyticsExportDocument,
    VoiceProviderPerformanceDocument,
)
from app.database.mongodb.collections.knowledge import (
    UniversalKnowledgeObjectDoc,
    KnowledgeDocument,
    KnowledgeImportJob,
    KnowledgeSource,
    KnowledgeValidationRecord,
    KnowledgeEventRecord,
    KnowledgeChunk,
    CompiledKnowledgeObjectDoc,
    KnowledgeEntityRecord,
    KnowledgeOntologyRecord,
    KnowledgeRelationshipRecord,
    KnowledgeGraphNodeDoc,
    KnowledgeGraphEdgeDoc,
    KnowledgeGraphSnapshotDoc,
    EnterpriseMemoryRecord,
    MemoryGovernanceRecord,
    EmbeddingConfigRecord,
    EmbeddingCacheRecord,
    RetrievalStrategyRecord,
    CitationRecord,
    RAGQueryRecord,
    AnswerVerificationRecord,
    KnowledgeLifecycleRecord,
    KnowledgeAnalyticsEventDoc,
    KnowledgeAnalyticsDailyDoc,
    KnowledgeAlertRecord,
    KnowledgeExportRecord,
)

# List of documents mapping to Beanie ODM.
DOCUMENT_MODELS = [
    AIRequestDocument,
    AIResponseDocument,
    ModelRegistryDocument,
    ProviderRegistryDocument,
    PromptTemplateDocument,
    PromptVersionDocument,
    TokenUsageDocument,
    CostUsageDocument,
    EmbeddingCacheDocument,
    User,
    Lead,
    ScrapeJob,
    CompanyIntelligence,
    LeadScore,
    EmailAccount,
    EmailTemplate,
    Campaign,
    CampaignStep,
    CampaignRecipient,
    EmailEvent,
    EmailAnalytics,
    SalesIntelligenceReport,
    ResearchReport,
    VectorChunk,
    AgentJob,
    AgentEvent,
    ExecutiveReport,
    AgentMessageDocument,
    AgentArtifactDocument,
    AgentConsensusDocument,
    AgentCollaborationDocument,
    WorkflowTemplateDocument,
    WorkflowExecutionDocument,
    WorkflowStepDocument,
    WorkflowCheckpointDocument,
    ToolExecutionDocument,
    WorkflowPolicyDocument,
    ConversationSessionDocument,
    ConversationMessageDocument,
    ConversationMemoryDocument,
    ConversationFeedbackDocument,
    AuditLogDocument,
    FeatureFlagDocument,
    SystemMetricDocument,
    RequestTraceDocument,
    ScheduledJobDocument,
    JobHistoryDocument,
    InstalledPluginDocument,
    PluginSettingsDocument,
    NotificationDocument,
    # Phase 12.7B Extended AI Gateway
    AIPolicyDocument,
    CapabilityRegistryDocument,
    AISessionDocument,
    PromptRegistryDocument,
    PromptApprovalDocument,
    ModelBenchmarkDocument,
    BenchmarkHistoryDocument,
    GuardrailLogDocument,
    EvaluationRunDocument,
    EvaluationScoreDocument,
    AIMemoryDocument,
    WorkflowArtifactDocument,
    # Phase 12.7C Enterprise AI Orchestration Platform
    AIWorkflowDocument,
    AIWorkflowRunDocument,
    AIWorkflowNodeDocument,
    AIWorkflowEdgeDocument,
    AIExecutionPlanDocument,
    AIPipelineTemplateDocument,
    AIQueueDocument,
    AIDeadLetterQueueDocument,
    ProviderHealthDocument,
    ResourceMetricsDocument,
    # Phase 13.1 Enterprise Voice Infrastructure
    VoiceSessionDocument,
    VoiceStreamDocument,
    VoiceBufferDocument,
    VoiceMetricsDocument,
    VoiceEventDocument,
    VoiceDeviceDocument,
    # Phase 13.2 Speech Recognition Gateway
    SpeechRequestDocument,
    SpeechResponseDocument,
    SpeechSessionDocument,
    SpeechProviderDocument,
    SpeechModelDocument,
    SpeechCostDocument,
    SpeechBenchmarkDocument,
    # Phase 13.3 Text-to-Speech Gateway
    TTSRequestDocument,
    TTSAudioOutputDocument,
    TTSVoiceProfileDocument,
    TTSProviderDocument,
    TTSModelDocument,
    TTSCostDocument,
    TTSCacheDocument,
    TTSBenchmarkDocument,
    # Phase 13.4 Real-Time Bidirectional Voice Streaming
    BidirectionalSessionDocument,
    BidirectionalTurnDocument,
    BidirectionalMetricsDocument,
    # Phase 13.6 Voice Command Planner Integration
    VoiceCommandLogDocument,
    VoiceConfirmationDocument,
    # Phase 13.7 Enterprise Voice Meeting Assistant
    VoiceMeetingDocument,
    VoiceMeetingSegmentDocument,
    VoiceMeetingActionItemDocument,
    VoiceMeetingSummaryDocument,
    # Phase 13.8 Conversational Voice Agents
    VoiceAgentPersonaDocument,
    VoiceAgentSessionDocument,
    VoiceAgentTurnDocument,
    # Phase 13.9 Enterprise Telephony Integration
    TelephonyCallDocument,
    TelephonyRecordingDocument,
    TelephonyQueueEventDocument,
    TelephonyCallSummaryDocument,
    # Phase 13.10 Voice Analytics
    VoiceAnalyticsEventDocument,
    VoiceAnalyticsSessionDocument,
    VoiceAnalyticsDailyDocument,
    VoiceAnalyticsAlertDocument,
    VoiceAnalyticsExportDocument,
    VoiceProviderPerformanceDocument,
    # Phase 14 Enterprise Knowledge Fabric (26 Models)
    UniversalKnowledgeObjectDoc,
    KnowledgeDocument,
    KnowledgeImportJob,
    KnowledgeSource,
    KnowledgeValidationRecord,
    KnowledgeEventRecord,
    KnowledgeChunk,
    CompiledKnowledgeObjectDoc,
    KnowledgeEntityRecord,
    KnowledgeOntologyRecord,
    KnowledgeRelationshipRecord,
    KnowledgeGraphNodeDoc,
    KnowledgeGraphEdgeDoc,
    KnowledgeGraphSnapshotDoc,
    EnterpriseMemoryRecord,
    MemoryGovernanceRecord,
    EmbeddingConfigRecord,
    EmbeddingCacheRecord,
    RetrievalStrategyRecord,
    CitationRecord,
    RAGQueryRecord,
    AnswerVerificationRecord,
    KnowledgeLifecycleRecord,
    KnowledgeAnalyticsEventDoc,
    KnowledgeAnalyticsDailyDoc,
    KnowledgeAlertRecord,
    KnowledgeExportRecord,
]

from typing import Optional

class DatabaseManager:
    client: AsyncIOMotorClient = None
    db_name: Optional[str] = None

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the MongoDB connection and Beanie ODM."""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://leadforge:leadforge_password@localhost:27017/leadforge_db?authSource=admin")
        cls.db_name = os.getenv("MONGODB_DB_NAME", "leadforge_db")
        
        logger.info(f"Connecting to MongoDB at {mongodb_url.split('@')[-1]}...")
        
        try:
            cls.client = AsyncIOMotorClient(mongodb_url)
            # Initialize Beanie with document models
            await init_beanie(
                database=cls.client[cls.db_name],
                document_models=DOCUMENT_MODELS
            )
            logger.info("Successfully connected to MongoDB and initialized Beanie ODM.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise e

    @classmethod
    async def close(cls) -> None:
        """Close the MongoDB connection pool."""
        if cls.client is not None:
            cls.client.close()
            logger.info("MongoDB connection closed.")
        else:
            logger.warning("MongoDB client was not initialized when close requested.")

async def get_db_client() -> AsyncIOMotorClient:
    """Dependency injector for database client."""
    return DatabaseManager.client
