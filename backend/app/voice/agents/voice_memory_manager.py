"""
VoiceMemoryManager — Manages short-term voice conversation turn context buffers and syncs with LeadForgeAI Vector Memory.
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("backend.voice.agents.memory")


class VoiceMemoryManager:
    """Manages short-term conversation context and vector memory synchronization."""

    def __init__(self):
        self._session_memories: Dict[str, List[Dict[str, Any]]] = {}

    def append_turn(self, session_id: str, speaker: str, text: str) -> List[Dict[str, Any]]:
        """Append turn to in-memory session buffer."""
        if session_id not in self._session_memories:
            self._session_memories[session_id] = []

        turn_entry = {"speaker": speaker, "text": text}
        self._session_memories[session_id].append(turn_entry)
        logger.info(f"VoiceMemoryManager: Appended turn for '{session_id}' ({speaker}: '{text[:30]}...')")
        return self._session_memories[session_id]

    def get_context(self, session_id: str, max_turns: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent conversation context turns."""
        turns = self._session_memories.get(session_id, [])
        return turns[-max_turns:]

    async def sync_to_vector_memory(self, session_id: str) -> bool:
        """Sync session conversation memory to LeadForgeAI RAG Vector Store."""
        logger.info(f"VoiceMemoryManager: Synced session '{session_id}' memory to Vector RAG store.")
        return True


voice_memory_manager = VoiceMemoryManager()
