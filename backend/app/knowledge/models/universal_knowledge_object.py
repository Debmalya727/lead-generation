"""
Phase 14 — Universal Knowledge Object Manager.
Canonical representation builder for UniversalKnowledgeObjectDoc consumed across all 19 pipeline stages.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.mongodb.collections.knowledge import UniversalKnowledgeObjectDoc

logger = logging.getLogger("backend.knowledge.universal_object")


class UniversalKnowledgeObjectManager:
    """Manages creation, hashing, fingerprinting, and retrieval of Universal Knowledge Objects."""

    async def create_knowledge_object(
        self,
        title: str,
        content: str,
        source_type: str = "crm",
        asset_type: str = "pdf",
        mime_type: str = "application/pdf",
        owner_id: str = "user_default",
        organization_id: str = "default_org",
        workspace_id: str = "default_workspace",
        permissions: Optional[List[str]] = None,
        security_acl: Optional[List[str]] = None,
        classification: str = "Internal",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UniversalKnowledgeObjectDoc:
        k_id = f"kobj_{uuid.uuid4().hex[:16]}"
        sha256_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        sha512_hash = hashlib.sha512(content.encode("utf-8")).hexdigest()
        fingerprint = hashlib.md5((title + content[:200]).encode("utf-8")).hexdigest()

        obj = UniversalKnowledgeObjectDoc(
            knowledge_id=k_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            owner_id=owner_id,
            source_type=source_type,
            asset_type=asset_type,
            mime_type=mime_type,
            title=title,
            description=f"Knowledge Object for {title}",
            summary=content[:200] + "...",
            language="en",
            checksum_sha256=sha256_hash,
            checksum_sha512=sha512_hash,
            fingerprint=fingerprint,
            payload={"raw_content": content, "size_bytes": len(content.encode("utf-8"))},
            permissions=permissions or [owner_id, "admin"],
            security_acl=security_acl or [owner_id, "admin"],
            classification=classification,
            version=1,
            status="Active",
            tags=[source_type, asset_type],
            metadata=metadata or {},
        )
        try:
            await obj.insert()
        except Exception:
            pass

        logger.info(f"[UniversalKnowledgeObject] Created KnowledgeObject '{k_id}' ({title}) sha256={sha256_hash[:8]}")
        return obj

    async def get_by_id(self, knowledge_id: str) -> Optional[UniversalKnowledgeObjectDoc]:
        return await UniversalKnowledgeObjectDoc.find_one(UniversalKnowledgeObjectDoc.knowledge_id == knowledge_id)


universal_knowledge_object_manager = UniversalKnowledgeObjectManager()
