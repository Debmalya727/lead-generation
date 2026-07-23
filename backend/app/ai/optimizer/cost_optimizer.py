"""
AI Resource Optimizer — CostOptimizer selecting lowest-cost provider/model for a capability.
"""
from typing import Dict, Any, Optional
import logging

from app.ai.registry.model_registry import ModelRegistry

logger = logging.getLogger("backend.ai.optimizer.cost")


class CostOptimizer:
    """Finds lowest-cost provider/model that satisfies a capability."""

    def select_cheapest(self, capability: str) -> Optional[Dict[str, Any]]:
        """Return cheapest model info for capability."""
        all_models = ModelRegistry.list_models()
        candidates = []

        for m_id, m_info in all_models.items():
            if m_info.get("is_embedding") and capability != "embedding":
                continue
            if not m_info.get("is_embedding") and capability == "embedding":
                continue

            cost_score = m_info.get("input_token_price", 0.0) + m_info.get("output_token_price", 0.0)
            candidates.append((cost_score, m_id, m_info))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        best = candidates[0]
        return {"model_id": best[1], "provider": best[2]["provider"], "score": best[0]}


cost_optimizer = CostOptimizer()
