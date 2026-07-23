"""
Phase 14.1 Enterprise Knowledge Gateway — Event Subscriber.
Listens to system events (CRM, Voice, Meetings, Research) and automatically routes them
into the Knowledge Gateway pipeline.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.knowledge.gateway.gateway_service import enterprise_knowledge_gateway

logger = logging.getLogger("backend.knowledge.gateway.event_subscriber")


class KnowledgeGatewayEventSubscriber:
    """Event subscriber listening to system-wide asset events."""

    async def handle_crm_lead_created(self, event_data: Dict[str, Any]):
        lead_name = event_data.get("company_name", "Lead")
        content = f"CRM Lead: {lead_name}. Industry: {event_data.get('industry', 'N/A')}. Notes: {event_data.get('notes', '')}"
        await enterprise_knowledge_gateway.ingest_asset(
            title=f"CRM Lead - {lead_name}",
            content_or_uri=content,
            asset_type="crm",
            user_id=event_data.get("user_id", "user_default"),
        )
        logger.info(f"[GatewaySubscriber] Auto-ingested CRM Lead: '{lead_name}'")

    async def handle_voice_call_completed(self, event_data: Dict[str, Any]):
        call_id = event_data.get("call_id", "voice_call")
        transcript = event_data.get("transcript", "Voice call completed.")
        await enterprise_knowledge_gateway.ingest_asset(
            title=f"Voice Call - {call_id}",
            content_or_uri=transcript,
            asset_type="voice",
            user_id=event_data.get("user_id", "user_default"),
        )
        logger.info(f"[GatewaySubscriber] Auto-ingested Voice Call: '{call_id}'")

    async def handle_meeting_completed(self, event_data: Dict[str, Any]):
        meeting_title = event_data.get("title", "Meeting")
        notes = event_data.get("summary", "Meeting notes.")
        await enterprise_knowledge_gateway.ingest_asset(
            title=f"Meeting - {meeting_title}",
            content_or_uri=notes,
            asset_type="meetings",
            user_id=event_data.get("user_id", "user_default"),
        )
        logger.info(f"[GatewaySubscriber] Auto-ingested Meeting: '{meeting_title}'")


gateway_event_subscriber = KnowledgeGatewayEventSubscriber()
