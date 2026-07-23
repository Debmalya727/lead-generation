"""
AI Resource Optimizer — LatencyOptimizer selecting fastest provider/model for a capability.
"""
from typing import Dict, Any, Optional
import logging

from app.ai.registry.model_registry import ModelRegistry

logger = logging.getLogger("backend.ai.optimizer.latency")


class LatencyOptimizer:
    """Finds fastest provider/model based on context window and performance heuristics."""

    def select_fastest(self, capability: str) -> Optional[Dict[str, Any]]:
        """Return fastest model info for capability."""
        # Preference mapping for fast execution
        fast_defaults = {
            "chat": ("gemini", "gemini-1.5-flash"),
            "reasoning": ("claude", "claude-3-5-sonnet"),
            "vision": ("openai", "gpt-4o-mini"),
            "embedding": ("openai", "text-embedding-3-small"),
            "summarization": ("gemini", "gemini-1.5-flash"),
            "tool_calling": ("openai", "gpt-4o-mini"),
        }

        if capability in fast_defaults:
            provider, model_id = fast_defaults[capability]
            return {"provider": provider, "model_id": model_id, "score": 100.0}

        return {"provider": "gemini", "model_id": "gemini-1.5-flash", "score": 50.0}


latency_optimizer = LatencyOptimizer()
