"""
Abstract Base Class for Enterprise AI Agents.

Every agent in LeadForgeAI must inherit `BaseAgent` and implement its lifecycle hooks:
- initialize(context)
- plan(context)
- execute(context)
- validate(context)
- finish(context)
- cleanup(context)
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.agents.runtime.result import AgentResult
from app.agents.runtime.context import ExecutionContext

logger = logging.getLogger("backend.agents.base_agent")


class BaseAgent(ABC):
    """Abstract Base Class for all AI Agents in LeadForgeAI."""

    agent_id: str = "base_agent"
    name: str = "Base Agent"
    version: str = "1.0.0"
    description: str = "Abstract base agent template"
    capabilities: List[str] = []

    def __init__(self):
        self.status: str = "initialized"
        self.confidence: int = 100
        self.execution_time: float = 0.0
        self.artifacts: List[Dict[str, Any]] = []
        self.logs: List[str] = []

    def log(self, message: str):
        """Record a structured execution log line."""
        entry = f"[{self.name}] {message}"
        self.logs.append(entry)
        logger.info(entry)

    async def initialize(self, context: ExecutionContext) -> None:
        """Lifecycle Hook 1: Initialize resources and validate context."""
        self.log(f"Initializing agent '{self.name}' for job '{context.job_id}'")
        self.status = "running"

    async def plan(self, context: ExecutionContext) -> Dict[str, Any]:
        """Lifecycle Hook 2: Prepare internal step-by-step strategy."""
        self.log("Planning task execution strategy...")
        return {"strategy": "default_execution"}

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> AgentResult:
        """Lifecycle Hook 3: Core agent execution logic (Abstract)."""
        raise NotImplementedError

    async def validate(self, result: AgentResult, context: ExecutionContext) -> bool:
        """Lifecycle Hook 4: Validate execution result outputs."""
        self.log(f"Validating agent result: status={result.status}")
        return result.status == "completed"

    async def finish(self, result: AgentResult, context: ExecutionContext) -> AgentResult:
        """Lifecycle Hook 5: Consolidate final outputs and artifacts."""
        self.log(f"Finishing agent execution for '{self.name}'")
        self.status = result.status
        self.confidence = result.confidence
        return result

    async def cleanup(self, context: ExecutionContext) -> None:
        """Lifecycle Hook 6: Clean up resources and temporary state."""
        self.log(f"Cleaning up agent '{self.name}'")

    async def run(self, context: ExecutionContext) -> AgentResult:
        """Template method orchestrating standard lifecycle execution."""
        start_time = time.time()
        try:
            await self.initialize(context)
            await self.plan(context)
            
            result = await self.execute(context)
            
            is_valid = await self.validate(result, context)
            if not is_valid:
                result.status = "failed"
                result.messages.append("Validation check failed for agent outputs.")
            
            final_result = await self.finish(result, context)
            return final_result
        except Exception as e:
            self.log(f"Unhandled exception in agent '{self.name}': {str(e)}")
            return AgentResult(
                status="failed",
                confidence=0,
                messages=[f"Agent execution error: {str(e)}"],
                logs=self.logs,
                artifacts=self.artifacts,
                outputs={"error": str(e)},
            )
        finally:
            self.execution_time = time.time() - start_time
            await self.cleanup(context)
