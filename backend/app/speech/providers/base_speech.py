"""
BaseSpeechAdapter — Abstract Base Class for Speech Recognition Providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Optional
from pydantic import BaseModel, Field


class SpeechTranscriptionResult(BaseModel):
    """Result payload from a Speech Recognition Provider adapter."""

    transcript: str
    confidence: float = 0.95
    language: str = "en"
    language_confidence: float = 0.98
    latency_ms: float = 0.0
    provider_used: str
    model_used: str
    is_partial: bool = False
    word_timestamps: Optional[Any] = None


class BaseSpeechAdapter(ABC):
    """ABC for STT / Speech Recognition provider adapters."""

    def __init__(self, model: str = "default", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """String identifier of the provider."""
        ...

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> SpeechTranscriptionResult:
        """Transcribe PCM/audio bytes synchronously."""
        ...

    async def stream_transcribe(
        self, audio_bytes_generator: AsyncGenerator[bytes, None], language: Optional[str] = None
    ) -> AsyncGenerator[SpeechTranscriptionResult, None]:
        """Stream transcription partial chunks asynchronously."""
        async for chunk in audio_bytes_generator:
            res = await self.transcribe(chunk, language=language)
            res.is_partial = True
            yield res
