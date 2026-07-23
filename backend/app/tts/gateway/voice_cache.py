"""
VoiceCache — In-memory & MongoDB SHA-256 deduplication cache for synthesized audio bytes.
"""
import hashlib
import base64
import logging
from typing import Optional

from app.database.mongodb.collections.tts_gateway import TTSCacheDocument

logger = logging.getLogger("backend.tts.gateway.cache")


class VoiceCache:
    """Caches synthesized TTS audio bytes to eliminate redundant API calls."""

    def __init__(self):
        self._memory_cache: dict = {}

    def _generate_cache_key(self, text: str, voice_id: str, emotion: str) -> str:
        raw = f"{text}:{voice_id}:{emotion}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    async def get_cached_audio(self, text: str, voice_id: str, emotion: str = "professional") -> Optional[bytes]:
        """Fetch cached audio bytes if available."""
        key = self._generate_cache_key(text, voice_id, emotion)
        if key in self._memory_cache:
            logger.info("VoiceCache: Memory cache HIT!")
            return self._memory_cache[key]

        try:
            doc = await TTSCacheDocument.find_one(TTSCacheDocument.cache_key == key)
            if doc:
                doc.hit_count += 1
                await doc.save()
                audio_bytes = base64.b64decode(doc.audio_bytes_base64)
                self._memory_cache[key] = audio_bytes
                logger.info("VoiceCache: MongoDB cache HIT!")
                return audio_bytes
        except Exception:
            pass

        return None

    async def set_cached_audio(self, text: str, voice_id: str, emotion: str, audio_bytes: bytes) -> None:
        """Store synthesized audio bytes in memory and MongoDB cache."""
        key = self._generate_cache_key(text, voice_id, emotion)
        self._memory_cache[key] = audio_bytes

        try:
            b64_str = base64.b64encode(audio_bytes).decode("utf-8")
            doc = TTSCacheDocument(
                cache_key=key,
                text_prompt=text,
                voice_id=voice_id,
                audio_bytes_base64=b64_str,
                hit_count=1,
            )
            await doc.insert()
            logger.info(f"VoiceCache: Cached {len(audio_bytes)} audio bytes for key '{key[:8]}'")
        except Exception:
            pass


voice_cache = VoiceCache()
