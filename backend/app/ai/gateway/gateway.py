"""
AIGateway orchestrating Phase 12.7A/12.7B Enterprise AI Gateway lifecycle:
- Request/Response validation
- Cache lookup & Semantic caching
- Fallback & Failover execution policy
- Token counting & Dollar cost recording
- Trace correlation logging
- [12.7B] Session tracking, Guardrail validation, Memory storage
"""
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, AsyncGenerator

from app.ai.registry.provider_registry import ProviderRegistry
from app.ai.registry.model_registry import ModelRegistry
from app.ai.cache.ai_cache import ai_cache
from app.ai.router.fallback import fallback_engine
from app.ai.cost.token_manager import token_manager
from app.ai.cost.cost_tracker import cost_tracker
from app.ai.tools.tool_registry import tool_registry
from app.ai.tools.tool_sandbox import tool_sandbox
from app.database.mongodb.collections.ai_gateway import AIRequestDocument, AIResponseDocument

logger = logging.getLogger("backend.ai.gateway")


class AIGateway:
    """Master Gateway Orchestrator for all LLM completions."""

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        provider: str = "gemini",
        model: str = "gemini-1.5-flash",
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        plugin_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        bypass_cache: bool = False,
        # Phase 12.7B extended parameters (optional, backward-compatible)
        capability: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes chat completions with full gateway security,
        semantic cache checks, fallback execution, and cost logging.
        """
        start_t = time.time()
        correlation_id = correlation_id or f"corr_ai_{uuid.uuid4().hex[:12]}"

        # 1. Validate inputs
        if not prompt:
            raise ValueError("Prompt content cannot be empty.")

        # 2. Record request in MongoDB
        req_doc = AIRequestDocument(
            correlation_id=correlation_id,
            user_id=user_id,
            org_id=org_id,
            conversation_id=conversation_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
            plugin_id=plugin_id,
            prompt=prompt,
            system_prompt=system_prompt,
            provider=provider,
            model=model,
        )
        await req_doc.insert()

        # 3. Check Cache
        if not bypass_cache:
            # First check exact response cache
            cached_resp = await ai_cache.get_response(prompt, system_prompt, model)
            if cached_resp:
                latency = round((time.time() - start_t) * 1000, 2)
                # Save Response Doc
                resp_doc = AIResponseDocument(
                    correlation_id=correlation_id,
                    response_text=cached_resp,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    estimated_cost=0.0,
                    latency_ms=latency,
                    provider_used="cache",
                    model_used=model,
                    cached=True,
                )
                await resp_doc.insert()
                return resp_doc.model_dump()

            # Second check semantic cache
            semantic_resp = await ai_cache.get_semantic_response(prompt, system_prompt, model)
            if semantic_resp:
                latency = round((time.time() - start_t) * 1000, 2)
                resp_doc = AIResponseDocument(
                    correlation_id=correlation_id,
                    response_text=semantic_resp,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    estimated_cost=0.0,
                    latency_ms=latency,
                    provider_used="semantic_cache",
                    model_used=model,
                    cached=True,
                )
                await resp_doc.insert()
                return resp_doc.model_dump()

        # 4. Route through FallbackEngine with CircuitBreaker, HealthManager, and RetryEngine
        async def execute_adapter(prov: str, mod: str) -> str:
            from app.ai.resilience.circuit_breaker import circuit_breaker_registry
            from app.ai.resilience.retry_engine import retry_engine
            from app.ai.gateway.health_manager import provider_health_manager

            if not circuit_breaker_registry.allow_request(prov):
                raise RuntimeError(f"Circuit breaker for provider '{prov}' is OPEN. Requests blocked.")

            adapter_cls = ProviderRegistry.get_provider_class(prov)
            if not adapter_cls:
                raise ValueError(f"Provider '{prov}' has no adapter registered in ProviderRegistry.")
            
            base_url = ""
            if prov == "openrouter":
                base_url = "https://openrouter.ai/api/v1"
            elif prov == "ollama":
                base_url = "http://localhost:11434"
            
            from typing import Any
            adapter_cls_cast: Any = adapter_cls
            adapter_inst = adapter_cls_cast(model=mod, base_url=base_url)

            call_start = time.time()
            try:
                text = await retry_engine.execute_with_retry(
                    func=lambda: adapter_inst.complete(prompt, system_prompt),
                    provider=prov,
                )
                call_lat = round((time.time() - call_start) * 1000, 2)
                circuit_breaker_registry.record_success(prov)
                provider_health_manager.record_success(prov, call_lat)
                return text
            except Exception as call_err:
                call_lat = round((time.time() - call_start) * 1000, 2)
                circuit_breaker_registry.record_failure(prov, call_err)
                provider_health_manager.record_failure(prov, call_err, call_lat)
                raise call_err

        run_result = await fallback_engine.execute_with_fallback(
            primary_provider=provider,
            primary_model=model,
            api_call_func=execute_adapter,
            prompt=prompt,
            system_prompt=system_prompt,
        )

        latency = round((time.time() - start_t) * 1000, 2)
        response_text = run_result["response_text"]
        actual_provider = run_result["provider_used"]
        actual_model = run_result["model_used"]

        # 5. Count Tokens & Cost
        p_tokens = token_manager.count_tokens(prompt + system_prompt)
        c_tokens = token_manager.count_tokens(response_text)
        cost = cost_tracker.calculate_cost(p_tokens, c_tokens, actual_model)

        # 6. Save Response in Cache
        if not bypass_cache and run_result["success"]:
            ai_cache.set_response(prompt, response_text, system_prompt, model)

        # 7. Record usage telemetry in DB
        await token_manager.record_usage(
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            user_id=user_id,
            org_id=org_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            agent_id=agent_id,
            plugin_id=plugin_id,
        )
        await cost_tracker.record_cost(
            cost=cost,
            user_id=user_id,
            org_id=org_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            agent_id=agent_id,
            plugin_id=plugin_id,
        )

        # 8. Record Response in MongoDB
        resp_doc = AIResponseDocument(
            correlation_id=correlation_id,
            response_text=response_text,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=p_tokens + c_tokens,
            estimated_cost=cost,
            latency_ms=latency,
            provider_used=actual_provider,
            model_used=actual_model,
            retry_count=run_result["retry_count"],
            fallback_count=run_result["fallback_count"],
        )
        await resp_doc.insert()

        result = resp_doc.model_dump()

        # 9. [Phase 12.7B] If session_id provided, store memory (non-blocking)
        if session_id or capability:
            try:
                from app.ai.memory.memory_manager import memory_manager
                await memory_manager.store(
                    prompt=prompt,
                    session_id=session_id,
                    user_id=user_id,
                    org_id=org_id,
                    workflow_id=workflow_id,
                    conversation_id=conversation_id,
                    tags=[capability] if capability else [],
                )
            except Exception as mem_err:
                logger.debug(f"AIGateway: Memory store skipped: {mem_err}")

        return result

    async def generate_completion_extended(
        self,
        prompt: str,
        system_prompt: str = "",
        provider: str = "gemini",
        model: str = "gemini-1.5-flash",
        capability: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        plugin_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        bypass_cache: bool = False,
        guardrail_config: Optional[Dict[str, Any]] = None,
        store_memory: bool = True,
    ) -> Dict[str, Any]:
        """
        Phase 12.7B Extended entry point.
        Adds: Session tracking, Guardrail validation, Memory storage.
        Use this for capability-routed calls from CapabilityRouter.
        """
        correlation_id = correlation_id or f"corr_ext_{uuid.uuid4().hex[:12]}"

        # Lazy imports to avoid circular dependencies
        from app.ai.sessions.session_manager import session_manager
        from app.ai.sessions.schemas import AISessionCreate, AISessionUpdate
        from app.ai.guardrails.guardrail_engine import guardrail_engine
        from app.ai.memory.memory_manager import memory_manager

        # Create session
        session_doc = await session_manager.create_session(AISessionCreate(
            conversation_id=conversation_id,
            workflow_id=workflow_id,
            user_id=user_id,
            org_id=org_id,
            agent_id=agent_id,
            capability=capability,
            provider=provider,
            model=model,
        ))
        active_session_id = session_id or session_doc.session_id

        # Execute via base generate_completion
        result = await self.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            provider=provider,
            model=model,
            user_id=user_id,
            org_id=org_id,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            agent_id=agent_id,
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            bypass_cache=bypass_cache,
            capability=capability,
            session_id=active_session_id,
        )

        response_text = result.get("response_text", "")

        # Run Guardrails
        guardrail_result = await guardrail_engine.validate_and_log(
            response_text=response_text,
            correlation_id=correlation_id,
            session_id=active_session_id,
            config=guardrail_config,
        )

        # Update session with results
        await session_manager.update_session(active_session_id, AISessionUpdate(
            prompt_tokens=result.get("prompt_tokens", 0),
            completion_tokens=result.get("completion_tokens", 0),
            estimated_cost=result.get("estimated_cost", 0.0),
            latency_ms=result.get("latency_ms", 0.0),
            retry_count=result.get("retry_count", 0),
            fallback_count=result.get("fallback_count", 0),
            cached=result.get("cached", False),
            provider=result.get("provider_used", provider),
            model=result.get("model_used", model),
            guardrail_passed=guardrail_result.passed,
            guardrail_flags=guardrail_result.flags,
        ))
        await session_manager.close_session(active_session_id)

        # Store memory record
        if store_memory:
            try:
                await memory_manager.store(
                    prompt=prompt,
                    session_id=active_session_id,
                    user_id=user_id,
                    org_id=org_id,
                    workflow_id=workflow_id,
                    conversation_id=conversation_id,
                    tags=[capability] if capability else [],
                )
            except Exception as e:
                logger.warning(f"AIGateway: Memory store failed (non-blocking): {str(e)}")

        # Augment result
        result["session_id"] = active_session_id
        result["capability"] = capability
        result["guardrail_passed"] = guardrail_result.passed
        result["guardrail_flags"] = guardrail_result.flags
        result["hallucination_score"] = guardrail_result.hallucination_score
        result["pii_detected"] = guardrail_result.pii_detected

        return result

    async def execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_scopes: Optional[List[str]] = None,
        correlation_id: str = "corr_gateway_tool",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes an AI tool call exclusively through the sandboxed execution bridge.
        Direct tool execution is forbidden.
        """
        logger.info(f"[AIGateway] Routing tool call '{tool_name}' through ToolSandbox...")
        return await tool_sandbox.execute_tool(
            tool_name=tool_name,
            arguments=arguments,
            user_scopes=user_scopes,
            correlation_id=correlation_id,
            user_id=user_id,
        )


# Global singleton instance
ai_gateway = AIGateway()
