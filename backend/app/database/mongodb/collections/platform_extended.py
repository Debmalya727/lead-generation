"""
Beanie MongoDB Document collections for Enterprise Interaction Platform:
- ScheduledJobDocument (scheduled_jobs)
- JobHistoryDocument (job_history)
- InstalledPluginDocument (installed_plugins)
- PluginSettingsDocument (plugin_settings)
- NotificationDocument (notifications)
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from beanie import Document
from pydantic import Field


class ScheduledJobDocument(Document):
    """Document defining background recurring and scheduled workflow jobs."""

    job_id: str = Field(..., description="Unique job ID e.g. job_123")
    name: str = Field(..., description="Human readable job name")
    description: str = Field(..., description="Job description")
    
    workflow_template_id: str = Field(..., description="Target WorkflowEngine template e.g. 'sales_discovery'")
    cron_expression: Optional[str] = Field(None, description="Standard cron string e.g. '0 0 * * *'")
    interval_seconds: Optional[int] = Field(None, description="Interval in seconds for periodic execution")
    
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Workflow inputs")
    is_active: bool = Field(True, description="Whether job is active")
    
    priority: str = Field("medium", description="low | medium | high | urgent")
    owner_id: str = Field(..., description="Owner user ID")
    
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = Field(0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "scheduled_jobs"
        indexes = [
            [("job_id", 1)],
            [("is_active", 1)],
            [("next_run_at", 1)],
        ]


class JobHistoryDocument(Document):
    """Document logging individual background job execution runs."""

    history_id: str = Field(..., description="Unique history record ID")
    job_id: str = Field(..., description="Associated ScheduledJob ID")
    workflow_execution_id: Optional[str] = Field(None, description="WorkflowEngine execution ID")
    
    status: str = Field("completed", description="started | completed | failed | cancelled")
    duration_ms: float = Field(0.0)
    error_message: Optional[str] = None
    
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "job_history"
        indexes = [
            [("history_id", 1)],
            [("job_id", 1), ("started_at", -1)],
        ]


class InstalledPluginDocument(Document):
    """Document tracking installed enterprise plugins in the Plugin SDK."""

    plugin_id: str = Field(..., description="Plugin identifier e.g. 'salesforce', 'hubspot', 'slack'")
    name: str = Field(..., description="Human readable plugin name")
    version: str = Field("1.0.0")
    category: str = Field("crm", description="crm | communication | productivity | custom")
    
    is_enabled: bool = Field(True)
    status: str = Field("installed", description="installed | active | error | disabled")
    capabilities: List[str] = Field(default_factory=list)
    
    installed_by: str = Field(..., description="User ID who installed plugin")
    installed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "installed_plugins"
        indexes = [
            [("plugin_id", 1)],
            [("is_enabled", 1)],
        ]


class PluginSettingsDocument(Document):
    """Document storing plugin API credentials, webhooks, and settings."""

    plugin_id: str = Field(..., description="Plugin identifier e.g. 'salesforce'")
    owner_id: str = Field(..., description="Owner user ID")
    
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "plugin_settings"
        indexes = [
            [("plugin_id", 1), ("owner_id", 1)],
        ]


class NotificationDocument(Document):
    """Document storing notifications dispatched by NotificationCenter."""

    notification_id: str = Field(..., description="Unique notification ID")
    recipient_id: str = Field(..., description="Target user ID")
    
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message body")
    type: str = Field("info", description="info | success | warning | error | workflow")
    
    event_type: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    
    is_read: bool = Field(False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notifications"
        indexes = [
            [("recipient_id", 1), ("is_read", 1)],
            [("created_at", -1)],
        ]
