"""
Phase 14.2.5 — Enterprise Knowledge Compiler.
Compiles normalized documents and chunks into unified CompiledKnowledgeObject representations.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.mongodb.collections.knowledge import (
    CompiledKnowledgeObjectDoc,
    KnowledgeChunk,
    KnowledgeDocument,
)

logger = logging.getLogger("backend.knowledge.compiler")


class EnterpriseKnowledgeCompiler:
    """Compiles normalized documents into immutable, versioned CompiledKnowledgeObjects."""

    async def compile_document(
        self,
        document_id: str,
        user_id: str = "user_default",
    ) -> CompiledKnowledgeObjectDoc:
        doc = await KnowledgeDocument.find_one(KnowledgeDocument.document_id == document_id)
        if not doc:
            raise ValueError(f"Document '{document_id}' not found for compilation.")

        chunks = await KnowledgeChunk.find(KnowledgeChunk.document_id == document_id).to_list()
        compiled_text = "\n\n".join([c.content for c in chunks])

        # Generate SHA256 Checksum
        checksum = hashlib.sha256(compiled_text.encode("utf-8")).hexdigest()

        # Build Canonical Representation
        canonical_repr = {
            "title": doc.title,
            "file_type": doc.file_type,
            "language": doc.language,
            "total_chunks": len(chunks),
            "total_tokens": sum(c.token_count for c in chunks),
            "security_acl": doc.security_acl,
            "metadata": doc.metadata,
        }

        object_id = f"cko_{uuid.uuid4().hex[:16]}"
        compiled_obj = CompiledKnowledgeObjectDoc(
            object_id=object_id,
            document_id=document_id,
            user_id=user_id,
            compiled_text=compiled_text,
            canonical_representation=canonical_repr,
            chunks_count=len(chunks),
            entities_count=0,
            tables_count=sum(1 for c in chunks if c.chunk_strategy == "table"),
            images_count=0,
            checksum=checksum,
            version=doc.version,
            permissions=doc.security_acl,
            language=doc.language,
            compiled_at=datetime.now(timezone.utc),
        )
        try:
            await compiled_obj.insert()
        except Exception:
            pass

        logger.info(f"[KnowledgeCompiler] Compiled document '{document_id}' into CompiledKnowledgeObject '{object_id}' (checksum={checksum[:8]})")
        return compiled_obj

    async def get_compiled_object(self, object_id: str) -> Optional[CompiledKnowledgeObjectDoc]:
        return await CompiledKnowledgeObjectDoc.find_one(CompiledKnowledgeObjectDoc.object_id == object_id)

    async def get_by_document(self, document_id: str) -> Optional[CompiledKnowledgeObjectDoc]:
        return await CompiledKnowledgeObjectDoc.find_one(CompiledKnowledgeObjectDoc.document_id == document_id)


enterprise_knowledge_compiler = EnterpriseKnowledgeCompiler()
