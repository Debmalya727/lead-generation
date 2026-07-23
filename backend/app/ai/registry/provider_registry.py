"""
Provider Registry for Phase 12.7A Enterprise AI Gateway.
Registers provider adapters implementing BaseLLMProvider.
"""
from typing import Dict, Type, Optional
from app.ai.providers.base_llm import BaseLLMProvider


class ProviderRegistry:
    """Registry tracking all AI provider adapters."""

    _adapters: Dict[str, Type[BaseLLMProvider]] = {}

    @classmethod
    def register_provider(cls, name: str, adapter_cls: Type[BaseLLMProvider]) -> None:
        """Register a provider adapter class."""
        cls._adapters[name.lower().strip()] = adapter_cls

    @classmethod
    def get_provider_class(cls, name: str) -> Optional[Type[BaseLLMProvider]]:
        """Retrieve registered provider class by name."""
        if not cls._adapters:
            # Trigger dynamic registration of built-in adapters
            import app.ai.providers.adapters
        return cls._adapters.get(name.lower().strip())

    @classmethod
    def list_providers(cls) -> Dict[str, Type[BaseLLMProvider]]:
        """List all registered providers."""
        if not cls._adapters:
            import app.ai.providers.adapters
        return cls._adapters
