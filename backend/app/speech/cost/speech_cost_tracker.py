"""
SpeechCostTracker — Tracks audio transcription spend based on audio duration and model rates.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.speech.registry.speech_model_registry import speech_model_registry
from app.database.mongodb.collections.speech_gateway import SpeechCostDocument

logger = logging.getLogger("backend.speech.cost.tracker")


class SpeechCostTracker:
    """Calculates and logs transcription dollar spend per audio minute."""

    async def log_cost(
        self,
        user_id: str,
        audio_duration_seconds: float,
        model: str = "whisper-1",
        provider: str = "whisper",
        org_id: Optional[str] = None,
    ) -> SpeechCostDocument:
        """Compute cost and log to MongoDB."""
        rate_per_min = speech_model_registry.get_cost_per_minute(model)
        amount_usd = round((audio_duration_seconds / 60.0) * rate_per_min, 6)
        cost_id = f"s_cost_{uuid.uuid4().hex[:12]}"

        doc = SpeechCostDocument(
            cost_id=cost_id,
            user_id=user_id,
            org_id=org_id,
            provider=provider,
            model=model,
            audio_seconds=audio_duration_seconds,
            amount_usd=amount_usd,
        )
        try:
            await doc.insert()
        except Exception:
            pass

        logger.info(f"SpeechCostTracker: Recorded ${amount_usd} spend for user '{user_id}' ({audio_duration_seconds}s audio)")
        return doc

    async def get_user_total_spend(self, user_id: str) -> float:
        """Calculate total spend for user."""
        docs = await SpeechCostDocument.find(SpeechCostDocument.user_id == user_id).to_list()
        return round(sum(d.amount_usd for d in docs), 4)


speech_cost_tracker = SpeechCostTracker()
