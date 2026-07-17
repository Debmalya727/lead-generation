from datetime import datetime, timezone
from typing import List, Optional
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING


class DiscoveredLead(BaseModel):
    id: str = Field(..., description="Unique generated ID for select/unselect actions")
    name: str = Field(..., description="Business name")
    website: Optional[str] = Field(None, description="Website URL")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    location: Optional[str] = Field(None, description="Location details")
    score: Optional[int] = Field(None, description="Calculated lead quality rating")
    provider: str = Field(..., description="Source provider name")


class ScrapeJob(Document):
    owner_id: PydanticObjectId = Field(..., description="Operator owner ID")
    keyword: str = Field(..., description="Keyword query used for discovery search")
    location: str = Field(..., description="Location query used for search")
    providers: List[str] = Field(..., description="List of providers selected")
    status: str = Field(default="pending", description="pending, running, completed, cancelled, failed")
    progress: float = Field(default=0.0, description="Completion percentage 0.0 - 100.0")
    total_results: int = Field(default=0, description="Total number of results discovered")
    error_message: Optional[str] = Field(None, description="Detailed job error details if failed")
    results: List[DiscoveredLead] = Field(default_factory=list, description="Array of discovered leads")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "jobs"
        indexes = [
            IndexModel([("owner_id", ASCENDING)], name="idx_job_owner_id"),
            IndexModel([("status", ASCENDING)], name="idx_job_status"),
            IndexModel([("created_at", ASCENDING)], name="idx_job_created_at")
        ]

    async def update_timestamp(self) -> None:
        """Update the updated_at timestamp on modification."""
        self.updated_at = datetime.now(timezone.utc)
        await self.save()
