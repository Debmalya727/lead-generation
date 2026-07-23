"""
Consensus package for Multi-Agent Collaboration Engine.
"""
from app.agents.collaboration.consensus.engine import ConsensusEngine
from app.agents.collaboration.consensus.conflict_detector import ConflictDetector

__all__ = ["ConsensusEngine", "ConflictDetector"]
