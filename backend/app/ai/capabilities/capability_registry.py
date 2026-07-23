"""
Capability Registry for Phase 12.7B AI Gateway.
Defines all 12 known capabilities with metadata and default routing.
"""
from typing import Dict, List, Any
import logging

from app.database.mongodb.collections.ai_gateway_extended import CapabilityRegistryDocument

logger = logging.getLogger("backend.ai.capabilities.registry")

# Static capability definitions — seeded into MongoDB on startup
KNOWN_CAPABILITIES: List[Dict[str, Any]] = [
    {
        "capability_id": "chat",
        "name": "Conversational Chat",
        "description": "Standard chat/conversation interactions",
        "default_provider": "gemini",
        "default_model": "gemini-1.5-flash",
        "tags": ["conversation", "general"],
    },
    {
        "capability_id": "reasoning",
        "name": "Complex Reasoning",
        "description": "Multi-step logical reasoning, chain-of-thought analysis",
        "default_provider": "claude",
        "default_model": "claude-3-5-sonnet",
        "tags": ["reasoning", "analysis"],
    },
    {
        "capability_id": "vision",
        "name": "Vision & Image Understanding",
        "description": "Image analysis, OCR, visual question answering",
        "default_provider": "openai",
        "default_model": "gpt-4o",
        "tags": ["vision", "multimodal"],
    },
    {
        "capability_id": "embedding",
        "name": "Text Embeddings",
        "description": "Dense vector embeddings for semantic search and RAG",
        "default_provider": "openai",
        "default_model": "text-embedding-3-small",
        "tags": ["embedding", "vector", "rag"],
    },
    {
        "capability_id": "tool_calling",
        "name": "Tool / Function Calling",
        "description": "Structured function calling with JSON output",
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
        "tags": ["tools", "function_calling"],
    },
    {
        "capability_id": "summarization",
        "name": "Text Summarization",
        "description": "Condense long documents into concise summaries",
        "default_provider": "gemini",
        "default_model": "gemini-1.5-flash",
        "tags": ["summarization", "condensation"],
    },
    {
        "capability_id": "translation",
        "name": "Language Translation",
        "description": "Translate text between languages",
        "default_provider": "gemini",
        "default_model": "gemini-1.5-flash",
        "tags": ["translation", "language"],
    },
    {
        "capability_id": "planning",
        "name": "Task Planning",
        "description": "Decompose complex goals into actionable plans",
        "default_provider": "claude",
        "default_model": "claude-3-5-sonnet",
        "tags": ["planning", "agent"],
    },
    {
        "capability_id": "coding",
        "name": "Code Generation",
        "description": "Generate, review, and debug code across languages",
        "default_provider": "claude",
        "default_model": "claude-3-5-sonnet",
        "tags": ["coding", "development"],
    },
    {
        "capability_id": "research",
        "name": "Research & Analysis",
        "description": "Deep research synthesis from large document sets",
        "default_provider": "gemini",
        "default_model": "gemini-1.5-pro",
        "tags": ["research", "analysis", "long_context"],
    },
    {
        "capability_id": "json_generation",
        "name": "Structured JSON Generation",
        "description": "Extract or generate strictly typed JSON outputs",
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
        "tags": ["json", "structured", "extraction"],
    },
    {
        "capability_id": "long_context",
        "name": "Long Context Processing",
        "description": "Process documents exceeding 100K tokens",
        "default_provider": "gemini",
        "default_model": "gemini-1.5-pro",
        "tags": ["long_context", "documents"],
    },
]


class CapabilityRegistryManager:
    """Registry of all known capabilities seeded from constants."""

    _capabilities: Dict[str, Dict[str, Any]] = {
        c["capability_id"]: c for c in KNOWN_CAPABILITIES
    }

    async def seed(self) -> None:
        """Seed capabilities into MongoDB if collection is empty."""
        count = await CapabilityRegistryDocument.count()
        if count == 0:
            for cap in KNOWN_CAPABILITIES:
                doc = CapabilityRegistryDocument(**cap)
                await doc.insert()
            logger.info(f"CapabilityRegistry: Seeded {len(KNOWN_CAPABILITIES)} capabilities.")

    def get(self, capability_id: str) -> Dict[str, Any]:
        """Return static capability definition."""
        return self._capabilities.get(capability_id, {})

    def list_all(self) -> List[Dict[str, Any]]:
        """Return all known capabilities."""
        return KNOWN_CAPABILITIES

    def is_known(self, capability_id: str) -> bool:
        """Check if a capability name is recognized."""
        return capability_id in self._capabilities


capability_registry_manager = CapabilityRegistryManager()
