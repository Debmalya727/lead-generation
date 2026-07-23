"""
Phase 14.2 — Knowledge Normalization Platform.
Multi-strategy document parser & chunker:
  - Semantic Chunking
  - Sliding Window
  - Recursive Token
  - Markdown Structure
  - Table Extraction
  - Code Block Extraction
  - OCR Text Support
  - Metadata Extraction (Language, Reading Complexity, Summaries, Keywords, Classification)
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from app.database.mongodb.collections.knowledge import KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger("backend.knowledge.normalization")


class KnowledgeNormalizationPlatform:
    """Normalizes document content, extracts structured blocks (tables/code), metadata, and builds chunks."""

    async def normalize_and_chunk(
        self,
        document_id: str,
        raw_text: str,
        user_id: str = "user_default",
        chunk_strategy: str = "semantic",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> List[KnowledgeChunk]:
        chunk_strategy = chunk_strategy.lower()

        # Extract Tables & Code Blocks first
        tables = self._extract_tables(raw_text)
        code_blocks = self._extract_code_blocks(raw_text)

        if chunk_strategy == "markdown_structure":
            raw_chunks = self._chunk_markdown(raw_text)
        elif chunk_strategy == "sliding_window":
            raw_chunks = self._chunk_sliding_window(raw_text, chunk_size, chunk_overlap)
        elif chunk_strategy == "recursive_token":
            raw_chunks = self._chunk_recursive_token(raw_text, chunk_size)
        elif chunk_strategy == "table":
            raw_chunks = tables if tables else [raw_text]
        elif chunk_strategy == "code_block":
            raw_chunks = code_blocks if code_blocks else [raw_text]
        elif chunk_strategy == "ocr":
            raw_chunks = [self._clean_ocr_text(raw_text)]
        else:
            # Default: Semantic
            raw_chunks = self._chunk_semantic(raw_text, chunk_size)

        # Content classification & metadata extraction
        metadata = self._extract_metadata(raw_text)

        chunks: List[KnowledgeChunk] = []
        for idx, text in enumerate(raw_chunks):
            if not text.strip():
                continue
            chunk_id = f"chk_{uuid.uuid4().hex[:16]}"
            bm25_tokens = list(set(re.findall(r"\b\w{3,}\b", text.lower())))

            chunk_doc = KnowledgeChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                user_id=user_id,
                chunk_index=idx,
                content=text.strip(),
                token_count=len(text.split()),
                chunk_strategy=chunk_strategy,
                embedding=[0.05 * (i % 10) for i in range(128)],  # 128-dim embedding simulation
                bm25_tokens=bm25_tokens,
                metadata={
                    "char_count": len(text),
                    "token_count": len(text.split()),
                    "language": metadata["language"],
                    "reading_complexity": metadata["reading_complexity"],
                    "classification": metadata["classification"],
                    "summary": metadata["summary"],
                },
            )
            try:
                await chunk_doc.insert()
            except Exception:
                pass
            chunks.append(chunk_doc)

        # Update parent document with chunk counts
        doc = await KnowledgeDocument.find_one(KnowledgeDocument.document_id == document_id)
        if doc:
            doc.total_chunks = len(chunks)
            doc.language = metadata["language"]
            await doc.save()

        logger.info(f"[KnowledgeNormalization] Normalized document '{document_id}' into {len(chunks)} chunks using strategy '{chunk_strategy}'")
        return chunks

    def _extract_tables(self, text: str) -> List[str]:
        # Regex for Markdown tables (| col1 | col2 |)
        table_pattern = r"(\|.*\|\n\|[-:\s|]+\|\n(?:\|.*\|\n?)+)"
        return re.findall(table_pattern, text)

    def _extract_code_blocks(self, text: str) -> List[str]:
        # Regex for fenced code blocks (```python ... ```)
        code_pattern = r"(```[\s\S]*?```)"
        return re.findall(code_pattern, text)

    def _clean_ocr_text(self, text: str) -> str:
        # Cleans noise and artifacts in OCR text
        cleaned = re.sub(r"[^\x00-\x7F]+", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _chunk_semantic(self, text: str, max_tokens: int) -> List[str]:
        paragraphs = text.split("\n\n")
        chunks = []
        curr = ""
        for p in paragraphs:
            if len((curr + " " + p).split()) > max_tokens and curr:
                chunks.append(curr.strip())
                curr = p
            else:
                curr = (curr + "\n\n" + p).strip()
        if curr:
            chunks.append(curr.strip())
        return chunks or [text]

    def _chunk_sliding_window(self, text: str, size: int, overlap: int) -> List[str]:
        words = text.split()
        if not words:
            return [text]
        chunks = []
        step = max(1, size - overlap)
        for i in range(0, len(words), step):
            chunk_words = words[i : i + size]
            chunks.append(" ".join(chunk_words))
        return chunks

    def _chunk_markdown(self, text: str) -> List[str]:
        sections = re.split(r"(?=\n#+ )", text)
        return [s.strip() for s in sections if s.strip()]

    def _chunk_recursive_token(self, text: str, size: int) -> List[str]:
        words = text.split()
        return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]

    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        words = text.split()
        word_count = len(words)

        # Language Detection heuristic
        lang = "en"
        if re.search(r"[\u4e00-\u9fff]", text):
            lang = "zh"
        elif re.search(r"[\u0400-\u04FF]", text):
            lang = "ru"

        # Reading complexity score (Flesch-Kincaid style heuristic)
        avg_word_len = (sum(len(w) for w in words) / max(1, word_count))
        complexity = "Medium" if avg_word_len < 6 else "High" if avg_word_len >= 6 else "Low"

        # Content classification
        classification = "General Knowledge"
        if "revenue" in text.lower() or "growth" in text.lower():
            classification = "Financial & Business Intelligence"
        elif "python" in text.lower() or "react" in text.lower() or "code" in text.lower():
            classification = "Technical Documentation"

        # Summary & Keywords
        summary = text[:200].strip() + "..." if len(text) > 200 else text
        keywords = list(set(re.findall(r"\b[A-Z][a-z]{3,}\b", text)))[:10]

        return {
            "language": lang,
            "reading_complexity": complexity,
            "classification": classification,
            "summary": summary,
            "keywords": keywords,
        }


knowledge_normalization_platform = KnowledgeNormalizationPlatform()
