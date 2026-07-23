"""
TTSCostTracker — Tracks text synthesis spend based on character counts and voice rates.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.tts.registry.tts_voice_registry import tts_voice_registry
from app.database.mongodb.collections.tts_gateway import TTSCostDocument

logger = logging.getLogger("backend.tts.cost.tracker")


class TTSCostTracker:
    """Calculates and logs TTS dollar spend per 1,000 characters."""

    async def log_cost(
        self,
        user_id: str,
        character_count: int,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        model: str = "eleven_multilingual_v2",
        provider: str = "elevenlabs",
        org_id: Optional[str] = None,
    ) -> TTSCostDocument:
        """Compute cost and log to MongoDB."""
        rate_per_1k = tts_voice_registry.get_cost_per_1k_chars(voice_id)
        amount_usd = round((character_count / 1000.0) * rate_per_1k, 6)
        cost_id = f"t_cost_{uuid.uuid4().hex[:12]}"

        doc = TTSCostDocument(
            cost_id=cost_id,
            user_id=user_id,
            org_id=org_id,
            provider=provider,
            model=model,
            character_count=character_count,
            amount_usd=amount_usd,
        )
        try:
            await doc.insert()
        except Exception:
            pass

        logger.info(f"TTSCostTracker: Recorded ${amount_usd} spend for user '{user_id}' ({character_count} chars)")
        return doc

    async def get_user_total_spend(self, user_id: str) -> float:
        """Calculate total spend for user."""
        docs = await TTSCostDocument.find(TTSCostDocument.user_id == user_id).to_list()
        return round(sum(d.amount_usd for d in docs), 4)


tts_cost_tracker = TTSCostTracker()
