from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.mongodb.collections.user import User
from app.database.mongodb.repositories.user_repository import UserRepository
from app.modules.auth.auth_module import AuthModule
from app.modules.users.users_module import UsersModule
from app.security.jwt import decode_token

# HTTPBearer extracts the raw JWT from the Authorization: Bearer <token> header.
# This renders a clean single-field "Bearer token" input in Swagger UI instead
# of the full OAuth2 Password Flow form (which incorrectly shows client_id /
# client_secret fields that this API does not implement).
reusable_oauth2 = HTTPBearer()


def get_user_repository() -> UserRepository:
    """Dependency provider for UserRepository layer."""
    return UserRepository()


def get_users_module(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UsersModule:
    """Dependency provider for UsersModule orchestration layer."""
    return UsersModule(user_repo)


def get_auth_module(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthModule:
    """Dependency provider for AuthModule orchestration layer."""
    return AuthModule(user_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """Dependency validator verifying signed access token and resolving active User."""
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing user ID reference",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with this session token does not exist.",
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your user account is deactivated.",
        )
        
    return user


from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.modules.leadfinder.lead_finder_module import LeadFinderModule


def get_lead_repository() -> LeadRepository:
    """Dependency provider for LeadRepository layer."""
    return LeadRepository()


def get_lead_finder_module(
    lead_repo: LeadRepository = Depends(get_lead_repository)
) -> LeadFinderModule:
    """Dependency provider for LeadFinderModule orchestration layer."""
    return LeadFinderModule(lead_repo)


from app.database.mongodb.repositories.job_repository import JobRepository
from app.modules.discovery.discovery_module import DiscoveryModule


def get_job_repository() -> JobRepository:
    """Dependency provider for JobRepository layer."""
    return JobRepository()


def get_discovery_module(
    job_repo: JobRepository = Depends(get_job_repository),
    lead_repo: LeadRepository = Depends(get_lead_repository)
) -> DiscoveryModule:
    """Dependency provider for DiscoveryModule orchestration layer."""
    return DiscoveryModule(job_repo, lead_repo)


from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.modules.intelligence.intelligence_module import IntelligenceModule


def get_intelligence_repository() -> IntelligenceRepository:
    """Dependency provider for IntelligenceRepository layer."""
    return IntelligenceRepository()


def get_intelligence_module(
    intel_repo: IntelligenceRepository = Depends(get_intelligence_repository),
    lead_repo: LeadRepository = Depends(get_lead_repository),
) -> IntelligenceModule:
    """Dependency provider for IntelligenceModule orchestration layer."""
    return IntelligenceModule(intel_repo, lead_repo)


from app.database.mongodb.repositories.scoring_repository import ScoringRepository
from app.modules.scoring.scoring_module import ScoringModule


def get_scoring_repository() -> ScoringRepository:
    """Dependency provider for ScoringRepository layer."""
    return ScoringRepository()


def get_scoring_module(
    scoring_repo: ScoringRepository = Depends(get_scoring_repository),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    intel_repo: IntelligenceRepository = Depends(get_intelligence_repository),
) -> ScoringModule:
    """Dependency provider for ScoringModule orchestration layer."""
    return ScoringModule(scoring_repo, lead_repo, intel_repo)


from app.database.mongodb.repositories.outreach_repository import (
    CampaignRepository,
    CampaignStepRepository,
    CampaignRecipientRepository,
    EmailTemplateRepository,
    EmailAccountRepository,
    EmailEventRepository,
    EmailAnalyticsRepository,
)
from app.modules.outreach.outreach_module import (
    CampaignModule,
    TemplateModule,
    EmailAccountModule,
    SendingModule,
    TrackingModule,
    AnalyticsModule,
)


def get_account_repository() -> EmailAccountRepository:
    return EmailAccountRepository()

def get_template_repository() -> EmailTemplateRepository:
    return EmailTemplateRepository()

def get_campaign_repository() -> CampaignRepository:
    return CampaignRepository()

def get_step_repository() -> CampaignStepRepository:
    return CampaignStepRepository()

def get_recipient_repository() -> CampaignRecipientRepository:
    return CampaignRecipientRepository()

def get_event_repository() -> EmailEventRepository:
    return EmailEventRepository()

def get_analytics_repository() -> EmailAnalyticsRepository:
    return EmailAnalyticsRepository()

def get_account_module(
    repo: EmailAccountRepository = Depends(get_account_repository),
) -> EmailAccountModule:
    return EmailAccountModule(repo)

def get_template_module(
    repo: EmailTemplateRepository = Depends(get_template_repository),
) -> TemplateModule:
    return TemplateModule(repo)

def get_campaign_module(
    camp_repo: CampaignRepository = Depends(get_campaign_repository),
    step_repo: CampaignStepRepository = Depends(get_step_repository),
    recip_repo: CampaignRecipientRepository = Depends(get_recipient_repository),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    analytics_repo: EmailAnalyticsRepository = Depends(get_analytics_repository),
) -> CampaignModule:
    return CampaignModule(camp_repo, step_repo, recip_repo, lead_repo, analytics_repo)

def get_tracking_module(
    recip_repo: CampaignRecipientRepository = Depends(get_recipient_repository),
    event_repo: EmailEventRepository = Depends(get_event_repository),
    analytics_repo: EmailAnalyticsRepository = Depends(get_analytics_repository),
) -> TrackingModule:
    return TrackingModule(recip_repo, event_repo, analytics_repo)

def get_analytics_module(
    analytics_repo: EmailAnalyticsRepository = Depends(get_analytics_repository),
    event_repo: EmailEventRepository = Depends(get_event_repository),
) -> AnalyticsModule:
    return AnalyticsModule(analytics_repo, event_repo)


from app.database.mongodb.repositories.sales_intelligence_repository import SalesIntelligenceRepository
from app.modules.sales_intelligence.sales_intelligence_module import SalesIntelligenceModule


def get_sales_intelligence_repository() -> SalesIntelligenceRepository:
    return SalesIntelligenceRepository()


def get_sales_intelligence_module(
    sales_intel_repo: SalesIntelligenceRepository = Depends(get_sales_intelligence_repository),
    lead_repo: LeadRepository = Depends(get_lead_repository),
) -> SalesIntelligenceModule:
    return SalesIntelligenceModule(sales_intel_repo, lead_repo)


from app.database.mongodb.repositories.research_repository import ResearchRepository
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.modules.research.research_module import ResearchModule


def get_research_repository() -> ResearchRepository:
    return ResearchRepository()


def get_research_module(
    research_repo: ResearchRepository = Depends(get_research_repository),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    company_intel_repo: IntelligenceRepository = Depends(get_intelligence_repository),
) -> ResearchModule:
    return ResearchModule(research_repo, lead_repo, company_intel_repo)


from app.vector.services.vector_service import VectorService


def get_vector_service(
    lead_repo: LeadRepository = Depends(get_lead_repository),
    intel_repo: IntelligenceRepository = Depends(get_intelligence_repository),
    scoring_repo: ScoringRepository = Depends(get_scoring_repository),
    sales_intel_repo: SalesIntelligenceRepository = Depends(get_sales_intelligence_repository),
    research_repo: ResearchRepository = Depends(get_research_repository),
    campaign_repo: CampaignRepository = Depends(get_campaign_repository),
    template_repo: EmailTemplateRepository = Depends(get_template_repository),
) -> VectorService:
    return VectorService(
        lead_repo=lead_repo,
        intel_repo=intel_repo,
        scoring_repo=scoring_repo,
        sales_intel_repo=sales_intel_repo,
        research_repo=research_repo,
        campaign_repo=campaign_repo,
        template_repo=template_repo,
    )


from app.database.mongodb.repositories.agent_repository import AgentRepository
from app.agents.services.agent_service import AgentService
from app.agents.services.collaboration_service import CollaborationService
from app.agents.services.workflow_service import WorkflowService
from app.conversation.services.conversation_service import ConversationService
from app.platform.services.platform_service import PlatformService


def get_agent_repository() -> AgentRepository:
    return AgentRepository()


def get_agent_service(
    agent_repo: AgentRepository = Depends(get_agent_repository),
) -> AgentService:
    return AgentService(agent_repo=agent_repo)


def get_collaboration_service() -> CollaborationService:
    return CollaborationService()


def get_workflow_service() -> WorkflowService:
    return WorkflowService()


def get_conversation_service() -> ConversationService:
    return ConversationService()


def get_platform_service() -> PlatformService:
    return PlatformService()





