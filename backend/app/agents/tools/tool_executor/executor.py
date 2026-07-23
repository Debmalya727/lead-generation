"""
ToolExecutor for Phase 11 — Milestone 4: Autonomous Workflow & Tool Orchestration Engine.

Manages tool execution lifecycle with:
- Schema validation
- Timeout enforcement
- Automatic retries
- Permission checks
- Cost tracking & execution log persistence
"""
import time
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.agents.tools.base import BaseTool
from app.agents.tools.tool_registry.registry import ToolRegistry
from app.database.mongodb.collections.agent_workflow import ToolExecutionDocument

logger = logging.getLogger("backend.agents.tools.executor")


class ToolExecutor:
    """Executor handling safe, monitored tool execution."""

    async def execute_tool(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
        invoker_agent: str = "System",
        execution_id: Optional[str] = None,
        step_id: Optional[str] = None,
        user_permissions: Optional[list] = None,
        max_retries: int = 1,
    ) -> Dict[str, Any]:
        """Validate, execute, track cost, and log tool invocation."""
        tool: Optional[BaseTool] = ToolRegistry.get(tool_id)
        if not tool:
            raise ValueError(f"Tool '{tool_id}' is not registered in ToolRegistry.")

        # 1. Check permissions
        if tool.permissions:
            if user_permissions is not None:
                missing = [p for p in tool.permissions if p not in user_permissions]
                if missing:
                    err_msg = f"Permission denied for tool '{tool_id}'. Required permissions: {missing}"
                    await self._log_execution(
                        tool_id=tool_id,
                        invoker=invoker_agent,
                        execution_id=execution_id,
                        step_id=step_id,
                        inputs=inputs,
                        outputs={},
                        status="permission_denied",
                        error=err_msg,
                    )
                    raise PermissionError(err_msg)

        # 2. Validate inputs
        tool.validate(inputs)

        # 3. Execute with retries & timeout
        timeout_sec = tool.timeout or 60
        last_error = None
        start_t = time.time()

        for attempt in range(1, max_retries + 2):
            try:
                logger.info(f"ToolExecutor running tool '{tool_id}' (attempt {attempt}/{max_retries+1})")
                outputs = await asyncio.wait_for(tool.execute(inputs), timeout=float(timeout_sec))
                duration = round(time.time() - start_t, 3)

                # Persist successful execution log
                await self._log_execution(
                    tool_id=tool_id,
                    invoker=invoker_agent,
                    execution_id=execution_id,
                    step_id=step_id,
                    inputs=inputs,
                    outputs=outputs,
                    status="success",
                    duration=duration,
                    cost=tool.cost_estimate,
                )

                return {
                    "status": "success",
                    "tool_id": tool_id,
                    "outputs": outputs,
                    "execution_time_seconds": duration,
                    "cost_estimate": tool.cost_estimate,
                }
            except asyncio.TimeoutError:
                last_error = f"Tool '{tool_id}' timed out after {timeout_sec}s."
                logger.warning(last_error)
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Tool '{tool_id}' execution exception on attempt {attempt}: {last_error}")

        duration = round(time.time() - start_t, 3)
        await self._log_execution(
            tool_id=tool_id,
            invoker=invoker_agent,
            execution_id=execution_id,
            step_id=step_id,
            inputs=inputs,
            outputs={},
            status="error",
            duration=duration,
            cost=0.0,
            error=last_error,
        )

        return {
            "status": "error",
            "tool_id": tool_id,
            "error_message": last_error,
            "outputs": {},
            "execution_time_seconds": duration,
            "cost_estimate": 0.0,
        }

    async def _log_execution(
        self,
        tool_id: str,
        invoker: str,
        execution_id: Optional[str],
        step_id: Optional[str],
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        status: str,
        duration: float = 0.0,
        cost: float = 0.0,
        error: Optional[str] = None,
    ) -> None:
        """Persist tool execution record to MongoDB."""
        import uuid
        try:
            doc = ToolExecutionDocument(
                tool_execution_id=f"toolex_{uuid.uuid4().hex[:12]}",
                tool_id=tool_id,
                execution_id=execution_id,
                step_id=step_id,
                invoker_agent=invoker,
                inputs=inputs,
                outputs=outputs,
                status=status,
                execution_time_seconds=duration,
                cost_estimate=cost,
                error_message=error,
                timestamp=datetime.now(timezone.utc),
            )
            await doc.insert()
        except Exception as e:
            logger.warning(f"Failed to persist ToolExecutionDocument: {str(e)}")
