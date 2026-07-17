"""
Outreach Module REST API Router.

Endpoints:
- Campaign CRUD & lifecycle (/campaigns)
- Email Templates (/templates)
- Email Accounts (/accounts)
- AI Generation (/ai/generate)
- Preview & Analytics
"""
from typing import List
from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import (
    get_current_user,
    get_campaign_module,
    get_template_module,
    get_account_module,
    get_analytics_module,
    get_lead_repository,
    get_intelligence_repository,
    get_scoring_repository,
)
from app.database.mongodb.collections.user import User
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.database.mongodb.repositories.scoring_repository import ScoringRepository
from app.modules.outreach.outreach_module import (
    CampaignModule,
    TemplateModule,
    EmailAccountModule,
    AnalyticsModule,
)
from app.modules.outreach.ai_generator import AIEmailGenerator
from app.modules.outreach.variable_engine import VariableEngine
from app.schemas.outreach import (
    EmailAccountCreate,
    EmailAccountResponse,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
    CampaignCreateRequest,
    CampaignStatusUpdateRequest,
    CampaignResponse,
    AIEmailGenerateRequest,
    AIResponse,
    PreviewEmailRequest,
    PreviewEmailResponse,
)

router = APIRouter()


# ── Email Accounts ───────────────────────────────────────────────

@router.get("/accounts", response_model=List[EmailAccountResponse])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    account_module: EmailAccountModule = Depends(get_account_module),
):
    """List all email sending accounts owned by current user."""
    return await account_module.list_accounts(str(current_user.id))


@router.post("/accounts", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: EmailAccountCreate,
    current_user: User = Depends(get_current_user),
    account_module: EmailAccountModule = Depends(get_account_module),
):
    """Add a new SMTP, Gmail, or Outlook sending account."""
    return await account_module.create_account(payload.model_dump(), str(current_user.id))


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    account_module: EmailAccountModule = Depends(get_account_module),
):
    """Delete an email account configuration."""
    await account_module.delete_account(account_id, str(current_user.id))
    return {"status": "success", "message": "Account deleted"}


@router.post("/accounts/{account_id}/test")
async def test_account_connection(
    account_id: str,
    recipient_email: str = Query(..., description="Email address to receive test email"),
    current_user: User = Depends(get_current_user),
    account_module: EmailAccountModule = Depends(get_account_module),
):
    """Send a test email using the configured account settings."""
    return await account_module.test_account(account_id, str(current_user.id), recipient_email)


# ── Email Templates ──────────────────────────────────────────────

@router.get("/templates", response_model=List[EmailTemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    template_module: TemplateModule = Depends(get_template_module),
):
    """List reusable email templates."""
    return await template_module.list_templates(str(current_user.id))


@router.post("/templates", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: EmailTemplateCreate,
    current_user: User = Depends(get_current_user),
    template_module: TemplateModule = Depends(get_template_module),
):
    """Create a new email template."""
    return await template_module.create_template(payload.model_dump(), str(current_user.id))


@router.put("/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: str,
    payload: EmailTemplateUpdate,
    current_user: User = Depends(get_current_user),
    template_module: TemplateModule = Depends(get_template_module),
):
    """Update an existing email template."""
    return await template_module.update_template(
        template_id, payload.model_dump(exclude_unset=True), str(current_user.id)
    )


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    template_module: TemplateModule = Depends(get_template_module),
):
    """Delete an email template."""
    await template_module.delete_template(template_id, str(current_user.id))
    return {"status": "success", "message": "Template deleted"}


# ── Campaigns ────────────────────────────────────────────────────

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    campaign_module: CampaignModule = Depends(get_campaign_module),
):
    """List all email campaigns."""
    return await campaign_module.list_campaigns(str(current_user.id))


@router.get("/campaigns/{campaign_id}")
async def get_campaign_detail(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    campaign_module: CampaignModule = Depends(get_campaign_module),
):
    """Get full campaign details including steps, recipient counts, and analytics."""
    return await campaign_module.get_campaign_detail(campaign_id, str(current_user.id))


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreateRequest,
    current_user: User = Depends(get_current_user),
    campaign_module: CampaignModule = Depends(get_campaign_module),
):
    """Create a new multi-step email campaign and enroll leads."""
    camp_data = {
        "name": payload.name,
        "sending_account_id": payload.sending_account_id,
        "daily_limit": payload.daily_limit,
        "ab_testing_enabled": payload.ab_testing_enabled,
        "schedule_config": payload.schedule_config,
    }
    steps_data = [step.model_dump() for step in payload.steps]
    return await campaign_module.create_campaign(
        data=camp_data,
        steps_data=steps_data,
        lead_ids=payload.lead_ids,
        owner_id=str(current_user.id),
    )


@router.put("/campaigns/{campaign_id}/status", response_model=CampaignResponse)
async def update_campaign_status(
    campaign_id: str,
    payload: CampaignStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    campaign_module: CampaignModule = Depends(get_campaign_module),
):
    """Start, pause, resume, or cancel a campaign."""
    return await campaign_module.update_status(campaign_id, payload.status, str(current_user.id))


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    campaign_module: CampaignModule = Depends(get_campaign_module),
):
    """Delete a campaign and its associated steps."""
    await campaign_module.delete_campaign(campaign_id, str(current_user.id))
    return {"status": "success", "message": "Campaign deleted"}


# ── AI Generation & Preview ──────────────────────────────────────

@router.post("/ai/generate", response_model=AIResponse)
async def generate_ai_email_copy(
    payload: AIEmailGenerateRequest,
    current_user: User = Depends(get_current_user),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    intel_repo: IntelligenceRepository = Depends(get_intelligence_repository),
    score_repo: ScoringRepository = Depends(get_scoring_repository),
):
    """Generate AI cold email, follow-up, subjects, or icebreaker using lead intelligence context."""
    lead = await lead_repo.get_by_id(payload.lead_id, str(current_user.id))
    if not lead:
        return AIResponse(subject="Default Cold Email", body="Hi {{first_name}}, let's connect.")

    intel = await intel_repo.get_by_lead_id(payload.lead_id, str(current_user.id))
    score_doc = await score_repo.get_by_lead_id(payload.lead_id, str(current_user.id))

    company_name = lead.name
    website = getattr(lead, "website", "") or ""

    industry = ""
    pain_points = []
    buying_signals = []
    tech_stack = []

    if intel and hasattr(intel, "intelligence") and intel.intelligence:
        industry = getattr(intel.intelligence, "industry", "") or ""
        pain_points = getattr(intel.intelligence, "pain_points", []) or []
        buying_signals = getattr(intel.intelligence, "buying_signals", []) or []

    if intel and hasattr(intel, "tech_stack"):
        tech_stack = [t.name for t in (getattr(intel, "tech_stack", []) or [])]

    score_val = getattr(score_doc, "score", 80) if score_doc else 80

    generator = AIEmailGenerator()

    if payload.generation_type == "subject":
        subjects = await generator.generate_subject_lines(company_name, industry)
        return AIResponse(subjects_list=subjects, subject=subjects[0] if subjects else f"Quick question for {company_name}")

    elif payload.generation_type == "icebreaker":
        icebreaker = await generator.generate_icebreaker(company_name, buying_signals, tech_stack)
        return AIResponse(icebreaker=icebreaker)

    elif payload.generation_type == "followup":
        res = await generator.generate_followup_email(
            company_name=company_name,
            step_number=payload.step_number or 2,
        )
        return AIResponse(subject=res.get("subject"), body=res.get("body"))

    else:
        # Default cold email
        res = await generator.generate_cold_email(
            company_name=company_name,
            website=website,
            industry=industry,
            pain_points=pain_points,
            buying_signals=buying_signals,
            tech_stack=tech_stack,
            lead_score=score_val,
            value_proposition=payload.value_proposition or "accelerate sales growth",
        )
        return AIResponse(
            subject=res.get("subject"),
            icebreaker=res.get("icebreaker"),
            body=res.get("body"),
            cta=res.get("cta"),
        )


@router.post("/preview", response_model=PreviewEmailResponse)
async def preview_email_variables(
    payload: PreviewEmailRequest,
    current_user: User = Depends(get_current_user),
    lead_repo: LeadRepository = Depends(get_lead_repository),
    intel_repo: IntelligenceRepository = Depends(get_intelligence_repository),
    score_repo: ScoringRepository = Depends(get_scoring_repository),
):
    """Render preview of email templates with substituted lead variables."""
    lead = await lead_repo.get_by_id(payload.lead_id, str(current_user.id))
    intel = await intel_repo.get_by_lead_id(payload.lead_id, str(current_user.id))
    score_doc = await score_repo.get_by_lead_id(payload.lead_id, str(current_user.id))

    rendered_subject = VariableEngine.render(payload.subject_template, payload.custom_variables, lead, intel, score_doc)
    rendered_body = VariableEngine.render(payload.body_template, payload.custom_variables, lead, intel, score_doc)

    return PreviewEmailResponse(rendered_subject=rendered_subject, rendered_body=rendered_body)


# ── Analytics ────────────────────────────────────────────────────

@router.get("/analytics/{campaign_id}")
async def get_campaign_analytics(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    analytics_module: AnalyticsModule = Depends(get_analytics_module),
):
    """Fetch campaign open, click, and reply rates."""
    return await analytics_module.get_analytics(campaign_id, str(current_user.id))
