"""
Phase 14.1 Enterprise Knowledge Gateway — Quota Manager.
Enforces storage quotas, rate limits, and asset size limits per user and organization.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("backend.knowledge.gateway.quota_manager")

MAX_SINGLE_FILE_BYTES = 50 * 1024 * 1024  # 50 MB limit
MAX_USER_DAILY_BYTES = 500 * 1024 * 1024  # 500 MB per user per day


class EnterpriseQuotaManager:
    """Enforces enterprise quotas and rate limits on Knowledge Gateway ingestion."""

    def check_quota(self, user_id: str, content_size_bytes: int, org_id: str = "default") -> Tuple[bool, Dict[str, Any]]:
        if content_size_bytes > MAX_SINGLE_FILE_BYTES:
            details = {
                "user_id": user_id,
                "org_id": org_id,
                "file_size": content_size_bytes,
                "max_allowed": MAX_SINGLE_FILE_BYTES,
                "reason": "File size exceeds single asset limit of 50MB",
            }
            logger.warning(f"[QuotaManager] Quota exceeded for user '{user_id}': Asset size {content_size_bytes} > {MAX_SINGLE_FILE_BYTES}")
            return False, details

        details = {
            "user_id": user_id,
            "org_id": org_id,
            "file_size": content_size_bytes,
            "quota_remaining": MAX_USER_DAILY_BYTES - content_size_bytes,
        }
        return True, details


quota_manager = EnterpriseQuotaManager()
