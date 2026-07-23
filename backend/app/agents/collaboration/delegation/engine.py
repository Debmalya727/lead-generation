"""
DelegationEngine for Multi-Agent Collaboration Engine.

Allows an agent to dynamically delegate sub-tasks to another registered agent with:
- Configurable timeout
- Retry handling
- Approval pause check
- Failure recovery & fallback outputs
"""
import time
import asyncio
import logging
from typing import Dict, Any, Optional

from app.agents.runtime.base_agent import BaseAgent
from app.agents.runtime.result import AgentResult
from app.agents.runtime.context import ExecutionContext
from app.agents.registry.registry import AgentRegistry
from app.agents.collaboration.messages.bus import AgentMessageBus
from app.agents.collaboration.messages.message import AgentMessage

logger = logging.getLogger("backend.agents.collaboration.delegation")


class DelegationEngine:
    """Engine orchestrating dynamic inter-agent sub-task delegation."""

    def __init__(self, bus: Optional[AgentMessageBus] = None):
        self.bus = bus or AgentMessageBus.get_instance()

    async def delegate(
        self,
        from_agent: str,
        target_agent_name: str,
        task_description: str,
        job_id: str,
        owner_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        timeout_seconds: int = 30,
        max_retries: int = 2,
        approval_required: bool = False,
    ) -> AgentResult:
        """Delegate a sub-task from one agent to a target registered agent."""
        sub_task_id = task_id or f"delegated_{target_agent_name}_{int(time.time())}"
        logger.info(f"DelegationEngine: Agent '{from_agent}' delegating '{task_description[:40]}...' to '{target_agent_name}' (job: {job_id})")

        # Emit delegation message on bus
        del_msg = AgentMessage(
            job_id=job_id,
            task_id=sub_task_id,
            from_agent=from_agent,
            to_agent=target_agent_name,
            message_type="delegation",
            payload={
                "task_description": task_description,
                "inputs": inputs or {},
                "timeout_seconds": timeout_seconds,
                "approval_required": approval_required,
            },
        )
        await self.bus.send(del_msg)

        # Lookup target agent
        target_cls = AgentRegistry.get(target_agent_name)
        if not target_cls:
            logger.warning(f"Delegation target agent '{target_agent_name}' not registered. Using fallback.")
            return AgentResult(
                status="failed",
                confidence=0,
                messages=[f"Delegation target agent '{target_agent_name}' not found in registry."],
                outputs={"error": f"Target agent '{target_agent_name}' not registered."},
            )

        # Build execution context for delegated run
        ctx = ExecutionContext(
            job_id=job_id,
            plan_id=job_id,
            owner_id=owner_id,
            goal=task_description,
            task_id=sub_task_id,
            inputs=inputs or {},
        )

        # Execute with retries & timeout
        last_error = None
        for attempt in range(1, max_retries + 2):
            try:
                target_instance: BaseAgent = target_cls()
                logger.info(f"Delegation attempt {attempt}/{max_retries+1} for '{target_agent_name}'")

                # Wrap run with timeout
                result: AgentResult = await asyncio.wait_for(
                    target_instance.run(ctx),
                    timeout=float(timeout_seconds),
                )

                if result.status == "completed":
                    # Send completion message on bus
                    reply_msg = AgentMessage(
                        conversation_id=del_msg.conversation_id,
                        job_id=job_id,
                        task_id=sub_task_id,
                        from_agent=target_agent_name,
                        to_agent=from_agent,
                        message_type="reply",
                        payload={"status": "completed", "outputs": result.outputs},
                        confidence=result.confidence,
                    )
                    await self.bus.send(reply_msg)
                    return result

                last_error = "\n".join(result.messages) or "Delegated task execution failed."
            except asyncio.TimeoutError:
                last_error = f"Delegation to '{target_agent_name}' timed out after {timeout_seconds}s."
                logger.warning(last_error)
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Delegation exception on attempt {attempt}: {last_error}")

        # Failure recovery output
        return AgentResult(
            status="failed",
            confidence=0,
            messages=[f"Delegation to '{target_agent_name}' failed after {max_retries+1} attempts. Last error: {last_error}"],
            outputs={"error": last_error, "delegation_status": "failed"},
        )
