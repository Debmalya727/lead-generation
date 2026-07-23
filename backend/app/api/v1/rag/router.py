"""
REST API Router for RAG Operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.database.mongodb.collections.user import User
from app.vector.pipelines.rag_pipeline import RAGPipeline
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGSourceCitation

router = APIRouter()


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Execute Enterprise Grounded RAG Query",
    description="Answer user questions using retrieved platform knowledge chunks with strict source citations and zero hallucination enforcement.",
)
async def query_rag_pipeline(
    payload: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """Execute RAG question-answering pipeline."""
    try:
        pipeline = RAGPipeline()
        res = await pipeline.execute_query(
            question=payload.question,
            owner_id=str(current_user.id),
            collection_name=payload.collection_name,
            lead_id=payload.lead_id,
            top_k=payload.top_k,
        )

        sources = [
            RAGSourceCitation(
                doc_num=s["doc_num"],
                collection=s["collection"],
                document_id=s["document_id"],
                lead_id=s.get("lead_id"),
                title=s["title"],
                score=s["score"],
                content_snippet=s["content_snippet"],
                metadata=s.get("metadata", {}),
            )
            for s in res.get("sources", [])
        ]

        return RAGQueryResponse(
            question=payload.question,
            answer=res["answer"],
            confidence_score=res["confidence_score"],
            summary_points=res.get("summary_points", []),
            sources=sources,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute RAG query: {str(e)}"
        )
