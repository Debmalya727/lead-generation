"""
SpeechModelRegistry — Model specifications, capabilities, and per-minute audio pricing rates ($/min).
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class SpeechModelSpec(BaseModel):
    model_id: str
    provider_id: str
    display_name: str
    cost_per_minute: float  # Price in USD per audio minute
    supports_streaming: bool = True
    supported_languages: List[str] = Field(default_factory=lambda: ["en", "es", "fr", "de", "zh", "ja"])


class SpeechModelRegistry:
    """Registry tracking speech recognition model capabilities and per-minute pricing."""

    def __init__(self):
        self._models: Dict[str, SpeechModelSpec] = {}
        self._register_defaults()

    def _register_defaults(self):
        defaults = [
            SpeechModelSpec(model_id="whisper-1", provider_id="whisper", display_name="OpenAI Whisper v1", cost_per_minute=0.006),
            SpeechModelSpec(model_id="faster-whisper-large-v3", provider_id="faster_whisper", display_name="Faster Whisper Large v3", cost_per_minute=0.001),
            SpeechModelSpec(model_id="nova-2", provider_id="deepgram", display_name="Deepgram Nova-2 (Ultra-Fast)", cost_per_minute=0.0043),
            SpeechModelSpec(model_id="google-stt-v2", provider_id="google", display_name="Google Cloud Speech v2", cost_per_minute=0.016),
            SpeechModelSpec(model_id="azure-speech-v1", provider_id="azure", display_name="Azure Cognitive Speech v1", cost_per_minute=0.016),
            SpeechModelSpec(model_id="conformer-2", provider_id="assemblyai", display_name="AssemblyAI Conformer-2", cost_per_minute=0.0065),
            SpeechModelSpec(model_id="mock-stt", provider_id="mock", display_name="Mock STT Engine", cost_per_minute=0.000),
        ]
        for m in defaults:
            self._models[m.model_id] = m

    def get_model(self, model_id: str) -> Optional[SpeechModelSpec]:
        """Fetch model spec by model ID."""
        return self._models.get(model_id) or self._models.get("whisper-1")

    def get_cost_per_minute(self, model_id: str) -> float:
        """Fetch per-minute USD cost rate."""
        spec = self.get_model(model_id)
        return spec.cost_per_minute if spec else 0.006

    def list_models(self) -> List[SpeechModelSpec]:
        """List registered speech recognition models."""
        return list(self._models.values())


speech_model_registry = SpeechModelRegistry()
