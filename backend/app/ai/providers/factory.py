"""
LLM Provider Factory — reads environment variables to instantiate the correct provider.

Environment variables:
    LLM_PROVIDER:     Provider name: openai (default), openrouter, mock
    LLM_API_KEY:      API key for the provider (not needed for mock)
    LLM_MODEL:        Model name (default: gpt-4o-mini)
    LLM_BASE_URL:     Custom base URL (for OpenRouter: https://openrouter.ai/api/v1)
"""
import logging
import os
from app.ai.providers.base_llm import BaseLLMProvider

logger = logging.getLogger("backend.ai.factory")


class AIGatewayLLMProvider(BaseLLMProvider):
    """LLM provider wrapper routing all requests through the central AI Gateway."""

    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        from app.ai.gateway.gateway import ai_gateway
        res = await ai_gateway.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=self.provider,
            model=self.model,
        )
        return res["response_text"]


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function returning the configured LLM provider instance.
    All calls route through the unified AIGateway.
    """
    provider_name = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    model = os.getenv("LLM_MODEL", "gemini-1.5-flash").strip()
    
    logger.info(f"Factory routing get_llm_provider() via AIGateway: provider={provider_name}, model={model}")
    return AIGatewayLLMProvider(provider=provider_name, model=model)

