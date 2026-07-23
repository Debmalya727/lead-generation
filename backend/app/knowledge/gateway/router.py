"""
Phase 14.1 Enterprise Knowledge Gateway — Production REST API Router.
Endpoints:
  - POST /api/v1/knowledge/gateway/ingest
  - POST /api/v1/knowledge/gateway/import-jobs
  - GET  /api/v1/knowledge/gateway/import-jobs/{job_id}
  - GET  /api/v1/knowledge/gateway/import-jobs
  - POST /api/v1/knowledge/gateway/sources
  - GET  /api/v1/knowledge/gateway/sources
  - GET  /api/v1/knowledge/gateway/documents
  - GET  /api/v1/knowledge/gateway/documents/{document_id}
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Security
from app.knowledge.gateway.gateway_service import enterprise_knowledge_gateway
from app.knowledge.gateway.import_tracker import import_tracker
from app.knowledge.gateway.schemas import (
    CreateImportJobRequest,
    CreateSourceRequest,
    ImportJobResponse,
    IngestAssetRequest,
    KnowledgeObjectResponse,
    SourceConfigResponse,
)

logger = logging.getLogger("backend.knowledge.gateway.router")

router = APIRouter(prefix="/gateway", tags=["14.1 Enterprise Knowledge Gateway"])


@router.post("/ingest", response_model=KnowledgeObjectResponse)
async def ingest_asset(req: IngestAssetRequest):
    """Ingest enterprise asset into structured Knowledge Object."""
    try:
        doc = await enterprise_knowledge_gateway.ingest_asset(
            title=req.title,
            content_or_uri=req.content_or_uri,
            asset_type=req.asset_type,
            user_id=req.user_id,
            org_id=req.org_id,
            security_acl=req.security_acl,
            metadata=req.metadata,
            job_id=req.job_id,
        )
        return doc.model_dump()
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        logger.error(f"[GatewayRouter] Ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Internal Knowledge Gateway error")


@router.post("/import-jobs", response_model=ImportJobResponse)
async def create_import_job(req: CreateImportJobRequest):
    """Start asynchronous bulk import job."""
    job = await import_tracker.create_job(user_id=req.user_id, source_name=req.source_name, file_count=req.file_count)
    return job.model_dump()


@router.get("/import-jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(job_id: str):
    """Retrieve import job status and progress metrics."""
    job = await import_tracker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Import job '{job_id}' not found")
    return job.model_dump()


@router.get("/import-jobs", response_model=List[ImportJobResponse])
async def list_import_jobs(user_id: str = Query("user_default"), limit: int = Query(50)):
    """List import jobs for user."""
    jobs = await import_tracker.list_jobs(user_id=user_id, limit=limit)
    return [j.model_dump() for j in jobs]


@router.post("/sources", response_model=SourceConfigResponse)
async def create_source(req: CreateSourceRequest):
    """Register active knowledge source connector."""
    src = await enterprise_knowledge_gateway.create_source(name=req.name, source_type=req.source_type, config=req.config)
    return src.model_dump()


@router.get("/sources", response_model=List[SourceConfigResponse])
async def list_sources():
    """List registered knowledge sources."""
    sources = await enterprise_knowledge_gateway.list_sources()
    return [s.model_dump() for s in sources]


@router.get("/documents", response_model=List[KnowledgeObjectResponse])
async def list_documents(user_id: str = Query("user_default"), limit: int = Query(50)):
    """List ingested Knowledge Objects."""
    docs = await enterprise_knowledge_gateway.list_documents(user_id=user_id, limit=limit)
    return [d.model_dump() for d in docs]


@router.get("/documents/{document_id}", response_model=KnowledgeObjectResponse)
async def get_document(document_id: str):
    """Get single Knowledge Object details."""
    doc = await enterprise_knowledge_gateway.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Knowledge Object '{document_id}' not found")
    return doc.model_dump()
