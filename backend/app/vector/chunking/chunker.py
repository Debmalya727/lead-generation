"""
Intelligent Text Chunkers for Enterprise Knowledge Platform.

Supports:
- Document-level section chunking
- Semantic paragraph chunking
- Sliding character window chunking with metadata preservation
"""
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("backend.vector.chunking")


class DocumentChunker:
    """Document-level chunker splitting text by major section headings or double line breaks."""

    def chunk_document(
        self,
        content: str,
        document_id: str,
        lead_id: Optional[str],
        owner_id: str,
        collection_name: str,
        title: str,
        metadata: Optional[Dict[str, Any]] = None,
        max_chunk_size: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Split document into section chunks while preserving metadata tags."""
        if not content or not content.strip():
            return []

        sections = [s.strip() for s in re.split(r"\n\s*\n|#+\s+", content) if s.strip()]
        chunks: List[Dict[str, Any]] = []

        current_text = ""
        chunk_idx = 0

        for sec in sections:
            if len(current_text) + len(sec) + 1 <= max_chunk_size:
                current_text = f"{current_text}\n{sec}".strip() if current_text else sec
            else:
                if current_text:
                    c_id = f"{document_id}_chunk_{chunk_idx}"
                    chunks.append({
                        "chunk_id": c_id,
                        "document_id": document_id,
                        "lead_id": lead_id,
                        "owner_id": owner_id,
                        "collection_name": collection_name,
                        "title": title,
                        "content": current_text,
                        "chunk_index": chunk_idx,
                        "metadata": metadata or {},
                    })
                    chunk_idx += 1
                current_text = sec

        if current_text:
            c_id = f"{document_id}_chunk_{chunk_idx}"
            chunks.append({
                "chunk_id": c_id,
                "document_id": document_id,
                "lead_id": lead_id,
                "owner_id": owner_id,
                "collection_name": collection_name,
                "title": title,
                "content": current_text,
                "chunk_index": chunk_idx,
                "metadata": metadata or {},
            })

        total = len(chunks)
        for item in chunks:
            item["total_chunks"] = total

        return chunks


class SlidingWindowChunker:
    """Sliding window character chunker with configurable overlap."""

    def chunk_text(
        self,
        content: str,
        document_id: str,
        lead_id: Optional[str],
        owner_id: str,
        collection_name: str,
        title: str,
        metadata: Optional[Dict[str, Any]] = None,
        window_size: int = 600,
        overlap: int = 100,
    ) -> List[Dict[str, Any]]:
        """Chunk text using a sliding character window."""
        if not content:
            return []

        chunks = []
        start = 0
        chunk_idx = 0
        text_len = len(content)

        while start < text_len:
            end = min(start + window_size, text_len)
            sub_text = content[start:end].strip()

            if sub_text:
                c_id = f"{document_id}_win_{chunk_idx}"
                chunks.append({
                    "chunk_id": c_id,
                    "document_id": document_id,
                    "lead_id": lead_id,
                    "owner_id": owner_id,
                    "collection_name": collection_name,
                    "title": title,
                    "content": sub_text,
                    "chunk_index": chunk_idx,
                    "metadata": metadata or {},
                })
                chunk_idx += 1

            if end == text_len:
                break
            start += (window_size - overlap)

        total = len(chunks)
        for item in chunks:
            item["total_chunks"] = total

        return chunks
