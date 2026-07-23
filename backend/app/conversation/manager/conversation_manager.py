"""
ConversationManager for Phase 12: Enterprise Conversational CRM.

Master orchestrator binding SessionManager, IntentClassifier, EntityExtractor,
ClarificationEngine, ConversationMemoryManager, ConversationPlanner, and ResponseEngine.
"""
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from bson import ObjectId

from app.conversation.sessions.session_manager import SessionManager
from app.conversation.intent.classifier import IntentClassifier
from app.conversation.intent.entity_extractor import EntityExtractor
from app.conversation.intent.clarification_engine import ClarificationEngine
from app.conversation.memory.conversation_memory import ConversationMemoryManager
from app.conversation.planner.planner import ConversationPlanner
from app.conversation.response.response_engine import ResponseEngine
from app.database.mongodb.collections.agent_conversation import (
    ConversationSessionDocument,
    ConversationMessageDocument,
)

logger = logging.getLogger("backend.conversation.manager")


class ConversationManager:
    """Master manager for conversational enterprise sales interactions."""

    def __init__(self):
        self.session_manager = SessionManager()
        self.classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.clarification_engine = ClarificationEngine()
        self.memory_manager = ConversationMemoryManager()
        self.planner = ConversationPlanner()
        self.response_engine = ResponseEngine()

    async def process_user_message(
        self,
        owner_id: str,
        user_text: str,
        session_id: Optional[str] = None,
        company_override: Optional[str] = None,
    ) -> Tuple[ConversationMessageDocument, ConversationSessionDocument]:
        """
        Process a user natural language input or slash command:
        1. Resolve / Create Session
        2. Persist User Message
        3. Intent & Entity Extraction
        4. Memory Update
        5. Check Clarification
        6. Plan & Execute via Workflow Engine
        7. Format AI Response & Action Cards
        8. Persist Assistant Message
        """
        owner_obj_id = ObjectId(owner_id) if ObjectId.is_valid(owner_id) else ObjectId()

        # 1. Resolve Session
        if not session_id:
            session = await self.session_manager.create_session(owner_id=owner_id, title=user_text[:30])
            session_id = session.session_id
        else:
            session = await self.session_manager.get_session(session_id, owner_id)
            if not session:
                session = await self.session_manager.create_session(owner_id=owner_id, title=user_text[:30])
                session_id = session.session_id

        # 2. Persist User Message
        user_msg_doc = ConversationMessageDocument(
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            owner_id=owner_obj_id,
            role="user",
            content=user_text,
            timestamp=datetime.now(timezone.utc),
        )
        await user_msg_doc.insert()

        # 3. Intent & Entity Extraction
        mem_doc = await self.memory_manager.get_memory(session_id, owner_id)
        classification = self.classifier.classify(user_text)
        intent = classification["intent"]
        confidence = classification["confidence"]
        slash_cmd = classification.get("slash_command")

        context_mem = {"current_company": mem_doc.current_company}
        entities = self.entity_extractor.extract(user_text, context_mem)
        if company_override:
            entities["company_name"] = company_override

        company_name = entities.get("company_name", mem_doc.current_company or "Target Company")

        # 4. Update Memory
        if company_name and company_name != "Target Company":
            await self.memory_manager.update_memory(session_id, owner_id, current_company=company_name)

        # 5. Check Clarification
        needs_clarification, missing, prompt = self.clarification_engine.check_clarification(intent, entities)

        execution_doc = None
        exec_id = None
        exec_vis = {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "planner_stage": "WorkflowEngine Plan Generation",
        }

        # 6. Plan & Execute via Workflow Engine (if clarification not needed)
        if not needs_clarification and intent != "general_question":
            template_id, execution_doc, plan_summary = await self.planner.plan_and_execute(
                intent=intent,
                entities=entities,
                owner_id=owner_id,
                slash_command=slash_cmd,
            )
            exec_id = execution_doc.execution_id
            exec_vis["execution_id"] = exec_id
            exec_vis["workflow_status"] = execution_doc.status
            exec_vis["progress"] = execution_doc.progress

            await self.memory_manager.update_memory(session_id, owner_id, workflow_id=template_id)

        # 7. Format AI Response & Action Cards
        md_text, action_cards, res_confidence = self.response_engine.format_response(
            intent=intent,
            company_name=company_name,
            execution_doc=execution_doc,
            clarification_prompt=prompt if needs_clarification else None,
        )

        # 8. Persist Assistant Message
        assistant_msg_doc = ConversationMessageDocument(
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            owner_id=owner_obj_id,
            role="assistant",
            content=md_text,
            intent=intent,
            confidence=res_confidence,
            entities=entities,
            execution_id=exec_id,
            action_cards=[c.model_dump() if hasattr(c, 'model_dump') else dict(c) for c in action_cards],
            execution_visualization=exec_vis,
            timestamp=datetime.now(timezone.utc),
        )
        await assistant_msg_doc.insert()

        # Update session metadata
        session.message_count += 2
        session.last_intent = intent
        session.active_company_name = company_name
        if session.title == "New Conversation" and len(user_text) > 0:
            session.title = user_text[:30]
        session.updated_at = datetime.now(timezone.utc)
        await session.save()

        return assistant_msg_doc, session

    async def get_history(self, session_id: str, limit: int = 50) -> List[ConversationMessageDocument]:
        """Fetch chronological message history for a session."""
        return await ConversationMessageDocument.find(
            ConversationMessageDocument.session_id == session_id
        ).sort("timestamp").limit(limit).to_list()
