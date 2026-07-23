"""
Master TTSGateway Orchestrator for Phase 13.3: Text-to-Speech Gateway.
Coordinates speech synthesis requests, SSML parsing, emotion prosody mapping, voice caching, fallback routing, cost attribution, and MongoDB logging.
"""
import uuid
import time
import logging
from typing import Optional, Dict, Any

from app.tts.providers.base_tts import TTSSynthesisResult
from app.tts.gateway.ssml_parser import ssml_parser
from app.tts.gateway.emotion_engine import emotion_engine
from app.tts.gateway.voice_cache import voice_cache
from app.tts.gateway.tts_fallback_engine import tts_fallback_engine
from app.tts.gateway.audio_buffer_streamer import audio_buffer_streamer
from app.tts.registry.tts_voice_registry import tts_voice_registry
from app.database.mongodb.collections.tts_gateway import (
    TTSRequestDocument,
    TTSAudioOutputDocument,
)

logger = logging.getLogger("backend.tts.gateway.master")


class TTSGateway:
    """Master Text-to-Speech (TTS) Gateway."""

    async def synthesize(
        self,
        text_prompt: str,
        provider: str = "elevenlabs",
        model: str = "eleven_multilingual_v2",
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        user_id: str = "user_default",
        org_id: Optional[str] = None,
        session_id: Optional[str] = None,
        emotion: str = "professional",
        use_cache: bool = True,
    ) -> TTSAudioOutputDocument:
        """Process TTS synthesis request through TTS Gateway pipeline."""
        req_id = f"t_req_{uuid.uuid4().hex[:12]}"
        out_id = f"t_out_{uuid.uuid4().hex[:12]}"
        start_t = time.time()

        # 1. Parse SSML tags
        has_ssml, clean_text, ssml_meta = ssml_parser.parse_ssml(text_prompt)
        text_to_speak = clean_text if has_ssml else text_prompt
        char_count = len(text_to_speak)

        # Log Request in MongoDB
        try:
            req_doc = TTSRequestDocument(
                request_id=req_id,
                user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                provider=provider,
                model=model,
                voice_id=voice_id,
                emotion=emotion,
                text_prompt=text_prompt,
                character_count=char_count,
                has_ssml=has_ssml,
            )
            await req_doc.insert()
        except Exception:
            pass

        # 2. Check Voice Cache
        cached_bytes = None
        if use_cache:
            cached_bytes = await voice_cache.get_cached_audio(text_to_speak, voice_id, emotion)

        if cached_bytes:
            # Cache Hit!
            ttfb = round((time.time() - start_t) * 1000, 2)
            tot_lat = ttfb + 5.0
            duration_sec = max(0.5, round(char_count * 0.06, 2))
            cost_usd = 0.0  # Free on cache hit

            out_doc = TTSAudioOutputDocument(
                output_id=out_id,
                request_id=req_id,
                session_id=session_id,
                audio_format="pcm_16000",
                audio_size_bytes=len(cached_bytes),
                audio_duration_seconds=duration_sec,
                ttfb_ms=ttfb,
                total_latency_ms=tot_lat,
                provider_used="cache",
                model_used=model,
                estimated_cost=cost_usd,
            )
            if session_id:
                audio_buffer_streamer.push_tts_to_voice_buffer(session_id, cached_bytes)
            try:
                await out_doc.insert()
            except Exception:
                pass
            return out_doc

        # 3. Emotion Prosody Mapping
        speed, pitch = emotion_engine.get_prosody_params(emotion)

        # 4. Synthesize Audio via Fallback Engine
        tts_res: TTSSynthesisResult = await tts_fallback_engine.execute_with_fallback(
            primary_provider=provider,
            model=model,
            voice_id=voice_id,
            text=text_to_speak,
            speed=speed,
            pitch=pitch,
            emotion=emotion,
        )

        # 5. Store in Voice Cache
        await voice_cache.set_cached_audio(text_to_speak, voice_id, emotion, tts_res.audio_bytes)

        # 6. Push to Voice Infrastructure Buffer if session_id active
        if session_id:
            audio_buffer_streamer.push_tts_to_voice_buffer(session_id, tts_res.audio_bytes)

        # 7. Compute cost attribution
        rate_per_1k = tts_voice_registry.get_cost_per_1k_chars(voice_id)
        cost_usd = round((char_count / 1000.0) * rate_per_1k, 6)

        tot_lat = round((time.time() - start_t) * 1000, 2)

        out_doc = TTSAudioOutputDocument(
            output_id=out_id,
            request_id=req_id,
            session_id=session_id,
            audio_format=tts_res.audio_format,
            audio_size_bytes=len(tts_res.audio_bytes),
            audio_duration_seconds=tts_res.audio_duration_seconds,
            ttfb_ms=tts_res.ttfb_ms,
            total_latency_ms=tot_lat,
            provider_used=tts_res.provider_used,
            model_used=tts_res.model_used,
            estimated_cost=cost_usd,
        )
        try:
            await out_doc.insert()
        except Exception:
            pass

        logger.info(f"TTSGateway: Synthesized {char_count} chars via '{tts_res.provider_used}' (TTFB={tts_res.ttfb_ms}ms, cost=${cost_usd})")
        return out_doc


tts_gateway = TTSGateway()
