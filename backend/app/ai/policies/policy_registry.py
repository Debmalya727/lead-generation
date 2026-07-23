"""
Policy Registry for AI Policy Engine (Phase 12.7B).
CRUD operations for AIPolicyDocument with in-memory caching.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.database.mongodb.collections.ai_gateway_extended import AIPolicyDocument
from app.ai.policies.schemas import PolicyRule, PolicyCondition, PolicyAction

logger = logging.getLogger("backend.ai.policies.registry")


class PolicyRegistry:
    """Manages policies stored in MongoDB with in-memory hot cache."""

    _cache: Dict[str, List[PolicyRule]] = {}  # capability → sorted rules

    async def seed_defaults(self, rules: List[PolicyRule]) -> None:
        """Seed default policy rules into MongoDB if collection is empty."""
        count = await AIPolicyDocument.count()
        if count == 0:
            for rule in rules:
                doc = AIPolicyDocument(
                    policy_id=rule.policy_id,
                    name=rule.name,
                    description=rule.description,
                    capability=rule.capability,
                    provider=rule.action.provider,
                    model=rule.action.model,
                    priority=rule.priority,
                    is_active=rule.is_active,
                    conditions=rule.conditions.model_dump(),
                    org_id=rule.org_id,
                )
                await doc.insert()
            logger.info(f"PolicyRegistry: Seeded {len(rules)} default policy rules.")
        self._cache.clear()

    async def get_rules_for_capability(self, capability: str) -> List[PolicyRule]:
        """Return all active rules for a capability, sorted by priority."""
        if capability in self._cache:
            return self._cache[capability]

        docs = await AIPolicyDocument.find(
            AIPolicyDocument.capability == capability,
            AIPolicyDocument.is_active == True
        ).sort("priority").to_list()

        rules = []
        for doc in docs:
            rule = PolicyRule(
                policy_id=doc.policy_id,
                name=doc.name,
                capability=doc.capability,
                priority=doc.priority,
                is_active=doc.is_active,
                conditions=PolicyCondition(**(doc.conditions or {})),
                action=PolicyAction(provider=doc.provider, model=doc.model),
                org_id=doc.org_id,
                description=doc.description,
            )
            rules.append(rule)

        self._cache[capability] = rules
        return rules

    async def list_all(self) -> List[AIPolicyDocument]:
        """Return all policy documents."""
        return await AIPolicyDocument.find_all().to_list()

    async def create(
        self,
        policy_id: str,
        name: str,
        capability: str,
        provider: str,
        model: str,
        priority: int = 100,
        conditions: Optional[Dict[str, Any]] = None,
        org_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AIPolicyDocument:
        """Create a new policy rule."""
        doc = AIPolicyDocument(
            policy_id=policy_id,
            name=name,
            capability=capability,
            provider=provider,
            model=model,
            priority=priority,
            conditions=conditions or {},
            org_id=org_id,
            description=description,
        )
        await doc.insert()
        self._cache.pop(capability, None)  # Invalidate cache
        return doc

    def invalidate_cache(self, capability: Optional[str] = None) -> None:
        """Invalidate the in-memory policy cache."""
        if capability:
            self._cache.pop(capability, None)
        else:
            self._cache.clear()


policy_registry = PolicyRegistry()
