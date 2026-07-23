"""
Capability Router for Phase 12.7B AI Gateway.
Routes capability-based requests through PolicyEngine to the AIGateway.
This is the primary entry point for all AI calls in the platform.
"""
import uuid
import logging
from typing import Any, Dict, Optional

from app.ai.policies.policy_engine import policy_engine
from app.ai.capabilities.capability_registry import capability_registry_manager

logger = logging.getLogger("backend.ai.capabilities.router")


class CapabilityRouter:
    """
    Routes a capability-named request through the policy engine and then
    into the AI Gateway. All platform components should call this instead
    of calling ai_gateway.generate_completion() directly with hard-coded providers.
    """

    async def route(
        self,
        capability: str,
        prompt: str,
        system_prompt: str = "",
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        plugin_id: Optional[str] = None,
        bypass_cache: bool = False,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        1. Resolve capability → {provider, model} via PolicyEngine
        2. Call AIGateway.generate_completion() with resolved provider/model
        3. Return augmented response with policy routing metadata
        """
        # Build routing context (policy conditions evaluation)
        routing_context = context or {}
        if org_id:
            routing_context["org_id"] = org_id

        # Ensure policy engine is initialized
        await policy_engine.initialize()

        # Resolve capability to provider+model
        resolution = await policy_engine.resolve(capability, routing_context)

        logger.info(
            f"CapabilityRouter: '{capability}' → {resolution.provider}/{resolution.model} "
            f"(policy={resolution.policy_id}, from={resolution.resolved_from})"
        )

        # Lazy import to avoid circular dependency
        from app.ai.gateway.gateway import ai_gateway

        correlation_id = f"cap_{capability}_{uuid.uuid4().hex[:10]}"

        result = await ai_gateway.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=resolution.provider,
            model=resolution.model,
            user_id=user_id,
            org_id=org_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            agent_id=agent_id,
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            bypass_cache=bypass_cache,
            # Pass capability and session context
            capability=capability,
            session_id=session_id,
        )

        # Augment result with routing metadata
        result["capability"] = capability
        result["policy_id"] = resolution.policy_id
        result["policy_name"] = resolution.policy_name
        result["resolved_from"] = resolution.resolved_from

        return result


capability_router = CapabilityRouter()
