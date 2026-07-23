from datetime import datetime, timezone
from typing import List, Optional, Tuple
from bson import ObjectId
from app.database.mongodb.collections.sales_intelligence import SalesIntelligenceReport


class SalesIntelligenceRepository:
    async def get_by_lead_id(self, lead_id: str, owner_id: str) -> Optional[SalesIntelligenceReport]:
        """Fetch sales intelligence document by lead_id with owner constraint."""
        try:
            return await SalesIntelligenceReport.find_one({
                "lead_id": ObjectId(lead_id),
                "owner_id": ObjectId(owner_id)
            })
        except Exception:
            return await SalesIntelligenceReport.find_one({
                "lead_id": lead_id,
                "owner_id": owner_id
            })

    async def get_by_id(self, doc_id: str, owner_id: str) -> Optional[SalesIntelligenceReport]:
        """Fetch sales intelligence document by doc ID with owner constraint."""
        try:
            doc = await SalesIntelligenceReport.get(ObjectId(doc_id))
        except Exception:
            doc = await SalesIntelligenceReport.get(doc_id)
        if doc and str(doc.owner_id) == owner_id:
            return doc
        return None

    async def get_by_id_no_auth(self, doc_id: str) -> Optional[SalesIntelligenceReport]:
        """Fetch document by ID without owner check (used internally by Celery background workers)."""
        try:
            return await SalesIntelligenceReport.get(ObjectId(doc_id))
        except Exception:
            return await SalesIntelligenceReport.get(doc_id)

    async def create(self, data: dict) -> SalesIntelligenceReport:
        """Persist a new SalesIntelligenceReport document."""
        doc = SalesIntelligenceReport(**data)
        await doc.insert()
        return doc

    async def update(self, doc: SalesIntelligenceReport, update_data: dict) -> SalesIntelligenceReport:
        """Apply field updates and persist the document."""
        for field, value in update_data.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
        doc.updated_at = datetime.now(timezone.utc)
        await doc.save()
        return doc

    async def delete(self, doc: SalesIntelligenceReport) -> bool:
        """Delete a SalesIntelligenceReport document."""
        await doc.delete()
        return True

    async def list_by_owner(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[SalesIntelligenceReport], int]:
        """List sales intelligence reports belonging to an owner, paginated."""
        try:
            query = {"owner_id": ObjectId(owner_id)}
        except Exception:
            query = {"owner_id": owner_id}

        find_query = SalesIntelligenceReport.find(query)
        total = await find_query.count()
        docs = await find_query.sort([("intent_score", -1)]).skip(skip).limit(limit).to_list()
        return docs, total
