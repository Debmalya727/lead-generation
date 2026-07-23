"""
SpeechFallbackEngine — Retries transcription calls with backoff and provider failover.
Fallback hierarchy: Requested Provider → Whisper → Deepgram → FasterWhisper → Mock
"""
import asyncio
import logging
from typing import Optional, List, Tuple

from app.speech.providers.base_speech import BaseSpeechAdapter, SpeechTranscriptionResult
from app.speech.registry.speech_provider_registry import speech_provider_registry

logger = logging.getLogger("backend.speech.gateway.fallback")


class SpeechFallbackEngine:
    """Manages STT provider failovers when API keys are missing or rate limits occur."""

    def __init__(self, default_policy: Optional[List[str]] = None):
        self.fallback_chain = default_policy or ["whisper", "deepgram", "faster_whisper", "mock"]

    async def execute_with_fallback(
        self,
        primary_provider: str,
        model: str,
        audio_bytes: bytes,
        language: Optional[str] = None,
        max_retries_per_provider: int = 2,
    ) -> SpeechTranscriptionResult:
        """Attempt primary provider; on failure, cascade down fallback chain."""
        chain = [primary_provider] + [p for p in self.fallback_chain if p != primary_provider]

        last_error = None
        for provider_id in chain:
            adapter = speech_provider_registry.get_adapter(provider_id, model=model)
            for attempt in range(1, max_retries_per_provider + 1):
                try:
                    res = await adapter.transcribe(audio_bytes, language=language)
                    if provider_id != primary_provider:
                        logger.warning(f"SpeechFallbackEngine: Primary '{primary_provider}' failed. Used fallback '{provider_id}'")
                    return res
                except Exception as e:
                    last_error = e
                    logger.warning(f"SpeechFallbackEngine: Attempt {attempt} failed for '{provider_id}': {e}")
                    await asyncio.sleep(0.1 * attempt)

        logger.error("SpeechFallbackEngine: All providers failed! Routing to Mock STT.")
        mock_adapter = speech_provider_registry.get_adapter("mock")
        return await mock_adapter.transcribe(audio_bytes, language=language)


speech_fallback_engine = SpeechFallbackEngine()
