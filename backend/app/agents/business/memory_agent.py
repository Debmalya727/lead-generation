"""
MemoryAgent — Phase 11 Milestone 2 Business Agent.

Queries Phase 10 Vector Search and RAG Pipeline to retrieve:
- Research report history
- Lead history and campaign data
- Email analytics
- Knowledge graph notes
- Sales intelligence summaries

Returns: memory_context, citations, relevant_facts, confidence.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from app.agents.runtime.base_agent import BaseAgent
from app.agents.runtime.result import AgentResult
from app.agents.runtime.context import ExecutionContext
from app.agents.registry.registry import register_agent
from app.agents.prompts.memory_prompts import (
    MEMORY_AGENT_SYSTEM_PROMPT,
    MEMORY_AGENT_USER_PROMPT,
)
from app.agents.memory.shared_memory import SharedMemory
from app.ai.providers.factory import get_llm_provider

logger = logging.getLogger("backend.agents.business.memory")


@register_agent
class MemoryAgent(BaseAgent):
    """Production Memory Agent querying vector search and RAG for lead-specific context."""

    agent_id: str = "memory_agent"
    name: str = "Memory Agent"
    version: str = "1.0.0"
    description: str = "Queries Phase 10 Vector Search and RAG Pipeline to retrieve comprehensive lead memory, relationship history, campaign data, and knowledge context with source citations."
    capabilities: List[str] = [
        "vector_search_retrieval",
        "rag_context_retrieval",
        "lead_history_extraction",
        "campaign_history_analysis",
        "email_analytics_retrieval",
        "knowledge_graph_lookup",
        "relationship_strength_scoring",
    ]

    def __init__(self):
        super().__init__()
        self.shared_memory = SharedMemory()
        self.llm_provider = get_llm_provider()

    async def execute(self, context: ExecutionContext) -> AgentResult:
        """Retrieve comprehensive lead memory using vector search and RAG."""
        self.log(f"MemoryAgent executing for lead_id='{context.lead_id}' (job: {context.job_id})")

        lead_id = context.lead_id
        owner_id = context.owner_id
        research_context = context.inputs.get("research_output", {})
        company_name = research_context.get("company_name", context.inputs.get("company_name", "Target Company"))

        # Build search queries from research context
        search_queries = self._build_search_queries(company_name, research_context)

        # Execute vector search across multiple queries
        all_vector_results = []
        for query in search_queries[:3]:  # Limit to 3 queries for performance
            results = await self.shared_memory.search(
                query=query,
                owner_id=owner_id,
                lead_id=lead_id,
                top_k=5,
            )
            all_vector_results.extend(results)

        self.log(f"Vector search retrieved {len(all_vector_results)} memory chunks.")

        # Execute RAG for structured context
        rag_result = await self.shared_memory.retrieve_rag(
            question=f"What is the full relationship history, campaign history, and key intelligence for {company_name}?",
            owner_id=owner_id,
            lead_id=lead_id,
        )

        # Format results for LLM
        vector_text = self._format_vector_results(all_vector_results)
        rag_text = rag_result.get("answer", "No RAG context available.") if isinstance(rag_result, dict) else str(rag_result)

        user_prompt = MEMORY_AGENT_USER_PROMPT.format(
            company_name=company_name,
            lead_id=lead_id or "N/A",
            vector_results=vector_text[:3000],
            rag_context=rag_text[:2000],
            research_context=json.dumps(research_context, indent=2, default=str)[:1500],
        )

        raw_response = await self.llm_provider.complete(
            prompt=user_prompt,
            system_prompt=MEMORY_AGENT_SYSTEM_PROMPT,
        )

        parsed = self._parse_llm_json(raw_response, company_name=company_name)
        confidence = parsed.get("confidence", 60)

        artifact = {
            "name": f"memory_context_{lead_id or 'no_lead'}.json",
            "type": "memory_context",
            "content": parsed,
        }
        self.artifacts.append(artifact)

        self.log(f"MemoryAgent completed. Relationship strength: {parsed.get('relationship_strength', 'unknown')}, Confidence={confidence}")

        return AgentResult(
            status="completed",
            confidence=confidence,
            messages=[
                f"Memory retrieval completed for '{company_name}'.",
                f"Relationship strength: {parsed.get('relationship_strength', 'unknown')}.",
                f"Retrieved {len(all_vector_results)} memory chunks from vector index.",
            ],
            logs=self.logs,
            artifacts=self.artifacts,
            outputs=parsed,
            metadata={"agent_type": "memory", "company_name": company_name, "lead_id": lead_id},
        )

    def _build_search_queries(self, company_name: str, research_context: Dict[str, Any]) -> List[str]:
        """Build targeted vector search queries."""
        queries = [f"{company_name} company intelligence sales"]
        if research_context.get("pain_points"):
            queries.append(f"{company_name} pain points challenges")
        if research_context.get("technology_stack"):
            queries.append(f"{company_name} technology stack integrations")
        queries.append(f"{company_name} email campaign outreach history")
        return queries

    def _format_vector_results(self, results: List[Dict[str, Any]]) -> str:
        """Format vector search results for LLM prompt."""
        if not results:
            return "No vector memory records found for this lead."
        lines = []
        for i, r in enumerate(results[:10], 1):
            content = r.get("content", r.get("text", str(r)))[:400]
            score = r.get("score", r.get("similarity", 0.0))
            collection = r.get("collection_name", "unknown")
            lines.append(f"[{i}] Collection: {collection} | Score: {score:.3f}\n{content}")
        return "\n\n".join(lines)

    def _parse_llm_json(self, raw: str, company_name: str = "Target Company") -> Dict[str, Any]:
        """Parse LLM JSON response with fallback."""
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as e:
            self.log(f"JSON parse warning: {str(e)}")
            return {
                "memory_summary": f"No historical memory found for {company_name}.",
                "lead_history": [],
                "campaign_history": [],
                "email_history": [],
                "relationship_strength": "new",
                "last_touchpoint": None,
                "knowledge_notes": [],
                "prior_objections": [],
                "engagement_score": 0,
                "citations": [],
                "confidence": 30,
                "memory_gaps": ["No indexed memory available for this lead."],
            }
