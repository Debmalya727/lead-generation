"""
BaseTTSAdapter — Abstract Base Class for Text-to-Speech Providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Optional
from pydantic import BaseModel, Field


class TTSSynthesisResult(BaseModel):
    """Result payload from a Text-to-Speech Provider adapter."""

    audio_bytes: bytes
    sample_rate: int = 16000
    audio_format: str = "pcm_16000"
    audio_duration_seconds: float = 0.0
    ttfb_ms: float = 0.0
    total_latency_ms: float = 0.0
    provider_used: str
    model_used: str
    voice_used: str
    is_cached: bool = False


class BaseTTSAdapter(ABC):
    """ABC for TTS / Text-to-Speech provider adapters."""

    def __init__(self, model: str = "default", voice_id: str = "default", api_key: Optional[str] = None):
        self.model = model
        self.voice_id = voice_id
        self.api_key = api_key

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """String identifier of the provider."""
        ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
        emotion: Optional[str] = None,
    ) -> TTSSynthesisResult:
        """Synthesize text into raw PCM/audio bytes."""
        ...

    async def stream_synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        chunk_size: int = 3200,
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesized audio chunks asynchronously."""
        full_res = await self.synthesize(text, voice_id=voice_id)
        raw_bytes = full_res.audio_bytes
        for i in range(0, len(raw_bytes), chunk_size):
            yield raw_bytes[i : i + chunk_size]
