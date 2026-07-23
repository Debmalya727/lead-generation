"""
TTSFallbackEngine — Retries TTS provider calls with exponential backoff and provider failover.
Fallback hierarchy: Requested Provider → ElevenLabs → OpenAI → Azure → Piper → Mock
"""
import asyncio
import logging
from typing import Optional, List

from app.tts.providers.base_tts import BaseTTSAdapter, TTSSynthesisResult
from app.tts.registry.tts_provider_registry import tts_provider_registry

logger = logging.getLogger("backend.tts.gateway.fallback")


class TTSFallbackEngine:
    """Manages TTS provider failovers when API keys are missing or provider errors occur."""

    def __init__(self, default_policy: Optional[List[str]] = None):
        self.fallback_chain = default_policy or ["elevenlabs", "openai", "azure", "piper", "mock"]

    async def execute_with_fallback(
        self,
        primary_provider: str,
        model: str,
        voice_id: str,
        text: str,
        speed: float = 1.0,
        pitch: float = 1.0,
        emotion: Optional[str] = None,
        max_retries_per_provider: int = 2,
    ) -> TTSSynthesisResult:
        """Attempt primary provider; on failure, cascade down fallback chain."""
        chain = [primary_provider] + [p for p in self.fallback_chain if p != primary_provider]

        last_error = None
        for provider_id in chain:
            adapter = tts_provider_registry.get_adapter(provider_id, model=model, voice_id=voice_id)
            for attempt in range(1, max_retries_per_provider + 1):
                try:
                    res = await adapter.synthesize(text, voice_id=voice_id, speed=speed, pitch=pitch, emotion=emotion)
                    if provider_id != primary_provider:
                        logger.warning(f"TTSFallbackEngine: Primary '{primary_provider}' failed. Used fallback '{provider_id}'")
                    return res
                except Exception as e:
                    last_error = e
                    logger.warning(f"TTSFallbackEngine: Attempt {attempt} failed for '{provider_id}': {e}")
                    await asyncio.sleep(0.1 * attempt)

        logger.error("TTSFallbackEngine: All providers failed! Routing to Mock TTS.")
        mock_adapter = tts_provider_registry.get_adapter("mock")
        return await mock_adapter.synthesize(text, voice_id=voice_id)


tts_fallback_engine = TTSFallbackEngine()
