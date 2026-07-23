import os
import logging

from app.vector.providers.base_vector import BaseVectorProvider
from app.vector.providers.in_memory_vector import InMemoryVectorProvider
from app.vector.providers.qdrant_vector import QdrantVectorProvider
from app.vector.providers.chroma_vector import ChromaVectorProvider
from app.vector.providers.milvus_vector import MilvusVectorProvider

logger = logging.getLogger("backend.vector.providers.factory")

_vector_provider_instance = None


def get_vector_provider() -> BaseVectorProvider:
    """
    Factory resolving active Vector Store Provider.
    Supports: Qdrant, Chroma, Milvus, InMemoryVectorProvider.
    """
    global _vector_provider_instance
    if _vector_provider_instance is not None:
        return _vector_provider_instance

    provider_name = os.getenv("VECTOR_PROVIDER", "in_memory").lower().strip()

    if provider_name == "qdrant":
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        logger.info(f"Initializing QdrantVectorProvider at {host}:{port}...")
        _vector_provider_instance = QdrantVectorProvider(host=host, port=port)
        return _vector_provider_instance

    if provider_name == "chroma":
        host = os.getenv("CHROMA_HOST", "localhost")
        port = int(os.getenv("CHROMA_PORT", "8000"))
        logger.info(f"Initializing ChromaVectorProvider at {host}:{port}...")
        _vector_provider_instance = ChromaVectorProvider(host=host, port=port)
        return _vector_provider_instance

    if provider_name == "milvus":
        host = os.getenv("MILVUS_HOST", "localhost")
        port = int(os.getenv("MILVUS_PORT", "19530"))
        logger.info(f"Initializing MilvusVectorProvider at {host}:{port}...")
        _vector_provider_instance = MilvusVectorProvider(host=host, port=port)
        return _vector_provider_instance

    logger.info("Initializing InMemoryVectorProvider (High-Speed Cosine Similarity Vector Store)...")
    _vector_provider_instance = InMemoryVectorProvider()
    return _vector_provider_instance
