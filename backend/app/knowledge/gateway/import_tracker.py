"""
Phase 14.1 Enterprise Knowledge Gateway — Import Tracker.
Tracks asynchronous bulk ingestion jobs and progress metrics.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from app.database.mongodb.collections.knowledge import KnowledgeImportJob

logger = logging.getLogger("backend.knowledge.gateway.import_tracker")


class ImportTracker:
    """Manager for tracking async knowledge import jobs."""

    async def create_job(self, user_id: str, source_name: str, file_count: int = 1) -> KnowledgeImportJob:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = KnowledgeImportJob(
            job_id=job_id,
            user_id=user_id,
            source_name=source_name,
            file_count=file_count,
            status="in_progress",
            processed_count=0,
        )
        try:
            await job.insert()
        except Exception:
            pass
        logger.info(f"[ImportTracker] Created import job '{job_id}' ({source_name}) expected files={file_count}")
        return job

    async def update_progress(self, job_id: str, error: Optional[str] = None) -> Optional[KnowledgeImportJob]:
        job = await KnowledgeImportJob.find_one(KnowledgeImportJob.job_id == job_id)
        if not job:
            return None

        job.processed_count += 1
        if error:
            job.error_log = f"{job.error_log or ''}\n{error}".strip()

        if job.processed_count >= job.file_count:
            job.status = "completed" if not job.error_log else "completed_with_errors"

        await job.save()
        return job

    async def get_job(self, job_id: str) -> Optional[KnowledgeImportJob]:
        return await KnowledgeImportJob.find_one(KnowledgeImportJob.job_id == job_id)

    async def list_jobs(self, user_id: str = "user_default", limit: int = 50) -> List[KnowledgeImportJob]:
        return await KnowledgeImportJob.find(KnowledgeImportJob.user_id == user_id).sort("-created_at").limit(limit).to_list()


import_tracker = ImportTracker()
