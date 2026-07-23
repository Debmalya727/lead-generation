"""
AI Resource Optimizer — ProviderSelector balancing cost, latency, health, benchmarks, and availability.
"""
from typing import Dict, Any, Optional
import logging

from app.ai.optimizer.cost_optimizer import cost_optimizer
from app.ai.optimizer.latency_optimizer import latency_optimizer
from app.ai.policies.policy_engine import policy_engine

logger = logging.getLogger("backend.ai.optimizer.selector")


class ProviderSelector:
    """Multi-factor provider/model selection engine."""

    async def select_provider(
        self,
        capability: str,
        strategy: str = "sequential",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Select optimal provider and model based on strategy and context."""
        context = context or {}

        if strategy == "cost_optimized":
            res = cost_optimizer.select_cheapest(capability)
            if res:
                return res
        elif strategy == "latency_optimized":
            res = latency_optimizer.select_fastest(capability)
            if res:
                return res

        # Default: Use PolicyEngine
        policy_res = await policy_engine.resolve(capability, context)
        return {
            "provider": policy_res.provider,
            "model_id": policy_res.model,
            "policy_id": policy_res.policy_id,
            "resolved_from": policy_res.resolved_from,
        }


provider_selector = ProviderSelector()
