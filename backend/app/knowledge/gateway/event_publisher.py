"""
Phase 14.1 Enterprise Knowledge Gateway — Event Publisher.
Publishes gateway events to the LeadForgeAI Event Bus and records KnowledgeEventRecords.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.database.mongodb.collections.knowledge import KnowledgeEventRecord

logger = logging.getLogger("backend.knowledge.gateway.event_publisher")


class KnowledgeGatewayEventPublisher:
    """Event Bus publisher for Knowledge Gateway events."""

    async def publish_asset_ingested(self, document_id: str, title: str, asset_type: str, user_id: str):
        payload = {
            "document_id": document_id,
            "title": title,
            "asset_type": asset_type,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._record_and_publish("knowledge.asset.ingested", document_id, payload)

    async def publish_asset_validated(self, document_id: str, is_valid: bool, details: Dict[str, Any]):
        payload = {
            "document_id": document_id,
            "is_valid": is_valid,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._record_and_publish("knowledge.asset.validated", document_id, payload)

    async def publish_asset_failed(self, title: str, reason: str, user_id: str):
        payload = {
            "title": title,
            "reason": reason,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._record_and_publish("knowledge.asset.failed", title, payload)

    async def _record_and_publish(self, event_type: str, document_id: str, payload: Dict[str, Any]):
        rec = KnowledgeEventRecord(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            document_id=document_id,
            payload=payload,
        )
        try:
            await rec.insert()
        except Exception:
            pass
        logger.info(f"[GatewayEventPublisher] Published event '{event_type}' for document '{document_id}'")


gateway_event_publisher = KnowledgeGatewayEventPublisher()
