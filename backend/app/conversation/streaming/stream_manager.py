"""
ChatStreamingManager for Phase 12: Enterprise Conversational CRM.

Generates real-time Server-Sent Events (SSE) streaming updates for conversation stages.
"""
import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional

logger = logging.getLogger("backend.conversation.streaming")


class ChatStreamingManager:
    """Manager handling real-time SSE event streaming for chat interactions."""

    async def stream_chat_response(
        self,
        session_id: str,
        user_message: str,
        company_name: str = "Target Company",
        intent: str = "company_research",
        final_markdown: str = "",
        action_cards: Optional[list] = None,
        execution_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Yield SSE formatted string events simulating agent stages:
        Thinking -> Planning -> Executing Workflow -> Complete
        """
        # Event 1: Thinking...
        yield self._format_sse("thinking", {"stage": "Thinking...", "details": "Classifying intent & extracting entities"})
        await asyncio.sleep(0.3)

        # Event 2: Planning...
        yield self._format_sse("planning", {"stage": "Planning...", "intent": intent, "details": f"Constructing Workflow plan for '{company_name}'"})
        await asyncio.sleep(0.4)

        # Event 3: Executing Workflow...
        yield self._format_sse("executing", {"stage": "Executing Workflow...", "execution_id": execution_id, "details": "Workflow Engine orchestrating tools & agents"})
        await asyncio.sleep(0.5)

        # Event 4: Complete
        yield self._format_sse("complete", {
            "stage": "Complete",
            "session_id": session_id,
            "content": final_markdown,
            "action_cards": [c.model_dump() if hasattr(c, 'model_dump') else dict(c) for c in (action_cards or [])],
            "execution_id": execution_id,
        })

    def _format_sse(self, event: str, data: Dict[str, Any]) -> str:
        """Format payload into SSE protocol standard event."""
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"
