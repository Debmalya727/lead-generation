"""
TTSProviderRegistry — Registers TTS provider adapters and manages availability.
"""
from typing import Dict, Any, Type, Optional, List
import logging

from app.tts.providers.base_tts import BaseTTSAdapter
from app.tts.providers.adapters import (
    ElevenLabsAdapter,
    OpenAITTSAdapter,
    AzureTTSAdapter,
    GoogleTTSAdapter,
    AmazonPollyAdapter,
    PiperTTSAdapter,
    MockTTSAdapter,
)

logger = logging.getLogger("backend.tts.registry.provider")


class TTSProviderRegistry:
    """Registry managing available Text-to-Speech provider adapters."""

    def __init__(self):
        self._adapters: Dict[str, Type[BaseTTSAdapter]] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("elevenlabs", ElevenLabsAdapter)
        self.register("openai", OpenAITTSAdapter)
        self.register("azure", AzureTTSAdapter)
        self.register("google", GoogleTTSAdapter)
        self.register("polly", AmazonPollyAdapter)
        self.register("piper", PiperTTSAdapter)
        self.register("mock", MockTTSAdapter)

    def register(self, provider_id: str, adapter_cls: Type[BaseTTSAdapter]):
        """Register a new TTS provider adapter."""
        self._adapters[provider_id] = adapter_cls
        logger.info(f"TTSProviderRegistry: Registered provider '{provider_id}'")

    def get_adapter(self, provider_id: str, model: str = "default", voice_id: str = "default", api_key: Optional[str] = None) -> BaseTTSAdapter:
        """Instantiate adapter by provider ID."""
        cls = self._adapters.get(provider_id, MockTTSAdapter)
        return cls(model=model, voice_id=voice_id, api_key=api_key)

    def list_providers(self) -> List[str]:
        """List registered provider IDs."""
        return list(self._adapters.keys())


tts_provider_registry = TTSProviderRegistry()
