"""
Dynamic Agent Registry for LeadForgeAI.

Enables runtime discovery, registration, lookup, and validation of AI agents without hardcoded imports.
"""
import logging
from typing import Dict, Type, List, Optional, Any

from app.agents.runtime.base_agent import BaseAgent

logger = logging.getLogger("backend.agents.registry")


class AgentRegistry:
    """Registry managing registered AI Agent classes."""

    _registry: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, agent_cls: Type[BaseAgent]) -> Type[BaseAgent]:
        """Register an agent class dynamically."""
        name = getattr(agent_cls, "name", agent_cls.__name__)
        agent_id = getattr(agent_cls, "agent_id", name.lower().replace(" ", "_"))

        if agent_id in cls._registry:
            logger.debug(f"Overwriting existing registered agent: {agent_id}")

        cls._registry[agent_id] = agent_cls
        logger.info(f"Registered AI Agent '{name}' (ID: '{agent_id}') in registry.")
        return agent_cls

    @classmethod
    def unregister(cls, agent_id: str) -> bool:
        """Unregister an agent by ID."""
        if agent_id in cls._registry:
            del cls._registry[agent_id]
            logger.info(f"Unregistered agent '{agent_id}'")
            return True
        return False

    @classmethod
    def discover(cls) -> None:
        """Auto-discover and import registered AI Agent modules."""
        modules_to_discover = [
            "app.agents.models.diagnostic_agent",
            "app.agents.business.research_agent",
            "app.agents.business.memory_agent",
            "app.agents.business.sales_strategy_agent",
            "app.agents.business.outreach_agent",
            "app.agents.business.review_agent",
            "app.agents.business.executive_agent",
        ]
        for module_path in modules_to_discover:
            try:
                __import__(module_path)
            except Exception as e:
                logger.warning(f"Error discovering agent module '{module_path}': {str(e)}")

    @classmethod
    def get(cls, agent_id: str) -> Optional[Type[BaseAgent]]:
        """Fetch agent class by ID or name."""
        cls.discover()
        # Check direct match by agent_id
        if agent_id in cls._registry:
            return cls._registry[agent_id]

        # Check by name matching
        normalized = agent_id.lower().strip().replace(" ", "_")
        for key, agent_cls in cls._registry.items():
            if key == normalized or getattr(agent_cls, "name", "").lower().replace(" ", "_") == normalized:
                return agent_cls

        return None

    @classmethod
    def list_agents(cls) -> List[Dict[str, Any]]:
        """List all registered agents and their capabilities."""
        agents_info = []
        for key, agent_cls in cls._registry.items():
            agents_info.append({
                "agent_id": key,
                "name": getattr(agent_cls, "name", agent_cls.__name__),
                "version": getattr(agent_cls, "version", "1.0.0"),
                "description": getattr(agent_cls, "description", ""),
                "capabilities": getattr(agent_cls, "capabilities", []),
            })
        return agents_info

    @classmethod
    def validate(cls, agent_id: str) -> bool:
        """Validate whether an agent exists in the registry."""
        return cls.get(agent_id) is not None


def register_agent(cls: Type[BaseAgent]) -> Type[BaseAgent]:
    """Decorator to register an AI agent class automatically."""
    return AgentRegistry.register(cls)
