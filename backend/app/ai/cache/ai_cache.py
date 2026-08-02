"""
Enterprise AI Cache System for Phase 12.7 Enterprise AI Platform.
Features:
1. Prompt Cache (Exact SHA-256 prompt hash)
2. Semantic Cache (Vector cosine similarity matching)
3. Response Cache (Final response payload)
4. Embedding Cache (Deduplicated embedding vectors)
5. Context Cache (Compiled RAG context documents)
6. Cache Invalidation (TTL, LRU eviction, manual scope purge)
7. Cache Warming & Export
8. Telemetry Metrics (Hit/Miss ratio, Saved Latency, Saved Tokens, Saved USD Cost, Memory consumed)
"""
import os
import time
import json
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from collections import OrderedDict

from app.database.mongodb.collections.ai_gateway import EmbeddingCacheDocument, AIResponseDocument

logger = logging.getLogger("backend.ai.cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


class LRUMemoryCache:
    """In-memory LRU cache store with capacity limits and TTL expiration."""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        item = self.cache[key]
        if time.time() > item["expire_at"]:
            del self.cache[key]
            return None
        self.cache.move_to_end(key)
        return item["value"]

    def put(self, key: str, value: Any, ttl_seconds: float = 3600.0) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = {
            "value": value,
            "expire_at": time.time() + ttl_seconds,
            "size_bytes": len(str(value).encode("utf-8")),
        }
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)  # Evict LRU item

    def clear(self, prefix: str = "") -> int:
        if not prefix:
            count = len(self.cache)
            self.cache.clear()
            return count
        to_del = [k for k in self.cache if k.startswith(prefix)]
        for k in to_del:
            del self.cache[k]
        return len(to_del)

    def size_bytes(self) -> int:
        return sum(item.get("size_bytes", 0) for item in self.cache.values())


class AICacheTelemetry:
    """Telemetry tracking hit/miss counters, saved latency, saved tokens, and saved USD cost."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.prompt_hits = 0
        self.semantic_hits = 0
        self.response_hits = 0
        self.embedding_hits = 0
        self.context_hits = 0
        self.saved_latency_ms = 0.0
        self.saved_tokens = 0
        self.saved_cost_usd = 0.0

    def record_hit(self, cache_type: str, saved_lat_ms: float = 250.0, tokens: int = 200, cost_usd: float = 0.0005) -> None:
        self.hits += 1
        if cache_type == "prompt":
            self.prompt_hits += 1
        elif cache_type == "semantic":
            self.semantic_hits += 1
        elif cache_type == "response":
            self.response_hits += 1
        elif cache_type == "embedding":
            self.embedding_hits += 1
        elif cache_type == "context":
            self.context_hits += 1

        self.saved_latency_ms += saved_lat_ms
        self.saved_tokens += tokens
        self.saved_cost_usd += cost_usd

    def record_miss(self) -> None:
        self.misses += 1

    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_ratio = (self.hits / total * 100.0) if total > 0 else 0.0
        miss_ratio = (self.misses / total * 100.0) if total > 0 else 0.0

        return {
            "total_requests": total,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio_percent": round(hit_ratio, 2),
            "miss_ratio_percent": round(miss_ratio, 2),
            "prompt_hits": self.prompt_hits,
            "semantic_hits": self.semantic_hits,
            "response_hits": self.response_hits,
            "embedding_hits": self.embedding_hits,
            "context_hits": self.context_hits,
            "saved_latency_seconds": round(self.saved_latency_ms / 1000.0, 2),
            "saved_tokens": self.saved_tokens,
            "saved_cost_usd": round(self.saved_cost_usd, 6),
        }


class AICache:
    """Enterprise multi-tier cache engine supporting Redis, LRU memory, and MongoDB storage."""

    _redis_client = None

    def __init__(self, memory_capacity: int = 2000):
        self._lru_cache = LRUMemoryCache(capacity=memory_capacity)
        self.telemetry = AICacheTelemetry()
        self._init_redis()

    def _init_redis(self):
        if self._redis_client is not None:
            return
        try:
            import redis
            self._redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            self._redis_client.ping()
            logger.info("AICache connected to Redis successfully.")
        except Exception as e:
            self._redis_client = None
            logger.warning(f"AICache Redis connection unavailable ({e}), using LRU memory fallback.")

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # ─── 1 & 3. Prompt & Response Cache ───

    async def get_response(self, prompt: str, system_prompt: str = "", model: str = "") -> Optional[str]:
        """Fetch exact cached prompt/response."""
        h = self._get_hash(prompt + system_prompt + model)
        key = f"response:{h}"

        # Try LRU memory
        val = self._lru_cache.get(key)
        if val:
            self.telemetry.record_hit("response")
            return val

        # Try Redis
        self._init_redis()
        if self._redis_client:
            try:
                r_val = self._redis_client.get(f"ai_cache:{key}")
                if r_val:
                    self._lru_cache.put(key, r_val, ttl_seconds=3600)
                    self.telemetry.record_hit("response")
                    return r_val
            except Exception:
                pass

        self.telemetry.record_miss()
        return None

    def set_response(self, prompt: str, response: str, system_prompt: str = "", model: str = "", ttl_seconds: int = 3600) -> None:
        """Store prompt response in cache."""
        h = self._get_hash(prompt + system_prompt + model)
        key = f"response:{h}"

        self._lru_cache.put(key, response, ttl_seconds=ttl_seconds)

        self._init_redis()
        if self._redis_client:
            try:
                self._redis_client.setex(f"ai_cache:{key}", ttl_seconds, response)
            except Exception:
                pass

    # ─── 2. Semantic Cache ───

    async def get_semantic_response(self, prompt: str, system_prompt: str = "", model: str = "", threshold: float = 0.92) -> Optional[str]:
        """Check for semantically similar prompt responses using cosine similarity."""
        try:
            from app.ai.embeddings.embedding_service import embedding_service
            query_vector = await embedding_service.embed_text(prompt)
            if not query_vector:
                return None

            docs = await EmbeddingCacheDocument.find_all().to_list()
            best_sim = 0.0
            best_text = None

            for doc in docs:
                sim = self._cosine_similarity(query_vector, doc.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_text = doc.text

            if best_sim >= threshold and best_text:
                resp = await self.get_response(best_text, system_prompt, model)
                if resp:
                    logger.info(f"[AICache] Semantic cache HIT similarity={best_sim:.4f}")
                    self.telemetry.record_hit("semantic")
                    return resp
        except Exception as e:
            logger.debug(f"[AICache] Semantic cache lookup miss: {e}")

        return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2) or not vec1:
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0
        return dot / (mag1 * mag2)

    # ─── 4. Embedding Cache ───

    async def get_embedding(self, text: str, provider: str = "", model: str = "") -> Optional[List[float]]:
        """Fetch cached embedding vector."""
        h = self._get_hash(text)
        key = f"embedding:{h}:{provider}:{model}"

        val = self._lru_cache.get(key)
        if val:
            self.telemetry.record_hit("embedding")
            return val

        self._init_redis()
        if self._redis_client:
            try:
                r_val = self._redis_client.get(f"ai_cache:{key}")
                if r_val:
                    parsed = json.loads(r_val)
                    self._lru_cache.put(key, parsed, ttl_seconds=86400)
                    self.telemetry.record_hit("embedding")
                    return parsed
            except Exception:
                pass

        self.telemetry.record_miss()
        return None

    async def set_embedding(self, text: str, embedding: List[float], provider: str = "", model: str = "", ttl_seconds: int = 86400) -> None:
        """Store embedding vector in cache."""
        h = self._get_hash(text)
        key = f"embedding:{h}:{provider}:{model}"

        self._lru_cache.put(key, embedding, ttl_seconds=ttl_seconds)

        self._init_redis()
        if self._redis_client:
            try:
                self._redis_client.setex(f"ai_cache:{key}", ttl_seconds, json.dumps(embedding))
            except Exception:
                pass

    # ─── 5. Context Cache (RAG) ───

    async def get_context(self, rag_query: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch cached compiled RAG context documents."""
        key = f"context:{self._get_hash(rag_query)}"
        val = self._lru_cache.get(key)
        if val:
            self.telemetry.record_hit("context")
            return val

        self._init_redis()
        if self._redis_client:
            try:
                r_val = self._redis_client.get(f"ai_cache:{key}")
                if r_val:
                    parsed = json.loads(r_val)
                    self._lru_cache.put(key, parsed, ttl_seconds=1800)
                    self.telemetry.record_hit("context")
                    return parsed
            except Exception:
                pass

        self.telemetry.record_miss()
        return None

    def set_context(self, rag_query: str, context_docs: List[Dict[str, Any]], ttl_seconds: int = 1800) -> None:
        """Cache compiled RAG context documents."""
        key = f"context:{self._get_hash(rag_query)}"
        self._lru_cache.put(key, context_docs, ttl_seconds=ttl_seconds)

        self._init_redis()
        if self._redis_client:
            try:
                self._redis_client.setex(f"ai_cache:{key}", ttl_seconds, json.dumps(context_docs))
            except Exception:
                pass

    # ─── 6. Cache Invalidation & Purge ───

    def clear(self, scope: str = "all") -> Dict[str, Any]:
        """Manually purge cache by scope: all | prompt | response | embedding | context."""
        cleared_count = 0
        if scope == "all":
            cleared_count += self._lru_cache.clear("")
        else:
            cleared_count += self._lru_cache.clear(prefix=f"{scope}:")

        self._init_redis()
        if self._redis_client:
            try:
                pattern = "ai_cache:*" if scope == "all" else f"ai_cache:{scope}:*"
                keys = self._redis_client.keys(pattern)
                if keys:
                    self._redis_client.delete(*keys)
                    cleared_count += len(keys)
            except Exception as e:
                logger.warning(f"Redis purge failed: {e}")

        logger.info(f"[AICache] Purged cache scope '{scope}': {cleared_count} keys removed.")
        return {"scope": scope, "cleared_count": cleared_count, "timestamp": datetime.now(timezone.utc).isoformat()}

    # ─── 7. Cache Warming ───

    def warm(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Pre-load cache entries for warming up prompt/context templates."""
        warmed = 0
        for item in items:
            prompt = item.get("prompt")
            response = item.get("response")
            if prompt and response:
                self.set_response(prompt, response, system_prompt=item.get("system_prompt", ""), model=item.get("model", ""))
                warmed += 1
            context_query = item.get("context_query")
            context_docs = item.get("context_docs")
            if context_query and context_docs:
                self.set_context(context_query, context_docs)
                warmed += 1

        logger.info(f"[AICache] Cache warming complete: {warmed} items pre-loaded.")
        return {"warmed_items": warmed, "timestamp": datetime.now(timezone.utc).isoformat()}

    # ─── 8. Export Snapshot ───

    def export_snapshot(self) -> Dict[str, Any]:
        """Export snapshot of cache keys and stats."""
        stats = self.get_stats_sync()
        return {
            "stats": stats,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "sample_keys": list(self._lru_cache.cache.keys())[:50],
        }

    def get_stats_sync(self) -> Dict[str, Any]:
        redis_connected = False
        redis_keys_count = 0
        if self._redis_client:
            try:
                redis_connected = True
                redis_keys_count = len(self._redis_client.keys("ai_cache:*"))
            except Exception:
                pass

        telemetry_stats = self.telemetry.get_stats()
        mem_bytes = self._lru_cache.size_bytes()

        return {
            **telemetry_stats,
            "redis_connected": redis_connected,
            "redis_keys_count": redis_keys_count,
            "lru_memory_keys": len(self._lru_cache.cache),
            "memory_consumed_mb": round(mem_bytes / (1024 * 1024), 3),
        }

    async def get_stats(self) -> Dict[str, Any]:
        return self.get_stats_sync()


ai_cache = AICache()
