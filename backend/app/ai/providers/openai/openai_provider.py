import asyncio
import logging
from openai import AsyncOpenAI
from app.ai.providers.base_llm import BaseLLMProvider

logger = logging.getLogger("backend.ai.openai_provider")


class OpenAIProvider(BaseLLMProvider):
    """
    LLM provider adapter for OpenAI-compatible APIs.
    Works with OpenAI directly and with OpenRouter by setting a custom base_url.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        max_retries: int = 3,
    ):
        self.model = model
        self.max_retries = max_retries
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"OpenAIProvider initialized with model={model}, base_url={base_url}")

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        """Send completion request with exponential backoff retry logic."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                logger.debug(f"OpenAIProvider completion successful on attempt {attempt}")
                return content or ""
            except Exception as e:
                logger.warning(f"OpenAIProvider attempt {attempt}/{self.max_retries} failed: {str(e)}")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff: 2, 4 seconds
                else:
                    logger.error(f"OpenAIProvider all retries exhausted: {str(e)}")
                    raise
        return ""
