"""
FallbackEngine for Phase 12.7A Enterprise AI Gateway.
Executes retries, switches models, or switches providers based on policies.
"""
import asyncio
import logging
from typing import List, Dict, Any, Callable, Awaitable

logger = logging.getLogger("backend.ai.fallback")


class FallbackEngine:
    """Orchestrates model switching and provider failover policies."""

    FALLBACK_POLICY: List[Dict[str, Any]] = [
        {"provider": "gemini", "model": "gemini-1.5-flash"},
        {"provider": "openai", "model": "gpt-4o-mini"},
        {"provider": "openrouter", "model": "openrouter-default"},
    ]

    async def execute_with_fallback(
        self,
        primary_provider: str,
        primary_model: str,
        api_call_func: Callable[[str, str], Awaitable[str]],
        prompt: str,
        system_prompt: str = "",
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Executes API call. On failure, applies retries with backoff.
        If retries exhaust, falls back to alternative model/provider.
        """
        current_provider = primary_provider
        current_model = primary_model
        
        attempted_runs = []
        fallback_index = 0
        
        while True:
            logger.info(f"FallbackEngine: Routing request to '{current_provider}' using '{current_model}'")
            retry_count = 0
            
            for retry in range(1, max_retries + 1):
                try:
                    # Execute adapter completion
                    result_text = await api_call_func(current_provider, current_model)
                    
                    return {
                        "success": True,
                        "response_text": result_text,
                        "provider_used": current_provider,
                        "model_used": current_model,
                        "retry_count": retry_count,
                        "fallback_count": fallback_index,
                    }
                except Exception as e:
                    retry_count = retry
                    logger.warning(
                        f"FallbackEngine: Attempt {retry}/{max_retries} failed for "
                        f"'{current_provider}/{current_model}': {str(e)}"
                    )
                    if retry < max_retries:
                        await asyncio.sleep(2 ** retry)  # Exponential backoff
            
            # Retries exhausted. Move to fallback policy
            attempted_runs.append(f"{current_provider}:{current_model}")
            
            # Find next policy candidate that hasn't been tried
            next_candidate = None
            while fallback_index < len(self.FALLBACK_POLICY):
                policy = self.FALLBACK_POLICY[fallback_index]
                fallback_index += 1
                cand_str = f"{policy['provider']}:{policy['model']}"
                if cand_str not in attempted_runs:
                    next_candidate = policy
                    break
                    
            if next_candidate:
                logger.warning(
                    f"FallbackEngine: Failover triggered! Switching to fallback policy "
                    f"'{next_candidate['provider']}/{next_candidate['model']}'"
                )
                current_provider = next_candidate["provider"]
                current_model = next_candidate["model"]
            else:
                # No more policies. Try Mock fallback
                logger.error("FallbackEngine: All fallback policies exhausted! Routing to Mock provider.")
                return {
                    "success": True,
                    "response_text": '{"strategic_summary": "Mock fallback analysis due to all providers down.", "confidence": 50}',
                    "provider_used": "mock",
                    "model_used": "mock-model",
                    "retry_count": retry_count,
                    "fallback_count": fallback_index,
                }


fallback_engine = FallbackEngine()
