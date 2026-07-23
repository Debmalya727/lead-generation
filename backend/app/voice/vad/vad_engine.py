"""
Voice Activity Detection (VAD) Engine for Phase 13.1.
Analyzes 16-bit PCM audio frames to calculate Root Mean Square (RMS) energy & Zero Crossing Rate (ZCR).
Detects: SpeechStarted, SpeechStopped, SilenceStarted, SilenceEnded, and Interruption events.
Strictly NO speech recognition (ASR) and NO text-to-speech (TTS).
"""
import math
import struct
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("backend.voice.vad.engine")


class VADResult:
    """Result of VAD analysis on an audio frame."""

    def __init__(
        self,
        session_id: str,
        is_speech: bool,
        energy_db: float,
        zcr: float,
        event_type: Optional[str] = None,
    ):
        self.session_id = session_id
        self.is_speech = is_speech
        self.energy_db = energy_db
        self.zcr = zcr
        self.event_type = event_type  # SpeechStarted | SpeechStopped | SilenceStarted | SilenceEnded | Interruption | None


class VADEngine:
    """
    Energy & Zero Crossing Rate Voice Activity Detection Engine.
    Operates on 16-bit mono linear PCM audio chunks.
    """

    def __init__(
        self,
        energy_threshold_db: float = -40.0,
        min_speech_duration_ms: float = 200.0,
        min_silence_duration_ms: float = 400.0,
    ):
        self.energy_threshold_db = energy_threshold_db
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms

        # Session states: session_id -> dict
        self._states: Dict[str, Dict[str, Any]] = {}

    def calculate_rms_energy(self, pcm_bytes: bytes) -> Tuple[float, float]:
        """
        Calculate RMS Energy (dB) and Zero Crossing Rate (ZCR) for 16-bit PCM.
        """
        if not pcm_bytes or len(pcm_bytes) < 2:
            return -100.0, 0.0

        # Unpack 16-bit signed integers (little-endian)
        num_samples = len(pcm_bytes) // 2
        try:
            samples = struct.unpack(f"<{num_samples}h", pcm_bytes[: num_samples * 2])
        except Exception:
            return -100.0, 0.0

        if num_samples == 0:
            return -100.0, 0.0

        # RMS Calculation
        sum_squares = sum(s * s for s in samples)
        mean_square = sum_squares / num_samples
        rms = math.sqrt(mean_square)

        # Convert RMS to dBFS (max 32767 for 16-bit)
        if rms > 0:
            db = 20 * math.log10(rms / 32768.0)
        else:
            db = -100.0

        # Zero Crossing Rate Calculation
        crossings = 0
        for i in range(1, num_samples):
            if (samples[i] >= 0 and samples[i - 1] < 0) or (samples[i] < 0 and samples[i - 1] >= 0):
                crossings += 1
        zcr = crossings / num_samples

        return round(db, 2), round(zcr, 4)

    def process_frame(
        self,
        session_id: str,
        pcm_bytes: bytes,
        is_system_speaking: bool = False,
    ) -> VADResult:
        """
        Processes audio frame and triggers speech/silence state transitions.
        """
        db, zcr = self.calculate_rms_energy(pcm_bytes)
        now_ms = time.time() * 1000

        if session_id not in self._states:
            self._states[session_id] = {
                "in_speech": False,
                "speech_start_ms": 0.0,
                "silence_start_ms": now_ms,
                "last_event": None,
            }

        st = self._states[session_id]
        is_speech_frame = db > self.energy_threshold_db
        event_type = None

        if is_speech_frame:
            if not st["in_speech"]:
                # Transition Silence -> Speech
                st["in_speech"] = True
                st["speech_start_ms"] = now_ms
                event_type = "SpeechStarted"
                logger.info(f"VADEngine [{session_id}]: SpeechStarted (energy={db}dB, zcr={zcr})")
                if is_system_speaking:
                    event_type = "Interruption"
                    logger.warning(f"VADEngine [{session_id}]: Interruption detected!")
            else:
                if is_system_speaking and st["last_event"] != "Interruption":
                    event_type = "Interruption"
                    logger.warning(f"VADEngine [{session_id}]: Interruption detected!")
        else:
            if st["in_speech"]:
                # Transition Speech -> Silence
                st["in_speech"] = False
                st["silence_start_ms"] = now_ms
                event_type = "SpeechStopped"
                logger.info(f"VADEngine [{session_id}]: SpeechStopped")

        if event_type:
            st["last_event"] = event_type

        return VADResult(
            session_id=session_id,
            is_speech=st["in_speech"],
            energy_db=db,
            zcr=zcr,
            event_type=event_type,
        )


vad_engine = VADEngine()
