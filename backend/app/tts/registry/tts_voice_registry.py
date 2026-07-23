"""
TTSVoiceRegistry — Voice profiles, synthetic/cloned voices, emotion presets, SSML support, and character pricing ($/1k chars).
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class VoiceProfileSpec(BaseModel):
    voice_id: str
    voice_name: str
    provider_id: str
    gender: str = "female"
    language: str = "en-US"
    is_cloned: bool = False
    supported_emotions: List[str] = Field(default_factory=lambda: ["cheerful", "empathetic", "professional", "urgent"])
    cost_per_1k_chars: float = 0.015


class TTSVoiceRegistry:
    """Registry tracking voice profiles, emotion capabilities, and character pricing."""

    def __init__(self):
        self._voices: Dict[str, VoiceProfileSpec] = {}
        self._register_defaults()

    def _register_defaults(self):
        defaults = [
            VoiceProfileSpec(voice_id="21m00Tcm4TlvDq8ikWAM", voice_name="Rachel (ElevenLabs Multilingual)", provider_id="elevenlabs", cost_per_1k_chars=0.015),
            VoiceProfileSpec(voice_id="AZnzlk1XvdvUeBnXmlld", voice_name="Domi (ElevenLabs Expressive)", provider_id="elevenlabs", cost_per_1k_chars=0.015),
            VoiceProfileSpec(voice_id="alloy", voice_name="Alloy (OpenAI TTS)", provider_id="openai", cost_per_1k_chars=0.015),
            VoiceProfileSpec(voice_id="echo", voice_name="Echo (OpenAI TTS Male)", provider_id="openai", cost_per_1k_chars=0.015),
            VoiceProfileSpec(voice_id="en-US-JennyNeural", voice_name="Jenny (Azure Neural)", provider_id="azure", cost_per_1k_chars=0.016),
            VoiceProfileSpec(voice_id="en-US-Neural2-F", voice_name="Neural2-F (Google Cloud)", provider_id="google", cost_per_1k_chars=0.016),
            VoiceProfileSpec(voice_id="Joanna", voice_name="Joanna (Amazon Polly Neural)", provider_id="polly", cost_per_1k_chars=0.004),
            VoiceProfileSpec(voice_id="en_US-amy-medium", voice_name="Amy (Piper Local ONNX)", provider_id="piper", cost_per_1k_chars=0.000),
            VoiceProfileSpec(voice_id="mock-voice", voice_name="Mock Voice Engine", provider_id="mock", cost_per_1k_chars=0.000),
        ]
        for v in defaults:
            self._voices[v.voice_id] = v

    def get_voice(self, voice_id: str) -> Optional[VoiceProfileSpec]:
        """Fetch voice profile spec."""
        return self._voices.get(voice_id) or self._voices.get("21m00Tcm4TlvDq8ikWAM")

    def get_cost_per_1k_chars(self, voice_id: str) -> float:
        """Fetch USD cost per 1k characters."""
        spec = self.get_voice(voice_id)
        return spec.cost_per_1k_chars if spec else 0.015

    def list_voices(self, provider_id: Optional[str] = None) -> List[VoiceProfileSpec]:
        """List voice profiles, optionally filtered by provider."""
        if provider_id:
            return [v for v in self._voices.values() if v.provider_id == provider_id]
        return list(self._voices.values())


tts_voice_registry = TTSVoiceRegistry()
