"""
ClarificationEngine for Phase 12: Enterprise Conversational CRM.

Generates follow-up clarification questions when critical entities are missing for an intent.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("backend.conversation.intent.clarification")


class ClarificationEngine:
    """Engine identifying missing information and generating clarification questions."""

    REQUIRED_ENTITIES = {
        "company_research": ["company_name"],
        "lead_scoring": ["company_name"],
        "sales_intelligence": ["company_name"],
        "outreach": ["company_name"],
        "reporting": ["company_name"],
        "lead_discovery": [],  # Can work with general criteria
    }

    def check_clarification(self, intent: str, entities: Dict[str, Any]) -> Tuple[bool, List[str], Optional[str]]:
        """
        Check if clarification is needed.
        Returns (needs_clarification, missing_entities, clarification_prompt)
        """
        required = self.REQUIRED_ENTITIES.get(intent, [])
        missing = [req for req in required if not entities.get(req)]

        if not missing:
            return False, [], None

        # Build natural clarification prompts
        if "company_name" in missing:
            prompt = "Which target company would you like me to analyze?"
        elif "industry" in missing:
            prompt = "Which industry or sector should I target?"
        elif "country" in missing:
            prompt = "Which country or geographical region are you focusing on?"
        else:
            prompt = f"Please specify the missing details: {', '.join(missing)}"

        logger.info(f"ClarificationEngine: Needed clarification for intent '{intent}', missing: {missing}")
        return True, missing, prompt
