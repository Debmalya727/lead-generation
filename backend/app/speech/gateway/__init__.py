"""Gateway package for Phase 13.2 Speech Gateway."""
from app.speech.gateway.speech_gateway import speech_gateway, SpeechGateway
from app.speech.gateway.fallback_engine import speech_fallback_engine
from app.speech.gateway.confidence_engine import confidence_engine
from app.speech.gateway.language_detector import language_detector
from app.speech.gateway.streaming import streaming_transcript_engine

__all__ = [
    "speech_gateway",
    "SpeechGateway",
    "speech_fallback_engine",
    "confidence_engine",
    "language_detector",
    "streaming_transcript_engine",
]
