"""
StreamingTranscriptEngine — Generates partial transcript stream chunks for real-time STT.
"""
from typing import AsyncGenerator, Dict, Any, Optional
import asyncio
import logging

from app.speech.providers.base_speech import SpeechTranscriptionResult
from app.speech.gateway.fallback_engine import speech_fallback_engine

logger = logging.getLogger("backend.speech.gateway.streaming")


class StreamingTranscriptEngine:
    """Streams partial and final transcription chunks over WebSockets."""

    async def stream_chunks(
        self,
        provider: str,
        model: str,
        audio_stream: AsyncGenerator[bytes, None],
        language: Optional[str] = None,
    ) -> AsyncGenerator[SpeechTranscriptionResult, None]:
        """Process incoming audio chunks and yield partial/final transcription results."""
        accumulated_text = []
        chunk_index = 0

        async for audio_chunk in audio_stream:
            chunk_index += 1
            res = await speech_fallback_engine.execute_with_fallback(
                primary_provider=provider,
                model=model,
                audio_bytes=audio_chunk,
                language=language,
            )
            res.is_partial = True
            accumulated_text.append(res.transcript)
            res.transcript = " ".join(accumulated_text)
            yield res


streaming_transcript_engine = StreamingTranscriptEngine()
