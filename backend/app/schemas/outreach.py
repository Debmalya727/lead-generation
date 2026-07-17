"""
Pydantic v2 schemas for Phase 7 AI Outreach & Sales Automation.
"""
from datetime import datetime
from typing import Dict, List, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr, Field

# ── Email Account Schemas ────────────────────────────────────────

class EmailAccountCreate(BaseModel):
    provider_type: str = Field("smtp", description="smtp | gmail | outlook")
    name: str = Field(..., description="Account name label")
    email_address: EmailStr = Field(..., description="Sending email address")
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = True
    daily_limit: int = 150
    warmup_enabled: bool = False
    is_default: bool = False


class EmailAccountResponse(BaseModel):
    id: PydanticObjectId
    owner_id: PydanticObjectId
    provider_type: str
    name: str
    email_address: str
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    daily_limit: int
    sending_count_today: int
    warmup_enabled: bool
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# ── Email Template Schemas ───────────────────────────────────────

class EmailTemplateCreate(BaseModel):
    name: str = Field(..., description="Template name")
    category: str = Field("cold_outreach", description="cold_outreach | follow_up | custom")
    subject: str = Field(..., description="Subject template string")
    body: str = Field(..., description="HTML/text body template string")


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class EmailTemplateResponse(BaseModel):
    id: PydanticObjectId
    owner_id: PydanticObjectId
    name: str
    category: str
    subject: str
    body: str
    variables_used: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# ── Campaign & Step Schemas ──────────────────────────────────────

class CampaignStepSchema(BaseModel):
    step_number: int = Field(1)
    delay_days: int = Field(0)
    step_type: str = Field("email", description="email | follow_up")
    subject: str = Field(...)
    body: str = Field(...)
    template_id: Optional[str] = None


class CampaignCreateRequest(BaseModel):
    name: str = Field(..., description="Campaign name")
    sending_account_id: Optional[str] = None
    daily_limit: int = Field(50)
    ab_testing_enabled: bool = False
    steps: List[CampaignStepSchema] = Field(..., min_items=1)
    lead_ids: List[str] = Field(default_factory=list)
    schedule_config: Dict[str, str] = Field(
        default_factory=lambda: {"time_zone": "UTC", "send_window_start": "09:00", "send_window_end": "17:00"}
    )


class CampaignStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="draft | active | paused | completed | cancelled")


class CampaignResponse(BaseModel):
    id: PydanticObjectId
    owner_id: PydanticObjectId
    name: str
    status: str
    sending_account_id: Optional[PydanticObjectId] = None
    daily_limit: int
    ab_testing_enabled: bool
    schedule_config: Dict[str, str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# ── AI Generation & Preview Schemas ─────────────────────────────

class AIEmailGenerateRequest(BaseModel):
    lead_id: str = Field(..., description="Lead ID to personalize for")
    generation_type: str = Field("cold_email", description="cold_email | followup | subject | icebreaker")
    value_proposition: Optional[str] = "accelerate sales growth and automate workflow"
    step_number: Optional[int] = 1


class AIResponse(BaseModel):
    subject: Optional[str] = None
    icebreaker: Optional[str] = None
    body: Optional[str] = None
    cta: Optional[str] = None
    subjects_list: List[str] = []


class PreviewEmailRequest(BaseModel):
    lead_id: str
    subject_template: str
    body_template: str
    custom_variables: Dict[str, str] = Field(default_factory=dict)


class PreviewEmailResponse(BaseModel):
    rendered_subject: str
    rendered_body: str
