from typing import List, Optional, Tuple
from bson import ObjectId
from app.database.mongodb.collections.intelligence import CompanyIntelligence


class IntelligenceRepository:
    async def get_by_lead_id(self, lead_id: str, owner_id: str) -> Optional[CompanyIntelligence]:
        """Fetch intelligence document by lead_id with owner constraint."""
        doc = await CompanyIntelligence.find_one({
            "lead_id": ObjectId(lead_id),
            "owner_id": ObjectId(owner_id)
        })
        return doc

    async def get_by_id(self, doc_id: str, owner_id: str) -> Optional[CompanyIntelligence]:
        """Fetch intelligence document by its own ID with owner constraint."""
        try:
            doc = await CompanyIntelligence.get(ObjectId(doc_id))
        except Exception:
            doc = await CompanyIntelligence.get(doc_id)
        if doc and str(doc.owner_id) == owner_id:
            return doc
        return None

    async def get_by_id_no_auth(self, doc_id: str) -> Optional[CompanyIntelligence]:
        """Fetch intelligence document by ID without owner check (used internally by Celery tasks)."""
        try:
            return await CompanyIntelligence.get(ObjectId(doc_id))
        except Exception:
            return await CompanyIntelligence.get(doc_id)

    async def create(self, data: dict) -> CompanyIntelligence:
        """Persist a new CompanyIntelligence document."""
        doc = CompanyIntelligence(**data)
        await doc.insert()
        return doc

    async def update(self, doc: CompanyIntelligence, update_data: dict) -> CompanyIntelligence:
        """Apply field updates and persist the document."""
        for field, value in update_data.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
        await doc.update_timestamp()
        return doc

    async def delete(self, doc: CompanyIntelligence) -> bool:
        """Delete a CompanyIntelligence document."""
        await doc.delete()
        return True

    async def list_by_owner(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[CompanyIntelligence], int]:
        """List all intelligence documents belonging to an owner, paginated."""
        query = {"owner_id": ObjectId(owner_id)}
        find_query = CompanyIntelligence.find(query)
        total = await find_query.count()
        docs = await find_query.skip(skip).limit(limit).to_list()
        return docs, total
