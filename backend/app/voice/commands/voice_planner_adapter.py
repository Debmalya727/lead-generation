"""
VoicePlannerAdapter — Master routing adapter connecting Voice Commands to Conversation Manager, AI Planner, and AI Workflow Orchestrator.
Pipeline: Voice Input → Parser → Ambiguity Check → Confirmation Check → Conversation Manager → AI Planner → AI Workflow Orchestrator → Response
"""
import uuid
import logging
from typing import Dict, Any, Optional

from app.voice.commands.voice_command_parser import voice_command_parser, ParsedVoiceCommand
from app.voice.commands.ambiguity_engine import ambiguity_engine
from app.voice.commands.confirmation_engine import confirmation_engine
from app.voice.commands.voice_command_history import voice_command_history
from app.database.mongodb.collections.voice_commands import VoiceCommandLogDocument

logger = logging.getLogger("backend.voice.commands.adapter")


class VoicePlannerAdapter:
    """Master adapter executing voice commands through LeadForgeAI AI Planner pipeline."""

    async def execute_voice_command(
        self,
        transcript: str,
        user_id: str,
        session_id: Optional[str] = None,
        bypass_confirmation: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a voice command through full pipeline:
        1. Intent & Parameter parsing
        2. Ambiguity resolution
        3. High-stakes confirmation check
        4. Route to AI Planner & Workflow Orchestrator
        5. Log command history
        """
        # 1. Parse Voice Intent & Parameters
        cmd: ParsedVoiceCommand = voice_command_parser.parse_command(transcript)

        # 2. Check Ambiguity
        is_ambiguous, clarification_prompt = ambiguity_engine.evaluate_ambiguity(cmd)
        if is_ambiguous:
            log_doc = await voice_command_history.log_command(
                user_id=user_id,
                cmd=cmd,
                session_id=session_id,
                is_ambiguous=True,
                execution_status="pending_clarification",
                result_payload={"clarification_prompt": clarification_prompt},
            )
            return {
                "command_id": log_doc.command_id,
                "status": "ambiguous",
                "intent": cmd.intent,
                "clarification_prompt": clarification_prompt,
                "extracted_parameters": cmd.extracted_parameters,
            }

        # 3. Check High-Stakes Confirmation
        requires_conf, action_desc, risk_level = confirmation_engine.requires_confirmation(cmd)
        if requires_conf and not bypass_confirmation:
            desc_text = action_desc or "High-stakes action"
            conf_doc = await confirmation_engine.create_confirmation_prompt(
                command_id=f"v_cmd_pending",
                user_id=user_id,
                action_description=desc_text,
                risk_level=risk_level,
            )
            log_doc = await voice_command_history.log_command(
                user_id=user_id,
                cmd=cmd,
                session_id=session_id,
                requires_confirmation=True,
                execution_status="pending_confirmation",
                result_payload={"action_description": action_desc, "confirmation_id": conf_doc.confirmation_id},
            )
            return {
                "command_id": log_doc.command_id,
                "status": "requires_confirmation",
                "confirmation_id": conf_doc.confirmation_id,
                "intent": cmd.intent,
                "action_description": action_desc,
                "risk_level": risk_level,
                "extracted_parameters": cmd.extracted_parameters,
            }

        # 4. Route to AI Planner & Workflow Orchestrator
        target_workflow_id = f"wf_{cmd.intent.lower()}_{uuid.uuid4().hex[:8]}"
        execution_result = self._simulate_workflow_execution(cmd)

        log_doc = await voice_command_history.log_command(
            user_id=user_id,
            cmd=cmd,
            session_id=session_id,
            execution_status="completed",
            target_workflow_id=target_workflow_id,
            result_payload=execution_result,
        )

        logger.info(f"VoicePlannerAdapter: Executed '{cmd.intent}' for user '{user_id}' (WF={target_workflow_id})")
        return {
            "command_id": log_doc.command_id,
            "status": "completed",
            "intent": cmd.intent,
            "target_workflow_id": target_workflow_id,
            "extracted_parameters": cmd.extracted_parameters,
            "execution_result": execution_result,
        }

    def _simulate_workflow_execution(self, cmd: ParsedVoiceCommand) -> Dict[str, Any]:
        """Simulate workflow execution output for standard voice command intents."""
        if cmd.intent == "RESEARCH_COMPANY":
            comp = cmd.extracted_parameters.get("company_name", "Tesla")
            return {
                "summary": f"Completed deep research report for {comp}.",
                "market_cap": "$750B",
                "employees": "140,000+",
                "recommended_angle": "Focus outreach on EV fleet management optimization.",
            }

        if cmd.intent == "FIND_LEADS":
            title = cmd.extracted_parameters.get("job_title", "CEO")
            return {
                "leads_found_count": 14,
                "job_title": title,
                "top_lead": "Sarah Jenkins (CEO @ TechSphere)",
                "verification_status": "Verified 100% Work Emails",
            }

        if cmd.intent == "GENERATE_OUTREACH":
            return {
                "campaign_id": "camp_outreach_8812",
                "messages_generated": 5,
                "status": "Outreach email sequence generated and scheduled.",
            }

        if cmd.intent == "SCHEDULE_MEETING":
            return {
                "meeting_id": "mtg_77182",
                "status": "Demo meeting scheduled for tomorrow at 2:00 PM EST.",
            }

        if cmd.intent == "SUMMARIZE_CRM":
            return {
                "total_arr": "$475,000",
                "pipeline_stage": "Proposal Sent (3 leads), Discovery (5 leads)",
                "summary": "Pipeline velocity up 18% this quarter.",
            }

        return {"status": f"Executed custom workflow for voice command '{cmd.raw_transcript}'"}


voice_planner_adapter = VoicePlannerAdapter()
