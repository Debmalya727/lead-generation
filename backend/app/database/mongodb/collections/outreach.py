"""
Beanie ODM Document models for Phase 7 AI Outreach & Sales Automation.

Collections:
- EmailAccount
- EmailTemplate
- Campaign
- CampaignStep
- CampaignRecipient
- EmailEvent
- EmailAnalytics
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING, DESCENDING


class EmailAccount(Document):
    """Configuration for an email sending account (SMTP, Gmail OAuth, Outlook)."""
    owner_id: PydanticObjectId = Field(..., description="User ID who owns this account")
    provider_type: str = Field(..., description="smtp | gmail | outlook")
    name: str = Field(..., description="Display label, e.g. 'Primary Sales SMTP'")
    email_address: str = Field(..., description="From email address")

    # SMTP specific fields
    smtp_host: Optional[str] = Field(None, description="SMTP server hostname")
    smtp_port: Optional[int] = Field(587, description="SMTP port e.g. 587 or 465")
    smtp_username: Optional[str] = Field(None, description="SMTP login username")
    smtp_password: Optional[str] = Field(None, description="SMTP login password or app password")
    use_tls: bool = Field(True, description="Use TLS/STARTTLS")

    # Provider OAuth / API token placeholders
    api_key: Optional[str] = Field(None, description="API key if provider uses API")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")

    # Sending controls
    daily_limit: int = Field(150, description="Max emails allowed per 24h")
    sending_count_today: int = Field(0, description="Count of emails sent today")
    last_sent_date: Optional[str] = Field(None, description="YYYY-MM-DD string tracking reset")
    warmup_enabled: bool = Field(False, description="Whether automated warmup is enabled")
    is_default: bool = Field(False, description="Default sending account for owner")
    is_active: bool = Field(True, description="Whether account is active")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "email_accounts"
        indexes = [
            IndexModel([("owner_id", ASCENDING)], name="idx_email_acc_owner"),
            IndexModel([("email_address", ASCENDING)], name="idx_email_acc_address"),
        ]

    async def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        await self.save()


class EmailTemplate(Document):
    """Reusable email template with variable placeholders."""
    owner_id: PydanticObjectId = Field(..., description="Owner user ID")
    name: str = Field(..., description="Template name")
    category: str = Field("cold_outreach", description="cold_outreach | follow_up | newsletter | custom")
    subject: str = Field(..., description="Template subject line with variables")
    body: str = Field(..., description="Template body content with variables")
    variables_used: List[str] = Field(default_factory=list, description="Variables detected in template")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "email_templates"
        indexes = [
            IndexModel([("owner_id", ASCENDING)], name="idx_template_owner"),
        ]

    async def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        await self.save()


class Campaign(Document):
    """Multi-step email campaign definition."""
    owner_id: PydanticObjectId = Field(..., description="Owner user ID")
    name: str = Field(..., description="Campaign name")
    status: str = Field("draft", description="draft | active | paused | completed | cancelled")

    sending_account_id: Optional[PydanticObjectId] = Field(None, description="ID of EmailAccount used to send")
    daily_limit: int = Field(50, description="Max emails per day for this campaign")
    ab_testing_enabled: bool = Field(False, description="Whether A/B subject testing is enabled")
    schedule_config: Dict[str, str] = Field(
        default_factory=lambda: {"time_zone": "UTC", "send_window_start": "09:00", "send_window_end": "17:00"}
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "campaigns"
        indexes = [
            IndexModel([("owner_id", ASCENDING)], name="idx_campaign_owner"),
            IndexModel([("status", ASCENDING)], name="idx_campaign_status"),
        ]

    async def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        await self.save()


class CampaignStep(Document):
    """Single step within a campaign sequence."""
    campaign_id: PydanticObjectId = Field(..., description="Parent campaign ID")
    step_number: int = Field(1, description="Step order sequence (1, 2, 3...)")
    delay_days: int = Field(0, description="Days to wait after previous step")
    step_type: str = Field("email", description="email | follow_up")

    subject: str = Field(..., description="Step subject line template")
    body: str = Field(..., description="Step email body template")
    template_id: Optional[PydanticObjectId] = Field(None, description="Optional associated EmailTemplate ID")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "campaign_steps"
        indexes = [
            IndexModel([("campaign_id", ASCENDING), ("step_number", ASCENDING)], name="idx_step_camp_seq", unique=True),
        ]


class CampaignRecipient(Document):
    """Enrolled lead recipient in a campaign sequence."""
    campaign_id: PydanticObjectId = Field(..., description="Parent campaign ID")
    lead_id: PydanticObjectId = Field(..., description="Enrolled Lead ID")
    owner_id: PydanticObjectId = Field(..., description="Owner user ID")

    email: str = Field(..., description="Recipient email address")
    first_name: Optional[str] = Field(None, description="Recipient first name")
    company: Optional[str] = Field(None, description="Recipient company name")

    current_step: int = Field(1, description="Current step sequence number")
    status: str = Field("pending", description="pending | sent | opened | clicked | replied | bounced | unsubscribed")

    variables: Dict[str, str] = Field(default_factory=dict, description="Resolved key-value variables")
    unsubscribe_token: str = Field(..., description="Unique token for unsubscribe link")

    scheduled_at: Optional[datetime] = Field(None, description="Next scheduled send time")
    sent_at: Optional[datetime] = Field(None, description="Timestamp of last send")
    opened_at: Optional[datetime] = Field(None, description="Timestamp of first open")
    clicked_at: Optional[datetime] = Field(None, description="Timestamp of first click")
    replied_at: Optional[datetime] = Field(None, description="Timestamp of reply")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "campaign_recipients"
        indexes = [
            IndexModel([("campaign_id", ASCENDING), ("lead_id", ASCENDING)], name="idx_recip_camp_lead", unique=True),
            IndexModel([("campaign_id", ASCENDING), ("status", ASCENDING)], name="idx_recip_camp_status"),
            IndexModel([("unsubscribe_token", ASCENDING)], name="idx_recip_unsub", unique=True),
        ]

    async def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        await self.save()


class EmailEvent(Document):
    """Log of email interaction events (send, open, click, reply, bounce, unsubscribe)."""
    campaign_id: PydanticObjectId = Field(..., description="Associated campaign ID")
    recipient_id: PydanticObjectId = Field(..., description="Associated recipient ID")
    lead_id: PydanticObjectId = Field(..., description="Associated lead ID")
    owner_id: PydanticObjectId = Field(..., description="Owner user ID")

    event_type: str = Field(..., description="send | open | click | reply | bounce | unsubscribe")
    link_url: Optional[str] = Field(None, description="Target URL if click event")
    user_agent: Optional[str] = Field(None, description="Browser/Client User-Agent")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "email_events"
        indexes = [
            IndexModel([("campaign_id", ASCENDING), ("event_type", ASCENDING)], name="idx_event_camp_type"),
            IndexModel([("recipient_id", ASCENDING)], name="idx_event_recipient"),
        ]


class EmailAnalytics(Document):
    """Aggregated analytics metrics for a campaign."""
    campaign_id: PydanticObjectId = Field(..., description="Campaign ID")
    owner_id: PydanticObjectId = Field(..., description="Owner user ID")

    total_recipients: int = Field(0)
    total_sent: int = Field(0)
    total_opened: int = Field(0)
    total_clicked: int = Field(0)
    total_replied: int = Field(0)
    total_bounced: int = Field(0)
    total_unsubscribed: int = Field(0)

    open_rate: float = Field(0.0, description="Percentage 0-100%")
    click_rate: float = Field(0.0, description="Percentage 0-100%")
    reply_rate: float = Field(0.0, description="Percentage 0-100%")
    bounce_rate: float = Field(0.0, description="Percentage 0-100%")

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "email_analytics"
        indexes = [
            IndexModel([("campaign_id", ASCENDING)], name="idx_analytics_campaign", unique=True),
            IndexModel([("owner_id", ASCENDING)], name="idx_analytics_owner"),
        ]

    async def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
        await self.save()
