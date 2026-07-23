"""
AICache supporting Redis caching, semantic caching (via vector similarity),
prompt/response caching, embedding caching, TTL, and cache statistics.
"""
import os
import json
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from app.database.mongodb.collections.ai_gateway import EmbeddingCacheDocument, AIResponseDocument

logger = logging.getLogger("backend.ai.cache")

# Retrieve Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

class AICache:
    """Multi-layer cache with Redis and MongoDB fallback."""

    _redis_client = None
    _memory_cache: Dict[str, Any] = {}

    def __init__(self):
        self._init_redis()

    def _init_redis(self):
        """Lazy init Redis connection."""
        if self._redis_client is not None:
            return
        try:
            import redis
            self._redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            self._redis_client.ping()
            logger.info("AICache successfully connected to Redis")
        except Exception as e:
            self._redis_client = None
            logger.warning(f"AICache failed to connect to Redis ({str(e)}), using memory/MongoDB fallback")

    def _get_hash(self, text: str) -> str:
        """Helper to generate SHA-256 hash of a string."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # ─── Response Cache (Prompt & Response) ───

    async def get_response(self, prompt: str, system_prompt: str = "", model: str = "") -> Optional[str]:
        """Fetch cached response for a given prompt + system_prompt + model."""
        key = f"response:{self._get_hash(prompt + system_prompt + model)}"
        
        # 1. Try Redis
        self._init_redis()
        if self._redis_client:
            try:
                val = self._redis_client.get(f"ai_cache:{key}")
                if val:
                    logger.info(f"AICache: Redis hit for prompt response")
                    return val
            except Exception:
                pass

        # 2. Try Memory
        if key in self._memory_cache:
            item = self._memory_cache[key]
            if datetime.now(timezone.utc) < item["expire_at"]:
                logger.info(f"AICache: Memory hit for prompt response")
                return item["value"]
            else:
                del self._memory_cache[key]

        # 3. Try MongoDB
        try:
            doc = await AIResponseDocument.find_one(
                AIResponseDocument.correlation_id == f"cached_{key}"
            )
            if doc:
                logger.info(f"AICache: MongoDB hit for prompt response")
                # Write back to Redis/Memory
                self.set_response(prompt, doc.response_text, system_prompt, model)
                return doc.response_text
        except Exception:
            pass

        return None

    def set_response(self, prompt: str, response: str, system_prompt: str = "", model: str = "", ttl_seconds: int = 3600) -> None:
        """Cache response for a prompt."""
        key = f"response:{self._get_hash(prompt + system_prompt + model)}"
        
        # 1. Save in Redis
        self._init_redis()
        if self._redis_client:
            try:
                self._redis_client.setex(f"ai_cache:{key}", ttl_seconds, response)
            except Exception:
                pass

        # 2. Save in Memory
        expire_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        self._memory_cache[key] = {"value": response, "expire_at": expire_at}

        # 3. Save in MongoDB as fallback reference
        async def save_mongo():
            try:
                doc = AIResponseDocument(
                    correlation_id=f"cached_{key}",
                    response_text=response,
                    provider_used="cache",
                    model_used=model or "cached",
                    cached=True
                )
                await doc.insert()
            except Exception:
                pass
        
        # Run async save in background if loop is active
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(save_mongo())
        except Exception:
            pass

    # ─── Embedding Cache ───

    async def get_embedding(self, text: str, provider: str = "", model: str = "") -> Optional[List[float]]:
        """Fetch cached embedding vector."""
        h = self._get_hash(text)
        key = f"embedding:{h}:{provider}:{model}"

        # 1. Try Redis
        self._init_redis()
        if self._redis_client:
            try:
                val = self._redis_client.get(f"ai_cache:{key}")
                if val:
                    return json.loads(val)
            except Exception:
                pass

        # 2. Try MongoDB
        try:
            doc = await EmbeddingCacheDocument.find_one(
                EmbeddingCacheDocument.text_hash == h
            )
            if doc:
                # Write back to Redis
                if self._redis_client:
                    try:
                        self._redis_client.setex(f"ai_cache:{key}", 86400, json.dumps(doc.embedding))
                    except Exception:
                        pass
                return doc.embedding
        except Exception:
            pass

        return None

    async def set_embedding(self, text: str, embedding: List[float], provider: str = "", model: str = "") -> None:
        """Cache embedding vector."""
        h = self._get_hash(text)
        key = f"embedding:{h}:{provider}:{model}"

        # 1. Save in Redis
        self._init_redis()
        if self._redis_client:
            try:
                self._redis_client.setex(f"ai_cache:{key}", 86400, json.dumps(embedding))
            except Exception:
                pass

        # 2. Save in MongoDB
        try:
            doc = await EmbeddingCacheDocument.find_one(EmbeddingCacheDocument.text_hash == h)
            if not doc:
                doc = EmbeddingCacheDocument(
                    text_hash=h,
                    text=text,
                    embedding=embedding,
                    provider=provider,
                    model=model
                )
                await doc.insert()
        except Exception as e:
            logger.warning(f"Failed to cache embedding to MongoDB: {str(e)}")

    # ─── Semantic Cache ───

    async def get_semantic_response(self, prompt: str, system_prompt: str = "", model: str = "", threshold: float = 0.96) -> Optional[str]:
        """
        Check if a semantically similar prompt exists in MongoDB using cosine similarity.
        Only works if we have pre-calculated embeddings.
        """
        try:
            from app.ai.embeddings.embedding_service import embedding_service
            # 1. Generate query embedding
            query_vector = await embedding_service.embed_text(prompt)
            if not query_vector:
                return None

            # 2. Search all cached embedding documents
            # Note: For production large scale, use Vector database (Chroma/Mongo Atlas vector search).
            # Here we do a fast in-memory similarity comparison for demonstration & local correctness.
            docs = await EmbeddingCacheDocument.find_all().to_list()
            
            best_similarity = 0.0
            best_text = None
            
            for doc in docs:
                sim = self._cosine_similarity(query_vector, doc.embedding)
                if sim > best_similarity:
                    best_similarity = sim
                    best_text = doc.text

            if best_similarity >= threshold and best_text:
                logger.info(f"AICache: Semantic cache HIT similarity={best_similarity:.4f}")
                # Fetch matching response
                resp = await self.get_response(best_text, system_prompt, model)
                if resp:
                    return resp
        except Exception as e:
            logger.debug(f"Semantic Cache miss or error: {str(e)}")
        
        return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two float vectors."""
        if len(vec1) != len(vec2) or not vec1:
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude_a = sum(a * a for a in vec1) ** 0.5
        magnitude_b = sum(b * b for b in vec2) ** 0.5
        if magnitude_a == 0.0 or magnitude_b == 0.0:
            return 0.0
        return dot_product / (magnitude_a * magnitude_b)

    async def get_stats(self) -> Dict[str, Any]:
        """Retrieve cache hit statistics."""
        redis_connected = False
        redis_keys_count = 0
        if self._redis_client:
            try:
                redis_connected = True
                redis_keys_count = len(self._redis_client.keys("ai_cache:*"))
            except Exception:
                pass
        
        mongo_embedding_count = await EmbeddingCacheDocument.count()
        mongo_response_count = await AIResponseDocument.find(AIResponseDocument.cached == True).count()

        return {
            "redis_connected": redis_connected,
            "redis_keys_count": redis_keys_count,
            "mongo_cached_embeddings": mongo_embedding_count,
            "mongo_cached_responses": mongo_response_count,
            "memory_cache_keys": len(self._memory_cache)
        }

# Global singleton
ai_cache = AICache()
