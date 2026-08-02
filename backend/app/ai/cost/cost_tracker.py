"""
CostTracker for Phase 12.7A Enterprise AI Gateway.
Computes Dollar cost per interaction based on model pricing matrix
and persists records to CostUsageDocument.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database.mongodb.collections.ai_gateway import CostUsageDocument
from app.ai.registry.model_registry import ModelRegistry

logger = logging.getLogger("backend.ai.cost_tracker")


class CostTracker:
    """Orchestrates pricing models and database dollar accumulation."""

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model_id: str) -> float:
        """Compute estimated USD cost based on token counts and model pricing."""
        info = ModelRegistry.get_model_info(model_id)
        if not info:
            return 0.0

        in_price = info.get("input_token_price", 0.0) / 1000000.0
        out_price = info.get("output_token_price", 0.0) / 1000000.0

        return (prompt_tokens * in_price) + (completion_tokens * out_price)

    async def record_cost(
        self,
        cost: float,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        plugin_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        """Accumulates USD cost metrics in CostUsageDocument across all identifier types."""
        if cost <= 0.0:
            return

        targets = []
        if user_id:
            targets.append(("user", user_id))
        if org_id:
            targets.append(("organization", org_id))
        if workflow_id:
            targets.append(("workflow", workflow_id))
        if conversation_id:
            targets.append(("conversation", conversation_id))
        if agent_id:
            targets.append(("agent", agent_id))
        if plugin_id:
            targets.append(("plugin", plugin_id))
        if provider:
            targets.append(("provider", provider))
        if model:
            targets.append(("model", model))
        if endpoint:
            targets.append(("endpoint", endpoint))

        for id_type, id_val in targets:
            try:
                doc = await CostUsageDocument.find_one(
                    CostUsageDocument.identifier_type == id_type,
                    CostUsageDocument.identifier_id == id_val
                )
                if not doc:
                    doc = CostUsageDocument(
                        identifier_type=id_type,
                        identifier_id=id_val,
                        estimated_cost=cost,
                        currency="USD",
                        updated_at=datetime.now(timezone.utc),
                    )
                    await doc.insert()
                else:
                    doc.estimated_cost += cost
                    doc.updated_at = datetime.now(timezone.utc)
                    await doc.save()
            except Exception as e:
                logger.warning(f"Failed to record cost usage for {id_type}:{id_val}: {str(e)}")


cost_tracker = CostTracker()
