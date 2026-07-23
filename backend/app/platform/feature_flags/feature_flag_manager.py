"""
FeatureFlagManager for Phase 12.5: Enterprise Platform Hardening.

Manages dynamic feature toggles and beta rollouts persisted in feature_flags collection.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.database.mongodb.collections.platform import FeatureFlagDocument

logger = logging.getLogger("backend.platform.feature_flags")


class FeatureFlagManager:
    """Manager handling dynamic feature flags."""

    DEFAULT_FLAGS = [
        {"flag_key": "voice_ai", "name": "Voice AI Agent", "description": "Enable conversational voice input & audio synthesis", "is_enabled": False},
        {"flag_key": "document_ai", "name": "Document AI RAG Indexing", "description": "Enable PDF/DOCX multi-modal RAG extraction", "is_enabled": True},
        {"flag_key": "enterprise_integrations", "name": "Enterprise Integrations Hub", "description": "Enable Salesforce & HubSpot CRM sync connectors", "is_enabled": False},
        {"flag_key": "beta_features", "name": "Beta Capabilities", "description": "Enable preview beta features across UI workspace", "is_enabled": True},
    ]

    async def is_enabled(self, flag_key: str, default: bool = False) -> bool:
        """Check if feature flag is enabled."""
        try:
            doc = await FeatureFlagDocument.find_one(FeatureFlagDocument.flag_key == flag_key)
            if doc:
                return bool(doc.is_enabled)
        except Exception:
            pass

        # Fallback to default flags
        def_flag = next((f for f in self.DEFAULT_FLAGS if f["flag_key"] == flag_key), None)
        return bool(def_flag["is_enabled"]) if def_flag else default

    async def set_flag(
        self,
        flag_key: str,
        is_enabled: bool,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> FeatureFlagDocument:
        """Set or update feature flag status."""
        doc = await FeatureFlagDocument.find_one(FeatureFlagDocument.flag_key == flag_key)
        if not doc:
            doc = FeatureFlagDocument(
                flag_key=flag_key,
                name=name or flag_key.replace("_", " ").title(),
                description=description or f"Toggle for {flag_key}",
                is_enabled=is_enabled,
                updated_at=datetime.now(timezone.utc),
            )
            await doc.insert()
        else:
            doc.is_enabled = is_enabled
            if name:
                doc.name = name
            if description:
                doc.description = description
            doc.updated_at = datetime.now(timezone.utc)
            await doc.save()

        logger.info(f"FeatureFlagManager: Set flag '{flag_key}' = {is_enabled}")
        return doc

    async def list_flags(self) -> List[Dict[str, Any]]:
        """List all feature flags."""
        try:
            docs = await FeatureFlagDocument.find_all().to_list()
            if docs:
                return [d.model_dump() if hasattr(d, 'model_dump') else dict(d) for d in docs]
        except Exception:
            pass

        return self.DEFAULT_FLAGS
