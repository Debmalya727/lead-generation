"""Gateway package for Phase 13.3 TTS Gateway."""
from app.tts.gateway.tts_gateway import tts_gateway, TTSGateway
from app.tts.gateway.ssml_parser import ssml_parser
from app.tts.gateway.emotion_engine import emotion_engine
from app.tts.gateway.voice_cache import voice_cache
from app.tts.gateway.tts_fallback_engine import tts_fallback_engine
from app.tts.gateway.audio_buffer_streamer import audio_buffer_streamer

__all__ = [
    "tts_gateway",
    "TTSGateway",
    "ssml_parser",
    "emotion_engine",
    "voice_cache",
    "tts_fallback_engine",
    "audio_buffer_streamer",
]
