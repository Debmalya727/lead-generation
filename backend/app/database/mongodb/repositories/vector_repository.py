from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from bson import ObjectId
from app.database.mongodb.collections.vector_index import VectorChunk


class VectorRepository:
    """Repository for VectorChunk CRUD operations with owner isolation."""

    async def create_chunk(self, chunk_data: dict) -> VectorChunk:
        """Persist a single VectorChunk document."""
        chunk = VectorChunk(**chunk_data)
        await chunk.insert()
        return chunk

    async def bulk_create_chunks(self, chunks_data: List[dict]) -> int:
        """Bulk insert multiple VectorChunk documents."""
        if not chunks_data:
            return 0
        documents = [VectorChunk(**data) for data in chunks_data]
        result = await VectorChunk.insert_many(documents)
        return len(result.inserted_ids)

    async def delete_by_document_id(self, document_id: str, owner_id: str) -> int:
        """Delete all chunks belonging to a document_id with owner check."""
        try:
            o_id = ObjectId(owner_id)
        except Exception:
            o_id = owner_id

        chunks = await VectorChunk.find({"document_id": document_id, "owner_id": o_id}).to_list()
        for chunk in chunks:
            await chunk.delete()
        return len(chunks)

    async def delete_by_document_id_no_auth(self, document_id: str) -> int:
        """Delete document chunks without owner check (used by Celery tasks)."""
        chunks = await VectorChunk.find({"document_id": document_id}).to_list()
        for chunk in chunks:
            await chunk.delete()
        return len(chunks)

    async def delete_by_lead_id(self, lead_id: str, owner_id: str) -> int:
        """Delete all chunks associated with a lead."""
        try:
            l_id = ObjectId(lead_id)
            o_id = ObjectId(owner_id)
        except Exception:
            l_id = lead_id
            o_id = owner_id

        chunks = await VectorChunk.find({"lead_id": l_id, "owner_id": o_id}).to_list()
        for chunk in chunks:
            await chunk.delete()
        return len(chunks)

    async def get_all_by_owner(self, owner_id: str, collection_name: Optional[str] = None) -> List[VectorChunk]:
        """Fetch all chunks belonging to an owner, optionally filtered by collection_name."""
        try:
            query = {"owner_id": ObjectId(owner_id)}
        except Exception:
            query = {"owner_id": owner_id}

        if collection_name:
            query["collection_name"] = collection_name

        return await VectorChunk.find(query).to_list()

    async def get_status_metrics(self, owner_id: str) -> Dict[str, Any]:
        """Compute total chunks and breakdown by collection for owner."""
        try:
            o_id = ObjectId(owner_id)
        except Exception:
            o_id = owner_id

        all_chunks = await VectorChunk.find({"owner_id": o_id}).to_list()
        total_chunks = len(all_chunks)

        collections_summary: Dict[str, int] = {}
        for chunk in all_chunks:
            col = chunk.collection_name
            collections_summary[col] = collections_summary.get(col, 0) + 1

        return {
            "total_chunks": total_chunks,
            "collections": collections_summary,
        }
