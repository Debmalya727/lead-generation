import os
import logging
from app.vector.embeddings.providers.base_embedding import BaseEmbeddingProvider
from app.vector.embeddings.providers.openai_embedding import OpenAIEmbeddingProvider
from app.vector.embeddings.providers.sentence_transformers_embedding import SentenceTransformersEmbeddingProvider

logger = logging.getLogger("backend.vector.embeddings.factory")

_embedding_provider_instance = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    """
    Factory resolving active Embedding Provider.
    Supports: OpenAI, SentenceTransformers, Mock.
    """
    global _embedding_provider_instance
    if _embedding_provider_instance is not None:
        return _embedding_provider_instance

    provider_name = os.getenv("EMBEDDING_PROVIDER", "openai").lower().strip()
    api_key = os.getenv("OPENAI_API_KEY", "")

    if provider_name == "openai" and api_key and not api_key.startswith("mock-"):
        try:
            logger.info("Initializing OpenAIEmbeddingProvider...")
            _embedding_provider_instance = OpenAIEmbeddingProvider(api_key=api_key)
            return _embedding_provider_instance
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAIEmbeddingProvider: {str(e)}, falling back to SentenceTransformers.")

    logger.info("Initializing SentenceTransformersEmbeddingProvider (Local Normalized 1536-dim Engine)...")
    _embedding_provider_instance = SentenceTransformersEmbeddingProvider()
    return _embedding_provider_instance
