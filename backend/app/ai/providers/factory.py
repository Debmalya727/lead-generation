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


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function returning the configured LLM provider instance.
    Falls back to MockLLMProvider if no API key is set.
    """
    provider_name = os.getenv("LLM_PROVIDER", "openai").lower().strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip()

    # Fall back to mock if no API key provided
    if not api_key:
        logger.warning(
            "LLM_API_KEY is not set. Using MockLLMProvider. "
            "Set LLM_API_KEY environment variable for real AI extraction."
        )
        from app.ai.providers.mock.mock_provider import MockLLMProvider
        return MockLLMProvider()

    if provider_name in ("openai", "openrouter"):
        from app.ai.providers.openai.openai_provider import OpenAIProvider
        # OpenRouter uses openai-compatible API but with its own base URL
        if provider_name == "openrouter" and base_url == "https://api.openai.com/v1":
            base_url = "https://openrouter.ai/api/v1"
        logger.info(f"Using OpenAIProvider (provider_name={provider_name}, model={model})")
        return OpenAIProvider(api_key=api_key, model=model, base_url=base_url)

    # Default fallback
    logger.warning(f"Unknown LLM_PROVIDER='{provider_name}'. Falling back to MockLLMProvider.")
    from app.ai.providers.mock.mock_provider import MockLLMProvider
    return MockLLMProvider()
