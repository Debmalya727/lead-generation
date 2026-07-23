"""
AI Memory Manager for Phase 12.7B AI Gateway.
Stores prompt hashes, embedding IDs, summaries, and workflow artifacts.
"""
import uuid
import hashlib
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.database.mongodb.collections.ai_gateway_extended import (
    AIMemoryDocument,
    WorkflowArtifactDocument,
)

logger = logging.getLogger("backend.ai.memory.manager")


class MemoryManager:
    """
    Unified AI Memory store for tracking prompt hashes, embedding references,
    cache links, and workflow artifacts across sessions.
    """

    def _hash(self, text: str) -> str:
        """Compute SHA-256 hash of text."""
        return hashlib.sha256(text.encode()).hexdigest()

    async def store(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        embedding_ids: Optional[List[str]] = None,
        cache_keys: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> AIMemoryDocument:
        """Store a prompt hash record in memory."""
        prompt_hash = self._hash(prompt)

        # Deduplicate by prompt_hash + session
        existing = await AIMemoryDocument.find_one(
            AIMemoryDocument.prompt_hash == prompt_hash
        )
        if existing:
            # Update with any new links
            if embedding_ids:
                for eid in embedding_ids:
                    if eid not in existing.embedding_ids:
                        existing.embedding_ids.append(eid)
            if cache_keys:
                for ck in cache_keys:
                    if ck not in existing.cache_keys:
                        existing.cache_keys.append(ck)
            await existing.save()
            return existing

        doc = AIMemoryDocument(
            memory_id=f"mem_{uuid.uuid4().hex[:12]}",
            prompt_hash=prompt_hash,
            embedding_ids=embedding_ids or [],
            cache_keys=cache_keys or [],
            user_id=user_id,
            org_id=org_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            session_id=session_id,
            tags=tags or [],
        )
        await doc.insert()
        logger.debug(f"MemoryManager: Stored memory record for hash {prompt_hash[:16]}...")
        return doc

    async def retrieve(
        self,
        prompt: str,
    ) -> Optional[AIMemoryDocument]:
        """Look up memory record by prompt hash."""
        prompt_hash = self._hash(prompt)
        return await AIMemoryDocument.find_one(AIMemoryDocument.prompt_hash == prompt_hash)

    async def store_artifact(
        self,
        artifact_type: str,
        content: Dict[str, Any],
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        source_prompt_hash: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> WorkflowArtifactDocument:
        """Store a structured workflow artifact."""
        import json
        content_str = json.dumps(content, sort_keys=True, default=str)
        content_hash = self._hash(content_str)


        # Deduplicate by content hash
        existing = await WorkflowArtifactDocument.find_one(
            WorkflowArtifactDocument.content_hash == content_hash
        )
        if existing:
            return existing

        doc = WorkflowArtifactDocument(
            artifact_id=f"art_{uuid.uuid4().hex[:12]}",
            artifact_type=artifact_type,
            workflow_id=workflow_id,
            session_id=session_id,
            conversation_id=conversation_id,
            agent_id=agent_id,
            content=content,
            content_hash=content_hash,
            source_prompt_hash=source_prompt_hash,
            tags=tags or [],
        )
        await doc.insert()
        logger.debug(f"MemoryManager: Stored artifact '{artifact_type}' id={doc.artifact_id}")
        return doc

    async def get_artifact(self, artifact_id: str) -> Optional[WorkflowArtifactDocument]:
        """Retrieve artifact by ID."""
        return await WorkflowArtifactDocument.find_one(
            WorkflowArtifactDocument.artifact_id == artifact_id
        )

    async def list_artifacts(
        self,
        workflow_id: Optional[str] = None,
        artifact_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[WorkflowArtifactDocument]:
        """List workflow artifacts with optional filters."""
        query = WorkflowArtifactDocument.find_all()
        if workflow_id:
            query = WorkflowArtifactDocument.find(WorkflowArtifactDocument.workflow_id == workflow_id)
        if artifact_type:
            query = WorkflowArtifactDocument.find(WorkflowArtifactDocument.artifact_type == artifact_type)
        return await query.sort("-created_at").limit(limit).to_list()

    async def search_by_context(
        self,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[AIMemoryDocument]:
        """Search memory records by context identifiers."""
        results = await AIMemoryDocument.find_all().sort("-created_at").limit(limit).to_list()
        # Filter client-side (MongoDB filter works too but this is simpler for now)
        filtered = []
        for doc in results:
            if user_id and doc.user_id != user_id:
                continue
            if workflow_id and doc.workflow_id != workflow_id:
                continue
            if session_id and doc.session_id != session_id:
                continue
            filtered.append(doc)
        return filtered[:limit]


memory_manager = MemoryManager()
