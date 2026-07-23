"""
Enterprise RAG Pipeline Execution Engine.

Pipeline Sequence:
1. User Question -> Retriever (Vector Similarity Search)
2. Context Builder -> Format Retrieved Evidence Chunks & Citations
3. Grounded Prompt Assembly
4. LLM Provider (`get_llm_provider()`) -> Grounded Answer + Source Citations + Evidence Panel
"""
import json
import logging
from typing import Dict, Any, List, Optional

from app.vector.retrievers.retriever import HybridRetriever
from app.ai.providers.factory import get_llm_provider
from app.vector.prompts.rag_prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT

logger = logging.getLogger("backend.vector.rag_pipeline")


class RAGPipeline:
    """Execution engine for Retrieval-Augmented Generation question answering."""

    def __init__(self):
        self.retriever = HybridRetriever()

    async def execute_query(
        self,
        question: str,
        owner_id: str,
        collection_name: Optional[str] = None,
        lead_id: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Execute full RAG pipeline and return grounded answer with citations."""
        logger.info(f"RAGPipeline executing query='{question}' (owner: {owner_id})")

        # 1. Retrieve relevant evidence chunks from vector store
        chunks = await self.retriever.retrieve(
            query=question,
            owner_id=owner_id,
            collection_name=collection_name,
            lead_id=lead_id,
            top_k=top_k,
            score_threshold=0.0,
        )

        if not chunks:
            return {
                "answer": "No relevant knowledge or evidence chunks were found in the workspace index matching your question.",
                "confidence_score": 0,
                "sources": [],
                "summary_points": ["No matching vector chunks retrieved."],
            }

        # 2. Build context text & source citations
        context_blocks = []
        sources = []

        for idx, c in enumerate(chunks, 1):
            source_tag = f"[Doc {idx}: {c['collection_name']} / {c['title']}]"
            context_blocks.append(f"--- EVIDENCE {source_tag} (Similarity Score: {c['score']}) ---\n{c['content']}\n")
            sources.append({
                "doc_num": idx,
                "collection": c["collection_name"],
                "document_id": c["document_id"],
                "lead_id": c.get("lead_id"),
                "title": c["title"],
                "score": c["score"],
                "content_snippet": c["content"][:200] + ("..." if len(c["content"]) > 200 else ""),
                "metadata": c.get("metadata", {}),
            })

        formatted_context = "\n".join(context_blocks)

        # 3. Build RAG User Prompt
        user_prompt = RAG_USER_PROMPT.format(
            question=question,
            context_text=formatted_context,
        )

        # 4. Call LLM Provider
        try:
            llm_provider = get_llm_provider()
            raw_response = await llm_provider.complete(
                prompt=user_prompt,
                system_prompt=RAG_SYSTEM_PROMPT,
            )

            cleaned_text = raw_response.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            parsed = json.loads(cleaned_text.strip())

            scores = [float(s["score"]) for s in sources if s.get("score") is not None]
            avg_score = (sum(scores) / len(scores)) if scores else 0.8
            calculated_confidence = int(avg_score * 100)

            return {
                "answer": parsed.get("answer", "Based on retrieved context, here is the answer: " + raw_response),
                "confidence_score": parsed.get("confidence_score", calculated_confidence),
                "summary_points": parsed.get("summary_points", ["Retrieved grounded facts from platform knowledge base."]),
                "sources": sources,
            }

        except Exception as e:
            logger.warning(f"Fallback RAG response formatting due to parsing exception: {str(e)}")
            return {
                "answer": f"Based on retrieved platform knowledge ({len(sources)} documents), here is the context summary:\n\n" + "\n".join([f"- {s['title']}: {s['content_snippet']}" for s in sources]),
                "confidence_score": 75,
                "summary_points": ["Extracted grounded evidence from vector store."],
                "sources": sources,
            }
