"""
BaseTool abstract interface for Phase 11 — Milestone 4: Autonomous Workflow & Tool Orchestration Engine.

All LeadForgeAI tools inherit from BaseTool.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseTool(ABC):
    """Abstract Base Class for all tools in LeadForgeAI Tool Registry."""

    tool_id: str
    name: str
    description: str
    category: str = "general"
    version: str = "1.0.0"
    
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    permissions: List[str] = []
    timeout: int = 60  # Default 60s timeout
    cost_estimate: float = 0.0  # Estimated cost in credits/dollars per run

    def validate(self, inputs: Dict[str, Any]) -> bool:
        """Validate input payload structure and required fields."""
        if not self.input_schema:
            return True
        required_fields = self.input_schema.get("required", [])
        for field in required_fields:
            if field not in inputs or inputs[field] is None:
                raise ValueError(f"Tool '{self.tool_id}' missing required input field: '{field}'")
        return True

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool logic and return normalized result payload."""
        pass

    async def health(self) -> Dict[str, Any]:
        """Check operational health status of tool dependencies."""
        return {
            "tool_id": self.tool_id,
            "status": "healthy",
            "version": self.version,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool metadata to dictionary representation."""
        return {
            "tool_id": getattr(self, "tool_id", self.__class__.__name__),
            "name": getattr(self, "name", self.__class__.__name__),
            "description": getattr(self, "description", ""),
            "category": getattr(self, "category", "general"),
            "version": getattr(self, "version", "1.0.0"),
            "input_schema": getattr(self, "input_schema", {}),
            "output_schema": getattr(self, "output_schema", {}),
            "permissions": getattr(self, "permissions", []),
            "timeout": getattr(self, "timeout", 60),
            "cost_estimate": getattr(self, "cost_estimate", 0.0),
        }
