"""
Policy Engine orchestrator for Phase 12.7B AI Gateway.
Resolves a capability + context to a concrete {provider, model} using policy rules.
"""
import logging
from typing import Any, Dict, Optional

from app.ai.policies.schemas import PolicyResolution
from app.ai.policies.policy_registry import policy_registry
from app.ai.policies.policy_matcher import policy_matcher
from app.ai.policies.policy_rules import DEFAULT_POLICY_RULES

logger = logging.getLogger("backend.ai.policies.engine")

# Default fallback if no policy matches
_DEFAULT_RESOLUTION = {"provider": "gemini", "model": "gemini-1.5-flash"}


class PolicyEngine:
    """
    Resolves capability + request context → {provider, model}.
    Resolution order:
      1. Org-specific policy rules (highest priority)
      2. Global policy rules (sorted by priority)
      3. Default fallback from capability registry
    """

    _initialized = False

    async def initialize(self) -> None:
        """Seed default policies on first startup."""
        if not self._initialized:
            await policy_registry.seed_defaults(DEFAULT_POLICY_RULES)
            self._initialized = True
            logger.info("PolicyEngine: Initialized with default policy rules.")

    async def resolve(
        self,
        capability: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyResolution:
        """
        Resolve a capability to a provider/model pair.
        Returns PolicyResolution with routing decision and policy metadata.
        """
        context = context or {}
        rules = await policy_registry.get_rules_for_capability(capability)

        # Filter by context conditions and priority
        matching = policy_matcher.filter_matching(rules, context)

        if matching:
            best = matching[0]
            logger.info(
                f"PolicyEngine: Capability '{capability}' resolved to "
                f"{best.action.provider}/{best.action.model} via policy '{best.policy_id}'"
            )
            return PolicyResolution(
                capability=capability,
                provider=best.action.provider,
                model=best.action.model,
                policy_id=best.policy_id,
                policy_name=best.name,
                resolved_from="policy",
            )

        # Fallback to default provider/model
        logger.info(f"PolicyEngine: No policy matched capability '{capability}'. Using default fallback.")
        return PolicyResolution(
            capability=capability,
            provider=_DEFAULT_RESOLUTION["provider"],
            model=_DEFAULT_RESOLUTION["model"],
            resolved_from="default",
        )


policy_engine = PolicyEngine()
