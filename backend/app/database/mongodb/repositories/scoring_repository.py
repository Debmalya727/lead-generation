from typing import List, Optional, Tuple
from bson import ObjectId
from app.database.mongodb.collections.lead_score import LeadScore


class ScoringRepository:
    """Repository for LeadScore CRUD operations with owner isolation."""

    async def get_by_lead_id(self, lead_id: str, owner_id: str) -> Optional[LeadScore]:
        """Fetch score document by lead_id with owner constraint."""
        return await LeadScore.find_one({
            "lead_id": ObjectId(lead_id),
            "owner_id": ObjectId(owner_id),
        })

    async def get_by_id(self, doc_id: str, owner_id: str) -> Optional[LeadScore]:
        """Fetch score document by its own ID with owner constraint."""
        try:
            doc = await LeadScore.get(ObjectId(doc_id))
        except Exception:
            doc = await LeadScore.get(doc_id)
        if doc and str(doc.owner_id) == owner_id:
            return doc
        return None

    async def get_by_id_no_auth(self, doc_id: str) -> Optional[LeadScore]:
        """Fetch score document by ID without owner check (internal Celery use)."""
        try:
            return await LeadScore.get(ObjectId(doc_id))
        except Exception:
            return await LeadScore.get(doc_id)

    async def create(self, data: dict) -> LeadScore:
        """Persist a new LeadScore document."""
        doc = LeadScore(**data)
        await doc.insert()
        return doc

    async def update(self, doc: LeadScore, update_data: dict) -> LeadScore:
        """Apply field updates and persist the document."""
        for field, value in update_data.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
        await doc.update_timestamp()
        return doc

    async def delete(self, doc: LeadScore) -> bool:
        """Delete a LeadScore document."""
        await doc.delete()
        return True

    async def list_by_owner(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[LeadScore], int]:
        """List all score documents belonging to an owner, paginated."""
        query = {"owner_id": ObjectId(owner_id)}
        find_query = LeadScore.find(query)
        total = await find_query.count()
        docs = await find_query.skip(skip).limit(limit).to_list()
        return docs, total
