"""
Phase 14.8.5 — Citation Engine.
Generates granular citations across Document, Page, Paragraph, Chunk, Table, Image,
Meeting Timestamp, Speaker, and Source.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.database.mongodb.collections.knowledge import CitationRecord

logger = logging.getLogger("backend.knowledge.citations")

CITATION_TYPES = {"document", "page", "paragraph", "chunk", "table", "image", "meeting_timestamp", "speaker", "source"}


class CitationEngine:
    """Granular evidence citation generator and attribution mapper."""

    async def generate_citation(
        self,
        source_id: str,
        document_id: str,
        snippet: str,
        citation_type: str = "chunk",
        location_reference: str = "",
        speaker_name: Optional[str] = None,
    ) -> CitationRecord:
        citation_type = citation_type.lower()
        if citation_type not in CITATION_TYPES:
            citation_type = "chunk"

        cid = f"cite_{uuid.uuid4().hex[:12]}"
        rec = CitationRecord(
            citation_id=cid,
            citation_type=citation_type,
            source_id=source_id,
            document_id=document_id,
            location_reference=location_reference,
            snippet=snippet[:250],
            speaker_name=speaker_name,
        )
        try:
            await rec.insert()
        except Exception:
            pass

        logger.info(f"[CitationEngine] Generated citation '{cid}' ({citation_type}) for doc '{document_id}'")
        return rec

    async def get_citations_for_document(self, document_id: str) -> List[CitationRecord]:
        return await CitationRecord.find(CitationRecord.document_id == document_id).to_list()


citation_engine = CitationEngine()
