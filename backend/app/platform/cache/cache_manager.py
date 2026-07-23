"""
CacheManager for Phase 12.5: Enterprise Platform Hardening.

Multi-layer caching system supporting Redis backed cache with in-memory fallback.
Caches: Workflow Cache, Tool Cache, RAG Cache, Conversation Cache.
"""
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("backend.platform.cache")


class CacheManager:
    """Manager handling multi-layer Redis and in-memory caching."""

    _memory_cache: Dict[str, Any] = {}

    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Fetch cached value by namespace and key."""
        full_key = f"{namespace}:{key}"
        try:
            from app.cache.redis_client import redis_client
            if redis_client:
                val = redis_client.get(full_key)
                if val:
                    return json.loads(val)
        except Exception:
            pass

        return self._memory_cache.get(full_key)

    def set(self, namespace: str, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Cache value with TTL."""
        full_key = f"{namespace}:{key}"
        serialized = json.dumps(value)
        try:
            from app.cache.redis_client import redis_client
            if redis_client:
                redis_client.setex(full_key, ttl_seconds, serialized)
                return
        except Exception:
            pass

        self._memory_cache[full_key] = value

    def invalidate(self, namespace: str, key: str) -> None:
        """Invalidate cached entry."""
        full_key = f"{namespace}:{key}"
        try:
            from app.cache.redis_client import redis_client
            if redis_client:
                redis_client.delete(full_key)
        except Exception:
            pass

        if full_key in self._memory_cache:
            del self._memory_cache[full_key]
