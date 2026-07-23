"""
PolicyEngine for Phase 11 — Milestone 4: Autonomous Workflow & Tool Orchestration Engine.

Enforces governance rules, tool permissions, token budgets, and approval policies.
"""
import logging
from typing import Dict, List, Optional, Any
from app.database.mongodb.collections.agent_workflow import WorkflowPolicyDocument

logger = logging.getLogger("backend.agents.workflow.policies")


class PolicyEngine:
    """Governance Policy Engine evaluating workflow compliance rules."""

    async def evaluate_step_policy(
        self,
        policy_id: Optional[str],
        tool_id: str,
        step_inputs: Dict[str, Any],
        token_usage: int = 0,
        current_step_count: int = 1,
    ) -> Dict[str, Any]:
        """
        Evaluate if a step invocation satisfies policy constraints.
        Returns {"allowed": bool, "approval_required": bool, "reason": str}
        """
        if not policy_id:
            return {"allowed": True, "approval_required": False, "reason": "No policy applied."}

        try:
            policy = await WorkflowPolicyDocument.find_one(WorkflowPolicyDocument.policy_id == policy_id)
            if not policy or not policy.is_active:
                return {"allowed": True, "approval_required": False, "reason": "Policy inactive or not found."}

            # 1. Allowed tools check
            if policy.allowed_tools and tool_id not in policy.allowed_tools:
                reason = f"Tool '{tool_id}' is not in policy allowed_tools whitelist."
                logger.warning(f"Policy Engine violation: {reason}")
                return {"allowed": False, "approval_required": False, "reason": reason}

            # 2. Token budget check
            if token_usage > policy.token_budget:
                reason = f"Token budget exceeded ({token_usage} > {policy.token_budget})."
                logger.warning(f"Policy Engine violation: {reason}")
                return {"allowed": False, "approval_required": False, "reason": reason}

            # 3. Execution limit step count check
            max_steps = policy.execution_limits.get("max_steps", 50)
            if current_step_count > max_steps:
                reason = f"Max step execution limit exceeded ({current_step_count} > {max_steps})."
                return {"allowed": False, "approval_required": False, "reason": reason}

            return {
                "allowed": True,
                "approval_required": policy.approval_required,
                "reason": "Policy constraints satisfied.",
            }
        except Exception as e:
            logger.warning(f"Policy Engine evaluation exception: {str(e)}")
            return {"allowed": True, "approval_required": False, "reason": f"Policy evaluation error: {str(e)}"}
