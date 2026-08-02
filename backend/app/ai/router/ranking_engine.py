"""
Dynamic Provider Ranking Engine for Phase 12.7 Enterprise AI Platform.
Calculates real-time provider scores using health, latency, cost, quality, and availability statistics.
Does NOT rely on hardcoded provider ordering.
"""
import logging
from typing import Dict, List, Any, Optional
from app.ai.registry.provider_registry import ProviderRegistry
from app.ai.registry.model_registry import ModelRegistry
from app.ai.gateway.health_manager import provider_health_manager

logger = logging.getLogger("backend.ai.router.ranking")


class DynamicProviderRankingEngine:
    """Engine dynamically ranking AI providers based on live telemetry."""

    @classmethod
    def rank_providers(
        cls,
        task_category: str = "completion",
        weight_latency: float = 0.3,
        weight_cost: float = 0.3,
        weight_quality: float = 0.3,
        weight_health: float = 0.1,
    ) -> List[Dict[str, Any]]:
        """
        Dynamically rank all active providers based on weighted score:
        Score = (health * w_health) + ((1 - norm_lat) * w_lat) + ((1 - norm_cost) * w_cost) + (qual * w_qual)
        """
        all_metadata = ProviderRegistry.get_all_metadata()
        health_stats = provider_health_manager.get_all_stats()

        ranked = []
        for provider_key, meta in all_metadata.items():
            if not meta.get("availability", True):
                continue

            stats = health_stats.get(provider_key, {})
            status = stats.get("status", "HEALTHY")
            if status == "UNAVAILABLE":
                continue

            health_score = 1.0 if status == "HEALTHY" else 0.5
            avg_lat = stats.get("avg_latency_ms", 500.0)
            latency_score = max(0.0, 1.0 - (avg_lat / 3000.0))  # Normalized over 3s max

            pricing = meta.get("pricing", {"input_per_1m": 1.0, "output_per_1m": 2.0})
            avg_cost = (pricing.get("input_per_1m", 1.0) + pricing.get("output_per_1m", 2.0)) / 2.0
            cost_score = max(0.0, 1.0 - (avg_cost / 15.0))  # Normalized over $15 max

            models = ModelRegistry.get_models_by_provider(provider_key)
            best_quality = max([m.get("quality_score", 7.0) for m in models], default=7.0) / 10.0

            total_score = (
                (health_score * weight_health) +
                (latency_score * weight_latency) +
                (cost_score * weight_cost) +
                (best_quality * weight_quality)
            )

            ranked.append({
                "provider": provider_key,
                "name": meta.get("name"),
                "score": round(total_score, 4),
                "health_status": status,
                "avg_latency_ms": round(avg_lat, 1),
                "avg_cost_per_1m": round(avg_cost, 3),
                "quality_score": round(best_quality * 10, 1),
                "priority": meta.get("priority", 10),
            })

        # Sort descending by calculated dynamic score, then priority
        ranked.sort(key=lambda x: (x["score"], -x["priority"]), reverse=True)
        return ranked


ranking_engine = DynamicProviderRankingEngine()
