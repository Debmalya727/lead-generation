"""
Intelligent Capability Router for Phase 12.7 Enterprise AI Platform.
Automatically selects the optimal provider and model based on task capabilities,
budget constraints, latency bounds, minimum quality scores, and real-time health availability.
"""
import logging
from typing import Dict, Any, List, Optional
from app.ai.registry.model_registry import ModelRegistry
from app.ai.router.ranking_engine import ranking_engine
from app.ai.gateway.health_manager import provider_health_manager

logger = logging.getLogger("backend.ai.router.capability")


class IntelligentCapabilityRouter:
    """Enterprise router matching task requirements to optimal provider & model."""

    @classmethod
    def select_optimal_provider_and_model(
        cls,
        task: str = "general",
        required_capability: Optional[str] = None,
        max_cost_per_1m: Optional[float] = None,
        max_latency_ms: Optional[float] = None,
        min_quality_score: Optional[float] = None,
        requires_vision: bool = False,
        requires_tools: bool = False,
    ) -> Dict[str, Any]:
        """Select best matching provider and model meeting constraints."""
        ranked_providers = ranking_engine.rank_providers()
        all_models = ModelRegistry.list_models()

        best_match = None
        highest_score = -1.0

        for prov in ranked_providers:
            provider_key = prov["provider"]
            health = provider_health_manager.get_health(provider_key)
            if health.get("status") == "UNAVAILABLE":
                continue

            models = ModelRegistry.get_models_by_provider(provider_key)
            for m in models:
                if m.get("is_embedding"):
                    continue

                if not m.get("availability", True):
                    continue

                # Capability checks
                caps = m.get("capabilities", [])
                if required_capability and required_capability not in caps and task not in caps:
                    continue

                if requires_vision and not m.get("vision_support", False):
                    continue

                if requires_tools and not m.get("tool_calling", False):
                    continue

                # Pricing check
                input_price = m.get("input_token_price", 1.0)
                if max_cost_per_1m and input_price > max_cost_per_1m:
                    continue

                # Latency check
                avg_lat = health.get("avg_latency_ms", 300.0)
                if max_latency_ms and avg_lat > max_latency_ms:
                    continue

                # Quality check
                qual = m.get("quality_score", 7.0)
                if min_quality_score and qual < min_quality_score:
                    continue

                # Match score
                candidate_score = (prov["score"] * 0.5) + (qual / 10.0 * 0.5)
                if candidate_score > highest_score:
                    highest_score = candidate_score
                    best_match = {
                        "provider": provider_key,
                        "model": m["model_id"],
                        "model_name": m.get("name"),
                        "match_score": round(candidate_score, 4),
                        "quality_score": qual,
                        "input_token_price": input_price,
                        "output_token_price": m.get("output_token_price", 0.0),
                        "context_window": m.get("context_window", 128000),
                        "provider_status": health.get("status"),
                    }

        if not best_match:
            logger.warning(f"[CapabilityRouter] No exact match for task '{task}', falling back to default provider.")
            best_match = {
                "provider": "groq" if provider_health_manager.get_health("groq").get("status") == "HEALTHY" else "mistral",
                "model": "llama-3.3-70b-versatile",
                "model_name": "Llama 3.3 70B Versatile",
                "match_score": 0.8,
                "quality_score": 9.0,
                "input_token_price": 0.59,
                "output_token_price": 0.79,
                "context_window": 128000,
                "provider_status": "HEALTHY",
            }

        logger.info(f"[CapabilityRouter] Selected '{best_match['provider']}/{best_match['model']}' for task '{task}' (score={best_match['match_score']})")
        return best_match


capability_router = IntelligentCapabilityRouter()
