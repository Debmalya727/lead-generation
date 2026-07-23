"""
AI Execution Planner — StrategySelector selecting execution strategy based on context.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger("backend.ai.planner.strategy")

VALID_STRATEGIES = ["sequential", "parallel", "cost_optimized", "latency_optimized", "fallback_heavy"]


class StrategySelector:
    """Selects the best execution strategy given user constraints and context."""

    def select_strategy(self, context: Dict[str, Any]) -> str:
        """Select strategy string."""
        if context.get("optimize_for") == "cost":
            return "cost_optimized"
        elif context.get("optimize_for") == "latency" or context.get("realtime") is True:
            return "latency_optimized"
        elif context.get("enable_parallel") is True:
            return "parallel"
        elif context.get("high_reliability") is True:
            return "fallback_heavy"

        return "sequential"


strategy_selector = StrategySelector()
