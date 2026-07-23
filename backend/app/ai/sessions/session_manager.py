"""
Session Manager for Phase 12.7B AI Gateway.
Creates and tracks per-request AI sessions with full telemetry.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database.mongodb.collections.ai_gateway_extended import AISessionDocument
from app.ai.sessions.schemas import AISessionCreate, AISessionUpdate

logger = logging.getLogger("backend.ai.sessions")


class SessionManager:
    """Creates and manages AI session lifecycle records."""

    async def create_session(self, data: AISessionCreate) -> AISessionDocument:
        """Create a new session document and return it."""
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        doc = AISessionDocument(
            session_id=session_id,
            conversation_id=data.conversation_id,
            workflow_id=data.workflow_id,
            user_id=data.user_id,
            org_id=data.org_id,
            agent_id=data.agent_id,
            capability=data.capability,
            provider=data.provider,
            model=data.model,
            streaming=data.streaming,
            status="active",
        )
        await doc.insert()
        logger.debug(f"SessionManager: Created session {session_id}")
        return doc

    async def update_session(self, session_id: str, update: AISessionUpdate) -> None:
        """Update session metrics after a completion."""
        doc = await AISessionDocument.find_one(AISessionDocument.session_id == session_id)
        if not doc:
            logger.warning(f"SessionManager: Session {session_id} not found for update.")
            return

        doc.prompt_tokens += update.prompt_tokens
        doc.completion_tokens += update.completion_tokens
        doc.total_tokens = doc.prompt_tokens + doc.completion_tokens
        doc.estimated_cost += update.estimated_cost
        doc.latency_ms = update.latency_ms
        doc.retry_count += update.retry_count
        doc.fallback_count += update.fallback_count
        doc.cached = update.cached

        if update.provider:
            doc.provider = update.provider
        if update.model:
            doc.model = update.model
        if update.guardrail_passed is not None:
            doc.guardrail_passed = update.guardrail_passed
        if update.guardrail_flags:
            doc.guardrail_flags.extend(update.guardrail_flags)
        if update.policy_id:
            doc.policy_id = update.policy_id
            doc.selected_policy = update.selected_policy
        if update.cache_key:
            doc.cache_references.append(update.cache_key)
        if update.prompt_hash:
            if update.prompt_hash not in doc.prompt_history:
                doc.prompt_history.append(update.prompt_hash)
                if len(doc.prompt_history) > 20:
                    doc.prompt_history = doc.prompt_history[-20:]

        await doc.save()

    async def close_session(self, session_id: str, status: str = "completed") -> None:
        """Mark session as completed or failed."""
        doc = await AISessionDocument.find_one(AISessionDocument.session_id == session_id)
        if doc:
            doc.status = status
            doc.completed_at = datetime.now(timezone.utc)
            await doc.save()
            logger.debug(f"SessionManager: Closed session {session_id} with status={status}")

    async def get_session(self, session_id: str) -> Optional[AISessionDocument]:
        """Retrieve a session by ID."""
        return await AISessionDocument.find_one(AISessionDocument.session_id == session_id)


session_manager = SessionManager()
