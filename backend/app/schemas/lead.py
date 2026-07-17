from datetime import datetime
from typing import List, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class LeadBase(BaseModel):
    name: str = Field(..., min_length=1, description="Business name")
    website: Optional[str] = Field(None, description="Website URL")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    location: Optional[str] = Field(None, description="Physical location")
    score: Optional[int] = Field(None, ge=0, le=100, description="Lead score (0-100)")
    status: str = Field(default="discovered", description="Current status of the lead")
    job_id: Optional[PydanticObjectId] = Field(None, description="Associated scraping job ID")


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[str] = None
    job_id: Optional[PydanticObjectId] = None


class LeadResponse(LeadBase):
    id: PydanticObjectId
    owner_id: PydanticObjectId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class LeadListResponse(BaseModel):
    items: List[LeadResponse]
    total_count: int
    page: int
    pages: int
    limit: int
