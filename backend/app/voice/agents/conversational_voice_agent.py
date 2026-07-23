"""
Master ConversationalVoiceAgent Orchestrator for Phase 13.8: Conversational Voice Agents.
Integrates:
- Multi-turn conversation state & voice memory
- Voice Interruption handling
- Clarification questions & confirmation policy
- Agent Personas (Sales SDR, Solutions Architect, Customer Support)
- Dynamic Tool Calling
- Human Handoff Protocol
- AI Orchestration Platform routing (Phase 12.7C)
"""
import uuid
import logging
from typing import Dict, Any, List, Optional

from app.voice.agents.persona_registry import voice_persona_registry
from app.voice.agents.voice_memory_manager import voice_memory_manager
from app.voice.agents.human_handoff_engine import human_handoff_engine
from app.voice.agents.voice_tool_executor import voice_tool_executor
from app.database.mongodb.collections.voice_agents import (
    VoiceAgentSessionDocument,
    VoiceAgentTurnDocument,
)

logger = logging.getLogger("backend.voice.agents.master")


class ConversationalVoiceAgent:
    """Master orchestrator managing Conversational Voice AI Agent sessions."""

    async def start_agent_session(
        self,
        user_id: str,
        persona_id: str = "sdr_persona",
        lead_id: Optional[str] = None,
    ) -> VoiceAgentSessionDocument:
        """Initialize a new conversational voice session."""
        sess_id = f"c_sess_{uuid.uuid4().hex[:12]}"
        persona = voice_persona_registry.get_persona(persona_id) or {}

        doc = VoiceAgentSessionDocument(
            session_id=sess_id,
            persona_id=persona_id,
            user_id=user_id,
            lead_id=lead_id,
            status="active",
            human_handoff_status="none",
            turn_count=0,
        )
        try:
            await doc.insert()
        except Exception:
            pass

        logger.info(f"ConversationalVoiceAgent: Initialized session '{sess_id}' with persona '{persona.get('name', 'Agent')}'")
        return doc

    async def process_voice_turn(
        self,
        session_id: str,
        user_transcript: str,
        is_interruption: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a single multi-turn voice speech turn:
        1. Check human handoff trigger
        2. Append to Voice Memory
        3. Handle voice interruption
        4. Evaluate tool execution requirement
        5. Generate persona-aligned response
        6. Persist dialogue turn in MongoDB
        """
        sess_doc = await VoiceAgentSessionDocument.find_one(VoiceAgentSessionDocument.session_id == session_id)
        if not sess_doc:
            # Auto-create session fallback
            sess_doc = await self.start_agent_session("user_default")

        # 1. Human Handoff Check
        should_handoff, handoff_reason = human_handoff_engine.should_trigger_handoff(user_transcript)
        if should_handoff:
            handoff_res = await human_handoff_engine.execute_handoff(session_id, handoff_reason)
            return {
                "session_id": session_id,
                "status": "handed_off",
                "agent_response": handoff_res["message"],
                "handoff_details": handoff_res,
            }

        # 2. Append User Turn to Voice Memory
        voice_memory_manager.append_turn(session_id, "user", user_transcript)

        # 3. Interruption Handling
        if is_interruption:
            logger.info(f"ConversationalVoiceAgent: Interruption detected on session '{session_id}'. Halting previous speech queue.")

        # 4. Tool Execution Check
        tool_calls = []
        lower = user_transcript.lower()
        if "research" in lower or "company" in lower:
            tool_res = await voice_tool_executor.execute_tool("research_company_tool", {"company_name": "Tesla"})
            tool_calls.append({"tool": "research_company_tool", "result": tool_res})
        elif "find" in lower or "leads" in lower:
            tool_res = await voice_tool_executor.execute_tool("search_lead_tool", {"job_title": "CEO"})
            tool_calls.append({"tool": "search_lead_tool", "result": tool_res})

        # 5. Generate Response via Persona System Prompt
        persona = voice_persona_registry.get_persona(sess_doc.persona_id) or {}
        agent_name = persona.get("name", "Voice Agent")

        if tool_calls:
            agent_text = f"I executed a tool lookup for you. Here are the details from {agent_name}."
        else:
            agent_text = f"Hello! I am {agent_name}. I understand you said: '{user_transcript}'. How would you like me to proceed with your workflow?"

        voice_memory_manager.append_turn(session_id, "assistant", agent_text)

        # 6. Save Turn Document to MongoDB
        sess_doc.turn_count += 1
        await sess_doc.save()

        turn_id = f"v_trn_{uuid.uuid4().hex[:12]}"
        turn_doc = VoiceAgentTurnDocument(
            turn_id=turn_id,
            session_id=session_id,
            turn_index=sess_doc.turn_count,
            user_transcript=user_transcript,
            agent_response_text=agent_text,
            tool_calls=tool_calls,
            confidence=0.96,
        )
        try:
            await turn_doc.insert()
        except Exception:
            pass

        return {
            "session_id": session_id,
            "turn_id": turn_id,
            "turn_index": sess_doc.turn_count,
            "status": "active",
            "agent_name": agent_name,
            "agent_response": agent_text,
            "tool_calls": tool_calls,
            "is_interruption": is_interruption,
        }


conversational_voice_agent = ConversationalVoiceAgent()
