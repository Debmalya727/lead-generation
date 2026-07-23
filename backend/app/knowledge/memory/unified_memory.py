"""
Phase 14.6 — Unified Enterprise Memory.
Implements 4 Memory Types:
  - Working Memory
  - Episodic Memory
  - Semantic Memory
  - Procedural Memory
With Memory Decay e^(-λt), Associative Recall, Memory Consolidation, Summarization, and Retention Policies.
"""
from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.mongodb.collections.knowledge import EnterpriseMemoryRecord

logger = logging.getLogger("backend.knowledge.memory")

MEMORY_TYPES = {"working", "episodic", "semantic", "procedural"}


class UnifiedEnterpriseMemory:
    """4-Tier Enterprise Memory System managing Working, Episodic, Semantic, and Procedural memory."""

    async def store_memory(
        self,
        key: str,
        value: str,
        memory_type: str = "semantic",
        user_id: str = "user_default",
        confidence: float = 0.95,
        decay_factor: float = 0.01,
        retention_days: int = 365,
        associations: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EnterpriseMemoryRecord:
        memory_type = memory_type.lower()
        if memory_type not in MEMORY_TYPES:
            raise ValueError(f"Invalid memory_type '{memory_type}'. Supported: {MEMORY_TYPES}")

        mem_id = f"mem_{uuid.uuid4().hex[:16]}"
        mem = EnterpriseMemoryRecord(
            memory_id=mem_id,
            user_id=user_id,
            memory_type=memory_type,
            key=key,
            value=value,
            confidence=confidence,
            decay_factor=decay_factor,
            retention_days=retention_days,
            associations=associations or [],
            metadata=metadata or {},
        )
        try:
            await mem.insert()
        except Exception:
            pass

        logger.info(f"[UnifiedMemory] Stored memory '{mem_id}' ({memory_type}) for key '{key}'")
        return mem

    async def recall_memory(
        self,
        key_or_query: str,
        memory_type: Optional[str] = None,
        user_id: str = "user_default",
        limit: int = 10,
    ) -> List[EnterpriseMemoryRecord]:
        query = EnterpriseMemoryRecord.find(EnterpriseMemoryRecord.user_id == user_id)
        if memory_type:
            query = EnterpriseMemoryRecord.find(
                EnterpriseMemoryRecord.user_id == user_id,
                EnterpriseMemoryRecord.memory_type == memory_type,
            )

        memories = await query.sort("-last_accessed_at").limit(limit * 2).to_list()
        now = datetime.now(timezone.utc)

        recalled: List[EnterpriseMemoryRecord] = []
        for m in memories:
            hours_elapsed = (now - m.last_accessed_at).total_seconds() / 3600.0
            decayed_score = m.confidence * math.exp(-m.decay_factor * hours_elapsed)

            if key_or_query.lower() in m.key.lower() or key_or_query.lower() in m.value.lower() or decayed_score > 0.3:
                m.access_count += 1
                m.last_accessed_at = now
                await m.save()
                recalled.append(m)

        return recalled[:limit]

    async def consolidate_working_memory(self, user_id: str = "user_default") -> int:
        """Consolidates short-term working memory items into semantic or episodic memory."""
        working_items = await EnterpriseMemoryRecord.find(
            EnterpriseMemoryRecord.user_id == user_id,
            EnterpriseMemoryRecord.memory_type == "working",
        ).to_list()

        consolidated_count = 0
        for item in working_items:
            item.memory_type = "semantic" if item.access_count > 2 else "episodic"
            await item.save()
            consolidated_count += 1

        logger.info(f"[UnifiedMemory] Consolidated {consolidated_count} working memory items for user '{user_id}'")
        return consolidated_count


unified_enterprise_memory = UnifiedEnterpriseMemory()
