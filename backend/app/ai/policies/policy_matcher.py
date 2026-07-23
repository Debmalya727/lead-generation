"""
Policy matcher for AI Policy Engine (Phase 12.7B).
Evaluates request context against PolicyRule conditions.
"""
from typing import Any, Dict, List, Optional
from app.ai.policies.schemas import PolicyRule, PolicyCondition


class PolicyMatcher:
    """Evaluates whether a PolicyRule applies to a given request context."""

    def matches(self, rule: PolicyRule, context: Dict[str, Any]) -> bool:
        """
        Returns True if the rule's conditions match the given context dict.
        Context may include: org_id, user_tier, estimated_tokens, estimated_cost.
        """
        cond: PolicyCondition = rule.conditions

        # Org override — if the rule has an org_id, it only applies to that org
        if rule.org_id and rule.org_id != context.get("org_id"):
            return False

        # Condition: org_id restriction
        if cond.org_id and cond.org_id != context.get("org_id"):
            return False

        # Condition: user tier
        if cond.user_tier and cond.user_tier != context.get("user_tier"):
            return False

        # Condition: minimum context tokens
        if cond.min_context_tokens is not None:
            actual = context.get("estimated_tokens", 0)
            if actual < cond.min_context_tokens:
                return False

        # Condition: max cost per request
        if cond.max_cost_per_request is not None:
            actual = context.get("estimated_cost", 0.0)
            if actual > cond.max_cost_per_request:
                return False

        return True

    def filter_matching(self, rules: List[PolicyRule], context: Dict[str, Any]) -> List[PolicyRule]:
        """Filter and sort matching rules by priority (lowest = highest priority)."""
        matching = [r for r in rules if r.is_active and self.matches(r, context)]
        return sorted(matching, key=lambda r: r.priority)


policy_matcher = PolicyMatcher()
