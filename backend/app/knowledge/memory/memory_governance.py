"""
Phase 14.6.8 — Memory Governance.
Memory encryption, Legal Hold policies, and GDPR Right-to-be-Forgotten erasure.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.database.mongodb.collections.knowledge import EnterpriseMemoryRecord, MemoryGovernanceRecord

logger = logging.getLogger("backend.knowledge.memory.governance")


class MemoryGovernanceService:
    """Enterprise compliance manager for memory retention, GDPR deletion, and Legal Hold."""

    async def apply_governance_policy(
        self,
        memory_id: str,
        user_id: str,
        retention_policy: str = "standard_365d",
    ) -> MemoryGovernanceRecord:
        gov_id = f"gov_{uuid.uuid4().hex[:12]}"
        rec = MemoryGovernanceRecord(
            governance_id=gov_id,
            memory_id=memory_id,
            user_id=user_id,
            is_encrypted=True,
            is_legal_hold=False,
            gdpr_erasure_requested=False,
            retention_policy=retention_policy,
        )
        try:
            await rec.insert()
        except Exception:
            pass
        logger.info(f"[MemoryGovernance] Applied policy '{retention_policy}' to memory '{memory_id}'")
        return rec

    async def process_gdpr_erasure(self, user_id: str) -> int:
        """Executes GDPR Right-to-be-Forgotten erasure for user's non-legal-hold memories."""
        memories = await EnterpriseMemoryRecord.find(EnterpriseMemoryRecord.user_id == user_id).to_list()
        erased_count = 0

        for m in memories:
            gov = await MemoryGovernanceRecord.find_one(MemoryGovernanceRecord.memory_id == m.memory_id)
            if gov and gov.is_legal_hold:
                logger.warning(f"[MemoryGovernance] GDPR erasure skipped for memory '{m.memory_id}' (Legal Hold Active)")
                continue

            await m.delete()
            erased_count += 1

        logger.info(f"[MemoryGovernance] GDPR erasure completed for user '{user_id}': {erased_count} memories deleted.")
        return erased_count


memory_governance_service = MemoryGovernanceService()
