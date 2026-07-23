import asyncio
import logging
from typing import List
from openai import AsyncOpenAI

from app.vector.embeddings.providers.base_embedding import BaseEmbeddingProvider

logger = logging.getLogger("backend.vector.openai_embedding")


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Embedding Provider Adapter using OpenAI API (text-embedding-3-small / text-embedding-ada-002)."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.openai.com/v1",
    ):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"OpenAIEmbeddingProvider initialized with model={model}")

    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        if not text.strip():
            return [0.0] * 1536
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding call failed: {str(e)}")
            raise e

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""
        if not texts:
            return []
        try:
            cleaned = [t if t.strip() else "empty text" for t in texts]
            response = await self.client.embeddings.create(
                model=self.model,
                input=cleaned,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.warning(f"OpenAI batch embedding call failed: {str(e)}")
            raise e
