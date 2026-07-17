from typing import List, Optional, Tuple
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb.collections.lead import Lead


class LeadRepository:
    async def get_by_id(self, lead_id: str, owner_id: str) -> Optional[Lead]:
        """Fetch a specific lead document by ID, checking owner constraint."""
        try:
            lead = await Lead.get(ObjectId(lead_id))
        except Exception:
            lead = await Lead.get(lead_id)
            
        if lead and str(lead.owner_id) == owner_id:
            return lead
        return None

    async def list_leads(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        min_score: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Lead], int]:
        """Query and paginate leads with filters, owner scope, and keyword searches."""
        query = {"owner_id": ObjectId(owner_id)}
        
        if status:
            query["status"] = status
            
        if min_score is not None:
            query["score"] = {"$gte": min_score}
            
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"location": {"$regex": search, "$options": "i"}},
                {"website": {"$regex": search, "$options": "i"}},
            ]
            
        find_query = Lead.find(query)
        total_count = await find_query.count()
        
        # Determine sorting parameters
        direction = DESCENDING if sort_order.lower() == "desc" else ASCENDING
        leads = await find_query.sort([(sort_by, direction)]).skip(skip).limit(limit).to_list()
        
        return leads, total_count

    async def create(self, lead_data: dict) -> Lead:
        """Persist a new lead record."""
        lead = Lead(**lead_data)
        await lead.insert()
        return lead

    async def update(self, lead: Lead, update_data: dict) -> Lead:
        """Update and save modifications to a lead record."""
        for field, value in update_data.items():
            if hasattr(lead, field):
                setattr(lead, field, value)
        await lead.update_timestamp()
        return lead

    async def delete(self, lead: Lead) -> bool:
        """Remove a lead record from MongoDB."""
        await lead.delete()
        return True

    async def bulk_create(self, leads_data: List[dict]) -> int:
        """Bulk insert multiple lead documents to speed up CSV imports."""
        if not leads_data:
            return 0
            
        documents = [Lead(**data) for data in leads_data]
        # Beanie insert_many
        result = await Lead.insert_many(documents)
        return len(result.inserted_ids)
