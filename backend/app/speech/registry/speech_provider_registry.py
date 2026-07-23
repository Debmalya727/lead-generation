"""
SpeechProviderRegistry — Registers speech provider adapters and tracks health.
"""
from typing import Dict, Any, Type, Optional, List
import logging

from app.speech.providers.base_speech import BaseSpeechAdapter
from app.speech.providers.adapters import (
    WhisperAdapter,
    FasterWhisperAdapter,
    DeepgramAdapter,
    GoogleSpeechAdapter,
    AzureSpeechAdapter,
    AssemblyAIAdapter,
    MockSpeechAdapter,
)

logger = logging.getLogger("backend.speech.registry.provider")


class SpeechProviderRegistry:
    """Registry managing available speech-to-text provider adapters."""

    def __init__(self):
        self._adapters: Dict[str, Type[BaseSpeechAdapter]] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("whisper", WhisperAdapter)
        self.register("faster_whisper", FasterWhisperAdapter)
        self.register("deepgram", DeepgramAdapter)
        self.register("google", GoogleSpeechAdapter)
        self.register("azure", AzureSpeechAdapter)
        self.register("assemblyai", AssemblyAIAdapter)
        self.register("mock", MockSpeechAdapter)

    def register(self, provider_id: str, adapter_cls: Type[BaseSpeechAdapter]):
        """Register a new speech provider adapter."""
        self._adapters[provider_id] = adapter_cls
        logger.info(f"SpeechProviderRegistry: Registered provider '{provider_id}'")

    def get_adapter(self, provider_id: str, model: str = "default", api_key: Optional[str] = None) -> BaseSpeechAdapter:
        """Instantiate adapter by provider ID."""
        cls = self._adapters.get(provider_id, MockSpeechAdapter)
        return cls(model=model, api_key=api_key)

    def list_providers(self) -> List[str]:
        """List registered provider IDs."""
        return list(self._adapters.keys())


speech_provider_registry = SpeechProviderRegistry()
