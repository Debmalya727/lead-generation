"""
Shared Artifact Store for Multi-Agent Collaboration Engine.

Allows agents to store, version, query, and reuse structured artifacts across the platform.
"""
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.database.mongodb.collections.agent_collaboration import AgentArtifactDocument

logger = logging.getLogger("backend.agents.collaboration.artifacts")


class ArtifactStore:
    """Repository managing versioned shared agent artifacts."""

    async def save_artifact(
        self,
        job_id: str,
        owner_agent: str,
        artifact_type: str,
        content: Dict[str, Any],
        task_id: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        confidence: int = 85,
    ) -> Dict[str, Any]:
        """Save a new artifact or a new version of an existing artifact type."""
        # Determine next version for this job & artifact_type
        existing = await AgentArtifactDocument.find(
            AgentArtifactDocument.job_id == job_id,
            AgentArtifactDocument.artifact_type == artifact_type,
        ).sort("-version").first_or_none()

        version = (existing.version + 1) if existing else 1
        parent_id = existing.artifact_id if existing else None
        artifact_id = f"art_{artifact_type}_{uuid.uuid4().hex[:10]}"

        doc = AgentArtifactDocument(
            artifact_id=artifact_id,
            job_id=job_id,
            task_id=task_id,
            owner_agent=owner_agent,
            artifact_type=artifact_type,
            title=title or f"{owner_agent.replace('_agent','').capitalize()} Artifact (v{version})",
            metadata=metadata or {},
            content=content,
            confidence=confidence,
            version=version,
            parent_version_id=parent_id,
            created_at=datetime.now(timezone.utc),
        )
        await doc.insert()
        logger.info(f"ArtifactStore saved artifact '{artifact_id}' (type: {artifact_type}, v{version}) for job '{job_id}'")

        return self._to_dict(doc)

    async def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Fetch artifact by artifact_id."""
        doc = await AgentArtifactDocument.find_one(AgentArtifactDocument.artifact_id == artifact_id)
        return self._to_dict(doc) if doc else None

    async def list_artifacts(
        self,
        job_id: str,
        artifact_type: Optional[str] = None,
        owner_agent: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List artifacts for a job with optional type/owner filters."""
        query = [AgentArtifactDocument.job_id == job_id]
        if artifact_type:
            query.append(AgentArtifactDocument.artifact_type == artifact_type)
        if owner_agent:
            query.append(AgentArtifactDocument.owner_agent == owner_agent)

        docs = await AgentArtifactDocument.find(*query).sort("-version").limit(limit).to_list()
        return [self._to_dict(d) for d in docs]

    async def get_latest_artifact(self, job_id: str, artifact_type: str) -> Optional[Dict[str, Any]]:
        """Fetch latest version of an artifact type for a job."""
        doc = await AgentArtifactDocument.find(
            AgentArtifactDocument.job_id == job_id,
            AgentArtifactDocument.artifact_type == artifact_type,
        ).sort("-version").first_or_none()
        return self._to_dict(doc) if doc else None

    def _to_dict(self, doc: AgentArtifactDocument) -> Dict[str, Any]:
        """Convert Beanie document to dict."""
        return {
            "artifact_id": doc.artifact_id,
            "job_id": doc.job_id,
            "task_id": doc.task_id,
            "owner_agent": doc.owner_agent,
            "artifact_type": doc.artifact_type,
            "title": doc.title,
            "metadata": doc.metadata,
            "content": doc.content,
            "confidence": doc.confidence,
            "version": doc.version,
            "parent_version_id": doc.parent_version_id,
            "created_at": doc.created_at.isoformat() if hasattr(doc.created_at, 'isoformat') else str(doc.created_at),
        }
