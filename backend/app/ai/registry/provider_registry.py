"""
Centralized Enterprise Provider Registry for Phase 12.7 Enterprise AI Platform.
Tracks registration, adapters, health, capabilities, pricing, priority, and availability
across all 9 AI providers: Gemini, Groq, Mistral, OpenRouter, OpenAI, Claude, DeepSeek, Ollama, vLLM.
"""
import logging
from typing import Dict, Type, Optional, List, Any
from app.ai.providers.base_llm import BaseLLMProvider

logger = logging.getLogger("backend.ai.registry.provider")


class ProviderRegistry:
    """Centralized enterprise provider registry."""

    _adapters: Dict[str, Type[BaseLLMProvider]] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        adapter_cls: Type[BaseLLMProvider],
        capabilities: Optional[List[str]] = None,
        supported_models: Optional[List[str]] = None,
        pricing: Optional[Dict[str, float]] = None,
        priority: int = 10,
        is_available: bool = True,
    ) -> None:
        """Register a provider adapter with enterprise metadata."""
        key = name.lower().strip()
        cls._adapters[key] = adapter_cls
        cls._metadata[key] = {
            "name": name,
            "key": key,
            "capabilities": capabilities or ["completion", "chat", "json"],
            "supported_models": supported_models or [],
            "pricing": pricing or {"input_per_1m": 0.5, "output_per_1m": 1.5},
            "priority": priority,
            "availability": is_available,
            "health_status": "HEALTHY",
        }
        logger.info(f"Registered AI Provider in Registry: '{key}' (priority={priority})")

    @classmethod
    def register_provider(cls, name: str, adapter_cls: Type[BaseLLMProvider]) -> None:
        """Legacy compatibility wrapper for register."""
        cls.register(name, adapter_cls)

    @classmethod
    def unregister(cls, name: str) -> bool:
        """Unregister a provider by name."""
        key = name.lower().strip()
        removed = False
        if key in cls._adapters:
            del cls._adapters[key]
            removed = True
        if key in cls._metadata:
            del cls._metadata[key]
            removed = True
        if removed:
            logger.info(f"Unregistered AI Provider: '{key}'")
        return removed

    @classmethod
    def get_provider_class(cls, name: str) -> Optional[Type[BaseLLMProvider]]:
        """Retrieve registered provider adapter class."""
        cls._ensure_initialized()
        return cls._adapters.get(name.lower().strip())

    @classmethod
    def list_providers(cls) -> Dict[str, Type[BaseLLMProvider]]:
        """List all registered provider classes."""
        cls._ensure_initialized()
        return cls._adapters

    @classmethod
    def health(cls, name: str) -> Dict[str, Any]:
        """Query health state of provider."""
        cls._ensure_initialized()
        key = name.lower().strip()
        meta = cls._metadata.get(key, {})
        return {
            "provider": key,
            "status": meta.get("health_status", "UNKNOWN"),
            "available": meta.get("availability", False),
        }

    @classmethod
    def capabilities(cls, name: str) -> List[str]:
        """Query supported capabilities of provider."""
        cls._ensure_initialized()
        meta = cls._metadata.get(name.lower().strip(), {})
        return meta.get("capabilities", ["completion"])

    @classmethod
    def supported_models(cls, name: str) -> List[str]:
        """Query supported model identifiers of provider."""
        cls._ensure_initialized()
        meta = cls._metadata.get(name.lower().strip(), {})
        return meta.get("supported_models", [])

    @classmethod
    def pricing(cls, name: str) -> Dict[str, float]:
        """Query pricing metrics per 1M tokens."""
        cls._ensure_initialized()
        meta = cls._metadata.get(name.lower().strip(), {})
        return meta.get("pricing", {"input_per_1m": 0.0, "output_per_1m": 0.0})

    @classmethod
    def availability(cls, name: str) -> bool:
        """Query availability status of provider."""
        cls._ensure_initialized()
        meta = cls._metadata.get(name.lower().strip(), {})
        return meta.get("availability", True)

    @classmethod
    def priority(cls, name: str) -> int:
        """Query execution priority order of provider."""
        cls._ensure_initialized()
        meta = cls._metadata.get(name.lower().strip(), {})
        return meta.get("priority", 10)

    @classmethod
    def get_all_metadata(cls) -> Dict[str, Dict[str, Any]]:
        """Get full metadata registry dictionary for all providers."""
        cls._ensure_initialized()
        return cls._metadata

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Lazy load built-in provider adapters if empty."""
        if not cls._adapters:
            import app.ai.providers.adapters
