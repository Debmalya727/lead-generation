"""
Phase 14.1 — Enterprise Knowledge Gateway.
Unified ingestion gateway alias pointing to EnterpriseKnowledgeGatewayService.
"""
from app.knowledge.gateway.gateway_service import (
    enterprise_knowledge_gateway,
    EnterpriseKnowledgeGatewayService,
)

# Canonical export alias
EnterpriseKnowledgeGateway = EnterpriseKnowledgeGatewayService

__all__ = [
    "enterprise_knowledge_gateway",
    "EnterpriseKnowledgeGateway",
    "EnterpriseKnowledgeGatewayService",
]
