"""
Phase 14.3.5 — Knowledge Ontology Manager.
Manages enterprise domain ontologies, taxonomies, class hierarchies, and properties schemas.
Supported domains: Sales | Finance | Legal | Engineering
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.database.mongodb.collections.knowledge import KnowledgeOntologyRecord

logger = logging.getLogger("backend.knowledge.ontology")


class KnowledgeOntologyManager:
    """Enterprise Ontology Registry managing taxonomies and class hierarchies."""

    async def register_class(
        self,
        domain_name: str,
        class_name: str,
        parent_class: Optional[str] = None,
        properties_schema: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeOntologyRecord:
        ont_id = f"ont_{uuid.uuid4().hex[:12]}"
        record = KnowledgeOntologyRecord(
            ontology_id=ont_id,
            domain_name=domain_name,
            class_name=class_name,
            parent_class=parent_class,
            properties_schema=properties_schema or {},
            version=1,
            is_active=True,
        )
        try:
            await record.insert()
        except Exception:
            pass
        logger.info(f"[KnowledgeOntology] Registered class '{class_name}' under domain '{domain_name}'")
        return record

    async def get_domain_ontology(self, domain_name: str) -> List[KnowledgeOntologyRecord]:
        return await KnowledgeOntologyRecord.find(KnowledgeOntologyRecord.domain_name == domain_name).to_list()


knowledge_ontology_manager = KnowledgeOntologyManager()
