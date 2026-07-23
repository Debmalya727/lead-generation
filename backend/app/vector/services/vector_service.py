"""
Vector Service Layer.

Indexes platform collections (`Lead`, `CompanyIntelligence`, `LeadScore`, `SalesIntelligenceReport`,
`ResearchReport`, `Campaigns`, `Emails`, `VerifiedFacts`, `KnowledgeGraph`) into vector store chunks.
"""
import logging
from typing import List, Dict, Any, Optional

from app.vector.providers.factory import get_vector_provider
from app.vector.embeddings.factory import get_embedding_provider
from app.vector.chunking.chunker import DocumentChunker, SlidingWindowChunker
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.database.mongodb.repositories.scoring_repository import ScoringRepository
from app.database.mongodb.repositories.sales_intelligence_repository import SalesIntelligenceRepository
from app.database.mongodb.repositories.research_repository import ResearchRepository
from app.database.mongodb.repositories.outreach_repository import CampaignRepository, EmailTemplateRepository

logger = logging.getLogger("backend.vector.service")


class VectorService:
    """Service layer managing vector indexing, semantic search, and reindexing."""

    def __init__(
        self,
        lead_repo: LeadRepository,
        intel_repo: IntelligenceRepository,
        scoring_repo: ScoringRepository,
        sales_intel_repo: SalesIntelligenceRepository,
        research_repo: ResearchRepository,
        campaign_repo: CampaignRepository,
        template_repo: EmailTemplateRepository,
    ):
        self.lead_repo = lead_repo
        self.intel_repo = intel_repo
        self.scoring_repo = scoring_repo
        self.sales_intel_repo = sales_intel_repo
        self.research_repo = research_repo
        self.campaign_repo = campaign_repo
        self.template_repo = template_repo

        self.vector_provider = get_vector_provider()
        self.embedding_provider = get_embedding_provider()
        self.chunker = DocumentChunker()
        self.window_chunker = SlidingWindowChunker()

    async def index_lead_knowledge(self, lead_id: str, owner_id: str) -> Dict[str, Any]:
        """Index all knowledge modules associated with a specific lead_id into vector chunks."""
        logger.info(f"VectorService indexing all knowledge for lead_id '{lead_id}' (owner: {owner_id})")

        total_indexed_chunks = 0
        indexed_collections = []

        # 1. Fetch Lead
        lead = await self.lead_repo.get_by_id(lead_id, owner_id)
        if not lead:
            raise ValueError(f"Lead '{lead_id}' not found or access denied.")

        # Delete existing chunks for this lead before re-indexing
        await self.vector_provider.delete_document_chunks(document_id=lead_id, owner_id=owner_id)

        # Index Lead Document
        lead_text = f"Lead Business Name: {lead.name}\nWebsite: {lead.website or 'N/A'}\nEmail: {lead.email or 'N/A'}\nPhone: {lead.phone or 'N/A'}\nLocation: {lead.location or 'N/A'}\nStatus: {lead.status}\nRating Score: {lead.score or 0}/100"
        lead_chunks = self.chunker.chunk_document(
            content=lead_text,
            document_id=lead_id,
            lead_id=lead.id,
            owner_id=lead.owner_id,
            collection_name="leads",
            title=f"Lead: {lead.name}",
            metadata={"status": lead.status, "score": lead.score or 0},
        )
        if lead_chunks:
            await self._embed_and_upsert(lead_chunks)
            total_indexed_chunks += len(lead_chunks)
            indexed_collections.append("leads")

        # 2. Index Company Intelligence
        intel = await self.intel_repo.get_by_lead_id(lead_id, owner_id)
        if intel and intel.intelligence:
            intel_data = intel.intelligence
            intel_text = (
                f"Company Intelligence for {lead.name}:\n"
                f"Industry: {intel_data.industry or 'N/A'}\n"
                f"Company Size: {intel_data.company_size or 'N/A'}\n"
                f"Revenue Estimate: {intel_data.revenue_estimate or 'N/A'}\n"
                f"Tech Stack: {', '.join([t.get('name', '') for t in intel.tech_stack])}\n"
                f"Pain Points: {', '.join(intel_data.pain_points or [])}\n"
                f"Buying Signals: {', '.join(intel_data.buying_signals or [])}"
            )
            intel_chunks = self.chunker.chunk_document(
                content=intel_text,
                document_id=str(intel.id),
                lead_id=lead.id,
                owner_id=lead.owner_id,
                collection_name="company_intelligence",
                title=f"Company Intelligence: {lead.name}",
                metadata={"industry": intel_data.industry},
            )
            if intel_chunks:
                await self._embed_and_upsert(intel_chunks)
                total_indexed_chunks += len(intel_chunks)
                indexed_collections.append("company_intelligence")

        # 3. Index Lead Score
        scoring = await self.scoring_repo.get_by_lead_id(lead_id, owner_id)
        if scoring:
            score_text = (
                f"Lead Rating Score for {lead.name}:\n"
                f"Score Rating: {scoring.score}/100 ({scoring.score_tier})\n"
                f"Profile Version: {scoring.version}\n"
                f"Rule Breakdown: {scoring.rules_breakdown}\n"
                f"Reasoning Summary: {scoring.reasoning}"
            )
            score_chunks = self.chunker.chunk_document(
                content=score_text,
                document_id=str(scoring.id),
                lead_id=lead.id,
                owner_id=lead.owner_id,
                collection_name="lead_scores",
                title=f"Lead Score: {lead.name} ({scoring.score}/100)",
                metadata={"score": scoring.score, "score_tier": scoring.score_tier},
            )
            if score_chunks:
                await self._embed_and_upsert(score_chunks)
                total_indexed_chunks += len(score_chunks)
                indexed_collections.append("lead_scores")

        # 4. Index Sales Intelligence Report
        sales_intel = await self.sales_intel_repo.get_by_lead_id(lead_id, owner_id)
        if sales_intel and sales_intel.status == "completed":
            dm_names = [dm.name for dm in (sales_intel.decision_makers or [])]
            sig_descs = [sig.description for sig in (sales_intel.growth_signals or [])]
            sales_text = (
                f"Sales Intelligence Report for {lead.name}:\n"
                f"Buying Intent Score: {sales_intel.intent_score}/100 ({sales_intel.intent_level})\n"
                f"Intent Rationale: {sales_intel.intent_reason}\n"
                f"Decision Makers: {', '.join(dm_names)}\n"
                f"Growth Signals: {', '.join(sig_descs)}\n"
                f"Primary Channel: {sales_intel.recommendations.best_outreach_channel if sales_intel.recommendations else 'Email'}\n"
                f"Pitch Angle: {sales_intel.recommendations.recommended_product_pitch if sales_intel.recommendations else 'N/A'}\n"
                f"Conversation Starter: {sales_intel.recommendations.conversation_starter if sales_intel.recommendations else 'N/A'}"
            )
            sales_chunks = self.chunker.chunk_document(
                content=sales_text,
                document_id=str(sales_intel.id),
                lead_id=lead.id,
                owner_id=lead.owner_id,
                collection_name="sales_intelligence",
                title=f"Sales Intelligence: {lead.name} ({sales_intel.intent_level} Intent)",
                metadata={"intent_score": sales_intel.intent_score, "intent_level": sales_intel.intent_level},
            )
            if sales_chunks:
                await self._embed_and_upsert(sales_chunks)
                total_indexed_chunks += len(sales_chunks)
                indexed_collections.append("sales_intelligence")

        # 5. Index AI Research Report
        research = await self.research_repo.get_by_lead_id(lead_id, owner_id)
        if research and research.status == "completed":
            res_text = (
                f"AI Research Report for {lead.name}:\n"
                f"Executive Summary: {research.ai_summary.executive_summary if research.ai_summary else ''}\n"
                f"Business Model: {research.website_findings.business_model if research.website_findings else ''}\n"
                f"Sales Opportunity: {research.ai_summary.sales_opportunity if research.ai_summary else ''}\n"
                f"Hiring Velocity: {research.hiring_findings.hiring_velocity if research.hiring_findings else 'Medium'}\n"
                f"Tech Maturity: {research.tech_findings.tech_maturity if research.tech_findings else ''}\n"
                f"Competitors: {', '.join([c.name for c in (research.competitor_findings.competitors if research.competitor_findings else [])])}\n"
                f"SWOT Strengths: {', '.join(research.ai_summary.swot.strengths if (research.ai_summary and research.ai_summary.swot) else [])}"
            )
            res_chunks = self.chunker.chunk_document(
                content=res_text,
                document_id=str(research.id),
                lead_id=lead.id,
                owner_id=lead.owner_id,
                collection_name="research_reports",
                title=f"Research Report: {lead.name}",
                metadata={"confidence": research.overall_confidence},
            )
            if res_chunks:
                await self._embed_and_upsert(res_chunks)
                total_indexed_chunks += len(res_chunks)
                indexed_collections.append("research_reports")

        return {
            "lead_id": lead_id,
            "company_name": lead.name,
            "total_indexed_chunks": total_indexed_chunks,
            "indexed_collections": indexed_collections,
        }

    async def _embed_and_upsert(self, chunks: List[Dict[str, Any]]) -> None:
        """Embed text contents and upsert chunks into vector database."""
        contents = [c["content"] for c in chunks]
        embeddings = await self.embedding_provider.embed_batch(contents)

        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb

        await self.vector_provider.upsert_chunks(chunks)

    async def search_vectors(
        self,
        query: str,
        owner_id: str,
        collection_name: Optional[str] = None,
        lead_id: Optional[str] = None,
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Perform raw vector search."""
        query_vector = await self.embedding_provider.embed_text(query)
        return await self.vector_provider.search_vectors(
            query_vector=query_vector,
            owner_id=owner_id,
            collection_name=collection_name,
            lead_id=lead_id,
            top_k=top_k,
            score_threshold=score_threshold,
        )

    async def get_index_status(self, owner_id: str) -> Dict[str, Any]:
        """Fetch index metrics and provider health."""
        return await self.vector_provider.get_status(owner_id)

    async def delete_document_chunks(self, document_id: str, owner_id: str) -> bool:
        """Delete vector chunks for a document."""
        return await self.vector_provider.delete_document_chunks(document_id, owner_id)
