"""
Phase 13.10 — Voice Analytics Alert Manager.
Manages alert rule definitions, threshold configuration, and alert lifecycle.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.mongodb.collections.voice_analytics import VoiceAnalyticsAlertDocument
from app.voice.analytics.analytics_engine import DEFAULT_ALERT_RULES

logger = logging.getLogger("backend.voice.analytics.alerts")


class VoiceAnalyticsAlertManager:
    """
    Manages alert rules and provides API-level operations:
    - List all alert rules
    - Get active unresolved alerts
    - Acknowledge / resolve alerts
    - Get alert history
    """

    def list_alert_rules(self) -> List[Dict[str, Any]]:
        """Return all configured alert rules."""
        return [
            {
                "rule_id": r["rule_id"],
                "metric": r["metric"],
                "operator": r["operator"],
                "threshold": r["threshold"],
                "severity": r["severity"],
                "message": r["message"],
            }
            for r in DEFAULT_ALERT_RULES
        ]

    async def get_active_alerts(
        self,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Return all active (unresolved) alerts."""
        query = VoiceAnalyticsAlertDocument.find(
            VoiceAnalyticsAlertDocument.resolved == False
        )
        if severity:
            query = VoiceAnalyticsAlertDocument.find(
                VoiceAnalyticsAlertDocument.resolved == False,
                VoiceAnalyticsAlertDocument.severity == severity,
            )
        docs = await query.sort("-triggered_at").limit(limit).to_list()
        return [d.model_dump() for d in docs]

    async def get_alert_history(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return all alerts (resolved + active) for history view."""
        docs = await VoiceAnalyticsAlertDocument.find_all().sort("-triggered_at").limit(limit).to_list()
        return [d.model_dump() for d in docs]

    async def acknowledge_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        doc = await VoiceAnalyticsAlertDocument.find_one(
            VoiceAnalyticsAlertDocument.alert_id == alert_id
        )
        if doc:
            doc.acknowledged = True
            doc.resolved = True
            doc.resolved_at = datetime.now(timezone.utc)
            await doc.save()
            return doc.model_dump()
        return None

    async def resolve_all(self, user_id: Optional[str] = None) -> int:
        """Bulk resolve all active alerts for a user."""
        query = VoiceAnalyticsAlertDocument.find(
            VoiceAnalyticsAlertDocument.resolved == False
        )
        if user_id:
            query = VoiceAnalyticsAlertDocument.find(
                VoiceAnalyticsAlertDocument.resolved == False,
                VoiceAnalyticsAlertDocument.user_id == user_id,
            )
        docs = await query.to_list()
        count = 0
        for doc in docs:
            doc.resolved = True
            doc.acknowledged = True
            doc.resolved_at = datetime.now(timezone.utc)
            await doc.save()
            count += 1
        return count

    def get_severity_counts(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {"critical": 0, "warning": 0, "info": 0}
        for a in alerts:
            sev = a.get("severity", "info")
            counts[sev] = counts.get(sev, 0) + 1
        return counts


voice_analytics_alert_manager = VoiceAnalyticsAlertManager()
