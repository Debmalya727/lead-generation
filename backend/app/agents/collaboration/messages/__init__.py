"""
Agent messaging package for Multi-Agent Collaboration Engine.
"""
from app.agents.collaboration.messages.message import AgentMessage
from app.agents.collaboration.messages.bus import AgentMessageBus

__all__ = ["AgentMessage", "AgentMessageBus"]
