from datetime import datetime, timezone
from typing import List, Optional, Tuple
from bson import ObjectId
from app.database.mongodb.collections.research import ResearchReport


class ResearchRepository:
    """Repository for ResearchReport CRUD operations with owner isolation."""

    async def get_by_lead_id(self, lead_id: str, owner_id: str) -> Optional[ResearchReport]:
        """Fetch research report by lead_id with owner constraint."""
        try:
            return await ResearchReport.find_one({
                "lead_id": ObjectId(lead_id),
                "owner_id": ObjectId(owner_id)
            })
        except Exception:
            return await ResearchReport.find_one({
                "lead_id": lead_id,
                "owner_id": owner_id
            })

    async def get_by_id(self, doc_id: str, owner_id: str) -> Optional[ResearchReport]:
        """Fetch research report by doc ID with owner constraint."""
        try:
            doc = await ResearchReport.get(ObjectId(doc_id))
        except Exception:
            doc = await ResearchReport.get(doc_id)
        if doc and str(doc.owner_id) == owner_id:
            return doc
        return None

    async def get_by_id_no_auth(self, doc_id: str) -> Optional[ResearchReport]:
        """Fetch document by ID without owner check (used internally by Celery workers)."""
        try:
            return await ResearchReport.get(ObjectId(doc_id))
        except Exception:
            return await ResearchReport.get(doc_id)

    async def create(self, data: dict) -> ResearchReport:
        """Persist a new ResearchReport document."""
        doc = ResearchReport(**data)
        await doc.insert()
        return doc

    async def update(self, doc: ResearchReport, update_data: dict) -> ResearchReport:
        """Apply field updates and persist the document."""
        for field, value in update_data.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
        doc.updated_at = datetime.now(timezone.utc)
        await doc.save()
        return doc

    async def delete(self, doc: ResearchReport) -> bool:
        """Delete a ResearchReport document."""
        await doc.delete()
        return True

    async def list_by_owner(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ResearchReport], int]:
        """List research reports belonging to an owner, paginated."""
        try:
            query = {"owner_id": ObjectId(owner_id)}
        except Exception:
            query = {"owner_id": owner_id}

        find_query = ResearchReport.find(query)
        total = await find_query.count()
        docs = await find_query.sort([("overall_confidence", -1)]).skip(skip).limit(limit).to_list()
        return docs, total
