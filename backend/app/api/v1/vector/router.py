"""
REST API Router for Vector Operations.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_vector_service
from app.database.mongodb.collections.user import User
from app.vector.services.vector_service import VectorService
from app.schemas.vector import (
    VectorIndexRequest,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResultItem,
    VectorStatusResponse,
)
from app.tasks.vector_tasks import index_lead_knowledge_task, reindex_knowledge_base_task

router = APIRouter()


@router.post(
    "/index",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Index Lead Knowledge into Vector Store",
    description="Trigger an asynchronous Celery task to chunk and embed all lead data (Company Intelligence, Lead Score, Sales Intelligence, Research) into vector indexes.",
)
async def index_lead_knowledge_endpoint(
    payload: VectorIndexRequest,
    current_user: User = Depends(get_current_user),
):
    """Enqueue lead vector indexing task."""
    index_lead_knowledge_task.delay(payload.lead_id, str(current_user.id))
    return {
        "status": "accepted",
        "message": f"Vector indexing task enqueued for lead '{payload.lead_id}'.",
        "lead_id": payload.lead_id,
    }


@router.post(
    "/search",
    response_model=VectorSearchResponse,
    summary="Perform Raw Semantic Vector Search",
    description="Search vector chunks using cosine similarity with optional collection and lead_id filters.",
)
async def search_vectors_endpoint(
    payload: VectorSearchRequest,
    current_user: User = Depends(get_current_user),
    service: VectorService = Depends(get_vector_service),
):
    """Perform raw vector search."""
    results = await service.search_vectors(
        query=payload.query,
        owner_id=str(current_user.id),
        collection_name=payload.collection_name,
        lead_id=payload.lead_id,
        top_k=payload.top_k,
        score_threshold=payload.score_threshold,
    )

    items = [
        VectorSearchResultItem(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            lead_id=r.get("lead_id"),
            collection_name=r["collection_name"],
            title=r["title"],
            content=r["content"],
            score=r["score"],
            metadata=r.get("metadata", {}),
            created_at=r["created_at"],
        )
        for r in results
    ]

    return VectorSearchResponse(
        query=payload.query,
        total_matches=len(items),
        results=items,
    )


@router.get(
    "/status",
    response_model=VectorStatusResponse,
    summary="Get Vector Index Status & Chunk Count",
)
async def get_vector_status_endpoint(
    current_user: User = Depends(get_current_user),
    service: VectorService = Depends(get_vector_service),
):
    """Fetch vector store provider health & metrics."""
    res = await service.get_index_status(str(current_user.id))
    return VectorStatusResponse(
        provider=res["provider"],
        status=res["status"],
        total_chunks=res["total_chunks"],
        collections=res["collections"],
    )


@router.post(
    "/reindex",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch Reindex Entire Workspace",
)
async def reindex_workspace_endpoint(
    current_user: User = Depends(get_current_user),
):
    """Trigger workspace reindexing task."""
    reindex_knowledge_base_task.delay(str(current_user.id))
    return {
        "status": "accepted",
        "message": "Batch reindexing task enqueued for workspace.",
    }


@router.delete(
    "/document/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Document Vector Chunks",
)
async def delete_document_vector_chunks(
    id: str,
    current_user: User = Depends(get_current_user),
    service: VectorService = Depends(get_vector_service),
):
    """Delete chunks for a specific document ID."""
    deleted = await service.delete_document_chunks(document_id=id, owner_id=str(current_user.id))
    return {"status": "success", "message": f"Deleted vector chunks for document '{id}'.", "deleted": deleted}
