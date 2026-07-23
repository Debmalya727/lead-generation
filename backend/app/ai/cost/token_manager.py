"""
TokenManager for Phase 12.7A Enterprise AI Gateway.
Estimates token counts for inputs/outputs and updates MongoDB usage documents.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database.mongodb.collections.ai_gateway import TokenUsageDocument

logger = logging.getLogger("backend.ai.token_manager")


class TokenManager:
    """Manages token estimation and accumulation database updates."""

    def count_tokens(self, text: str) -> int:
        """Estimate token count for a text block (rough character-ratio approximation)."""
        if not text:
            return 0
        # Check if tiktoken is available
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # Fallback estimation: average 4 chars per token
            return max(1, len(text) // 4)

    async def record_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        embedding_tokens: int = 0,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        plugin_id: Optional[str] = None,
    ) -> None:
        """Accumulates usage statistics in TokenUsageDocument."""
        total = prompt_tokens + completion_tokens + embedding_tokens
        if total == 0:
            return

        targets = []
        if user_id:
            targets.append(("user", user_id))
        if org_id:
            targets.append(("organization", org_id))
        if workflow_id:
            targets.append(("workflow", workflow_id))
        if conversation_id:
            targets.append(("conversation", conversation_id))
        if agent_id:
            targets.append(("agent", agent_id))
        if plugin_id:
            targets.append(("plugin", plugin_id))

        for id_type, id_val in targets:
            try:
                doc = await TokenUsageDocument.find_one(
                    TokenUsageDocument.identifier_type == id_type,
                    TokenUsageDocument.identifier_id == id_val
                )
                if not doc:
                    doc = TokenUsageDocument(
                        identifier_type=id_type,
                        identifier_id=id_val,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        embedding_tokens=embedding_tokens,
                        total_tokens=total,
                        updated_at=datetime.now(timezone.utc),
                    )
                    await doc.insert()
                else:
                    doc.prompt_tokens += prompt_tokens
                    doc.completion_tokens += completion_tokens
                    doc.embedding_tokens += embedding_tokens
                    doc.total_tokens += total
                    doc.updated_at = datetime.now(timezone.utc)
                    await doc.save()
            except Exception as e:
                logger.warning(f"Failed to record token usage for {id_type}:{id_val}: {str(e)}")


token_manager = TokenManager()
