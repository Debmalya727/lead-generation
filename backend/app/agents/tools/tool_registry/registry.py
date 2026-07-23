"""
Tool Registry for Phase 11 — Milestone 4: Autonomous Workflow & Tool Orchestration Engine.

Manages dynamic tool registration, auto-discovery, listing, and lookup.
"""
import logging
from typing import Dict, List, Type, Optional, Any
from app.agents.tools.base import BaseTool

logger = logging.getLogger("backend.agents.tools.registry")


class ToolRegistry:
    """Central registry tracking all available tools."""

    _registry: Dict[str, Type[BaseTool]] = {}

    @classmethod
    def register(cls, tool_cls: Type[BaseTool]) -> Type[BaseTool]:
        """Register a tool class in the registry."""
        tool_id = getattr(tool_cls, "tool_id", tool_cls.__name__.lower())
        cls._registry[tool_id] = tool_cls
        logger.info(f"ToolRegistry: Registered tool '{tool_id}' ({tool_cls.__name__})")
        return tool_cls

    @classmethod
    def unregister(cls, tool_id: str) -> None:
        """Unregister a tool by ID."""
        if tool_id in cls._registry:
            del cls._registry[tool_id]
            logger.info(f"ToolRegistry: Unregistered tool '{tool_id}'")

    @classmethod
    def get(cls, tool_id: str) -> Optional[BaseTool]:
        """Instantiate and return tool by tool_id."""
        cls.discover()
        tool_cls = cls._registry.get(tool_id)
        if tool_cls:
            return tool_cls()
        return None

    @classmethod
    def list_tools(cls) -> List[Dict[str, Any]]:
        """List all registered tools metadata."""
        cls.discover()
        tools_list = []
        for tool_id, tool_cls in cls._registry.items():
            instance = tool_cls()
            tools_list.append(instance.to_dict())
        return tools_list

    @classmethod
    def validate(cls, tool_id: str, inputs: Dict[str, Any]) -> bool:
        """Validate input payload against registered tool schema."""
        tool = cls.get(tool_id)
        if not tool:
            raise ValueError(f"Tool '{tool_id}' is not registered in ToolRegistry.")
        return tool.validate(inputs)

    @classmethod
    def discover(cls) -> None:
        """Auto-discover built-in tools."""
        modules = [
            "app.agents.tools.built_in.research_tool",
            "app.agents.tools.built_in.vector_search_tool",
            "app.agents.tools.built_in.memory_tool",
            "app.agents.tools.built_in.company_intelligence_tool",
            "app.agents.tools.built_in.lead_scoring_tool",
            "app.agents.tools.built_in.outreach_tool",
            "app.agents.tools.built_in.executive_report_tool",
            "app.agents.tools.built_in.artifact_tool",
            "app.agents.tools.built_in.message_bus_tool",
        ]
        for m in modules:
            try:
                __import__(m)
            except Exception as e:
                logger.warning(f"Error discovering tool module '{m}': {str(e)}")


def register_tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    """Decorator for auto-registering tool classes."""
    return ToolRegistry.register(cls)
