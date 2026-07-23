"""
AmbiguityEngine — Identifies missing or vague entity parameters in voice commands and generates targeted clarification prompts.
"""
from typing import Dict, Any, Tuple, Optional
import logging

from app.voice.commands.voice_command_parser import ParsedVoiceCommand

logger = logging.getLogger("backend.voice.commands.ambiguity")


class AmbiguityEngine:
    """Detects missing parameters and generates clarification prompts for ambiguous voice commands."""

    def evaluate_ambiguity(self, cmd: ParsedVoiceCommand) -> Tuple[bool, Optional[str]]:
        """
        Check if parsed command contains ambiguous or missing mandatory parameters.
        Returns: (is_ambiguous, clarification_prompt)
        """
        if cmd.intent == "UNKNOWN":
            return True, "I didn't quite catch that. Could you specify if you'd like to research a company, find leads, or summarize your CRM?"

        if cmd.intent == "RESEARCH_COMPANY":
            comp = cmd.extracted_parameters.get("company_name", "")
            if not comp or comp.lower() in ["a company", "company", "them"]:
                return True, "Which company would you like me to research?"

        if cmd.intent == "FIND_LEADS":
            title = cmd.extracted_parameters.get("job_title", "")
            if not title or title.lower() in ["leads", "people", "contacts"]:
                return True, "What specific job title or role are you looking for?"

        return False, None


ambiguity_engine = AmbiguityEngine()
