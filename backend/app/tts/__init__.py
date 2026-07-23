"""TTS package for Phase 13.3 Text-to-Speech Gateway."""
from app.tts.gateway.tts_gateway import tts_gateway
from app.tts.registry.tts_provider_registry import tts_provider_registry
from app.tts.registry.tts_voice_registry import tts_voice_registry
from app.tts.routers.tts_router import router as tts_router

__all__ = [
    "tts_gateway",
    "tts_provider_registry",
    "tts_voice_registry",
    "tts_router",
]
