"""
Central Provider Registry for Enterprise Lead Discovery.
Allows registering, discovering, and inspecting discovery providers dynamically.
Adding new lead discovery providers requires zero changes to core discovery logic.
"""
import logging
from typing import Dict, List, Type, Optional, Any
from app.modules.discovery.providers.base_provider import BaseDiscoveryProvider

logger = logging.getLogger("backend.discovery.provider_registry")


class ProviderRegistry:
    """Dynamic Singleton Registry for Lead Discovery Providers."""

    _instance: Optional["ProviderRegistry"] = None

    def __init__(self):
        self._providers: Dict[str, BaseDiscoveryProvider] = {}
        self._provider_classes: Dict[str, Type[BaseDiscoveryProvider]] = {}

    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, provider_class: Type[Any]) -> None:
        """Register a provider class."""
        instance = provider_class()
        name = instance.provider_name.lower().strip()
        self._providers[name] = instance
        self._provider_classes[name] = provider_class
        logger.info(f"[ProviderRegistry] Registered lead provider '{name}' ({provider_class.__name__})")

    def get_provider(self, name: str) -> Optional[BaseDiscoveryProvider]:
        """Get provider instance by registered name key."""
        clean_name = name.lower().strip()
        return self._providers.get(clean_name)

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all registered providers with capabilities and health status."""
        results = []
        for name, provider in self._providers.items():
            health_info = provider.health()
            results.append({
                "name": name,
                "class_name": provider.__class__.__name__,
                "health": health_info["status"],
                "circuit_state": health_info["circuit_state"],
                "requests_per_minute": health_info["requests_per_minute_quota"],
                "capabilities": health_info["capabilities"],
            })
        return results

    def get_health_summary(self) -> Dict[str, Any]:
        """Aggregate health status across all registered providers."""
        summary = {
            "total_providers": len(self._providers),
            "healthy_count": 0,
            "degraded_count": 0,
            "down_count": 0,
            "providers": {},
        }
        for name, provider in self._providers.items():
            health_info = provider.health()
            status = health_info["status"]
            if status == "healthy":
                summary["healthy_count"] += 1
            elif status == "degraded":
                summary["degraded_count"] += 1
            else:
                summary["down_count"] += 1
            summary["providers"][name] = health_info
        return summary


provider_registry = ProviderRegistry.get_instance()

# Auto-register standard discovery providers
def register_default_discovery_providers():
    try:
        from app.modules.discovery.providers.google_maps import GoogleMapsProvider
        from app.modules.discovery.providers.justdial import JustDialProvider
        from app.modules.discovery.providers.indiamart import IndiaMARTProvider
        from app.modules.discovery.providers.tradeindia import TradeIndiaProvider

        provider_registry.register(GoogleMapsProvider)
        provider_registry.register(JustDialProvider)
        provider_registry.register(IndiaMARTProvider)
        provider_registry.register(TradeIndiaProvider)
    except Exception as e:
        logger.warning(f"Default provider auto-registration notice: {e}")

register_default_discovery_providers()

