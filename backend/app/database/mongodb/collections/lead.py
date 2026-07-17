from datetime import datetime, timezone
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel, ASCENDING, DESCENDING


class Lead(Document):
    owner_id: PydanticObjectId = Field(..., description="ID of the user who owns this lead record")
    name: str = Field(..., description="Name of the business lead")
    website: Optional[str] = Field(None, description="Website URL of the business")
    phone: Optional[str] = Field(None, description="Phone number of the business")
    email: Optional[str] = Field(None, description="Contact email address of the business")
    location: Optional[str] = Field(None, description="Physical location or city/state")
    score: Optional[int] = Field(None, description="Lead rating score (e.g. 0-100)")
    status: str = Field(default="discovered", description="Status of lead: discovered, contacted, converted, lost")
    job_id: Optional[PydanticObjectId] = Field(None, description="Scraping job ID associated with this lead")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "businesses"
        indexes = [
            IndexModel([("owner_id", ASCENDING)], name="idx_lead_owner_id"),
            IndexModel([("status", ASCENDING)], name="idx_lead_status"),
            IndexModel([("score", DESCENDING)], name="idx_lead_score_desc"),
            # Prevent duplicate lead names at the same physical location for the same user
            IndexModel(
                [("owner_id", ASCENDING), ("name", ASCENDING), ("location", ASCENDING)],
                unique=True,
                name="idx_owner_name_location_unique"
            )
        ]

    async def update_timestamp(self) -> None:
        """Update the updated_at timestamp on modification."""
        self.updated_at = datetime.now(timezone.utc)
        await self.save()
