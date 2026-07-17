from datetime import datetime
from typing import List, Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class DiscoveryStartRequest(BaseModel):
    keyword: str = Field(..., min_length=1, description="Keyword target (e.g. HVAC)")
    location: str = Field(..., min_length=1, description="Location filter (e.g. Chicago)")
    providers: List[str] = Field(..., min_length=1, description="Target directories (google_maps, justdial, etc.)")


class DiscoveredLeadResponse(BaseModel):
    id: str
    name: str
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    score: Optional[int] = None
    provider: str


class JobStatusResponse(BaseModel):
    id: PydanticObjectId
    keyword: str
    location: str
    providers: List[str]
    status: str
    progress: float
    total_results: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class SaveLeadsRequest(BaseModel):
    lead_ids: List[str] = Field(..., min_items=1, description="List of discovered lead IDs to import into workspace leads")
