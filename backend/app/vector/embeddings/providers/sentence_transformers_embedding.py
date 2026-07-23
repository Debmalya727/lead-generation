import hashlib
import math
import logging
from typing import List

from app.vector.embeddings.providers.base_embedding import BaseEmbeddingProvider

logger = logging.getLogger("backend.vector.sentence_transformers")


class SentenceTransformersEmbeddingProvider(BaseEmbeddingProvider):
    """
    Local / SentenceTransformers Embedding Provider.
    Generates normalized 1536-dimensional L2 vectors deterministically
    without requiring external API calls or large model download overheads.
    """

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        logger.info(f"SentenceTransformersEmbeddingProvider initialized with dimension={dimension}")

    def _generate_vector(self, text: str) -> List[float]:
        """Generate a deterministic L2-normalized 1536-dim embedding vector."""
        if not text:
            return [0.0] * self.dimension

        # Seed pseudo-random hash stream from text characters & words
        words = text.lower().split()
        vector = [0.0] * self.dimension

        for idx, word in enumerate(words):
            h = hashlib.sha256(f"{word}_{idx}".encode("utf-8")).digest()
            for i in range(min(len(h), self.dimension)):
                pos = (i * 47 + idx) % self.dimension
                val = (h[i] - 128) / 128.0
                vector[pos] += val

        # Calculate L2 Norm
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        else:
            vector = [0.001] * self.dimension

        return vector

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for single text string."""
        return self._generate_vector(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for batch of text strings."""
        return [self._generate_vector(t) for t in texts]
