"""
Coordination package for Multi-Agent Collaboration Engine.
"""
from app.agents.collaboration.coordination.manager import CollaborationManager
from app.agents.collaboration.coordination.dynamic_dag import DynamicDAGManager

__all__ = ["CollaborationManager", "DynamicDAGManager"]
