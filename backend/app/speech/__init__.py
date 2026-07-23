"""Speech package for Phase 13.2 Speech Recognition Gateway."""
from app.speech.gateway.speech_gateway import speech_gateway
from app.speech.registry.speech_provider_registry import speech_provider_registry
from app.speech.registry.speech_model_registry import speech_model_registry
from app.speech.routers.speech_router import router as speech_router

__all__ = [
    "speech_gateway",
    "speech_provider_registry",
    "speech_model_registry",
    "speech_router",
]
