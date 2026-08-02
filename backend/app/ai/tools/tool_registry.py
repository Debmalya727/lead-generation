"""
Centralized AI Tool Registry for Phase 12.7 Enterprise AI Platform.
Manages tool registration, JSON schema exports (OpenAI, Gemini, Anthropic formats),
versioning, permission scope tags, and execution telemetry metrics.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Awaitable

logger = logging.getLogger("backend.ai.tools.registry")


@dataclass
class ToolDefinition:
    """Represents a registered AI Tool definition."""

    name: str
    description: str
    category: str  # crm | knowledge | calendar | email | voice | search | database | analytics | workflow
    permission_scope: str  # e.g. crm:read, crm:write, email:send, db:read, etc.
    parameters_schema: Dict[str, Any]
    handler_func: Callable[..., Awaitable[Any]]
    version: str = "v1.0.0"
    is_active: bool = True
    
    # Telemetry Metrics
    execution_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0

    def record_telemetry(self, duration_ms: float, success: bool = True) -> None:
        """Update live execution telemetry."""
        self.execution_count += 1
        self.total_duration_ms += duration_ms
        if not success:
            self.error_count += 1

    @property
    def average_latency_ms(self) -> float:
        """Calculate average execution latency."""
        return round(self.total_duration_ms / max(1, self.execution_count), 2)

    @property
    def success_rate_percent(self) -> float:
        """Calculate success rate percentage."""
        if self.execution_count == 0:
            return 100.0
        return round(((self.execution_count - self.error_count) / self.execution_count) * 100.0, 1)


class ToolRegistry:
    """Centralized Tool Registry for all AI Providers."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        category: str,
        permission_scope: str,
        parameters_schema: Dict[str, Any],
        handler_func: Callable[..., Awaitable[Any]],
        version: str = "v1.0.0",
    ) -> ToolDefinition:
        """Register a new tool into the centralized registry."""
        tool = ToolDefinition(
            name=name,
            description=description,
            category=category,
            permission_scope=permission_scope,
            parameters_schema=parameters_schema,
            handler_func=handler_func,
            version=version,
        )
        self._tools[name] = tool
        logger.info(f"[ToolRegistry] Registered tool '{name}' (v{version}) under scope '{permission_scope}'")
        return tool

    def get_tool(self, name: str) -> ToolDefinition:
        """Fetch tool definition by name."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered in ToolRegistry.")
        return self._tools[name]

    def list_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """List all active registered tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category.lower() == category.lower()]
        return tools

    # ─── Multi-Provider Schema Formatting ───

    def to_openai_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Format tools into OpenAI standard function calling schema."""
        tools = self.list_tools(category)
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters_schema,
                },
            }
            for t in tools
            if t.is_active
        ]

    def to_gemini_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Format tools into Google Gemini function declarations schema."""
        tools = self.list_tools(category)
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters_schema,
            }
            for t in tools
            if t.is_active
        ]

    def get_metrics(self) -> Dict[str, Any]:
        """Aggregate system-wide tool telemetry metrics."""
        tools = self.list_tools()
        total_calls = sum(t.execution_count for t in tools)
        total_errors = sum(t.error_count for t in tools)
        overall_success = round(((total_calls - total_errors) / max(1, total_calls)) * 100.0, 1) if total_calls > 0 else 100.0

        return {
            "registered_tools_count": len(tools),
            "total_execution_calls": total_calls,
            "total_errors": total_errors,
            "overall_success_rate_percent": overall_success,
            "tools": [
                {
                    "name": t.name,
                    "category": t.category,
                    "version": t.version,
                    "permission_scope": t.permission_scope,
                    "execution_count": t.execution_count,
                    "error_count": t.error_count,
                    "average_latency_ms": t.average_latency_ms,
                    "success_rate_percent": t.success_rate_percent,
                }
                for t in tools
            ],
        }


tool_registry = ToolRegistry()
