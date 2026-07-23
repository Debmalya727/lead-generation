"""
IntentClassifier for Phase 12: Enterprise Conversational CRM.

Classifies natural language inputs and slash commands into platform operational intents.
"""
import re
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("backend.conversation.intent.classifier")


class IntentClassifier:
    """Classifier determining user intent and confidence score."""

    INTENT_MAP = {
        "discover": "lead_discovery",
        "research": "company_research",
        "outreach": "outreach",
        "report": "reporting",
        "workflows": "workflow_execution",
        "score": "lead_scoring",
        "help": "general_question",
        "history": "analytics",
    }

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify text input into an intent.
        Returns {"intent": str, "confidence": float, "is_slash_command": bool, "slash_command": str|None}
        """
        cleaned = text.strip()
        
        # 1. Slash command detection
        if cleaned.startswith("/"):
            parts = cleaned.split(maxsplit=1)
            cmd = parts[0][1:].lower()
            intent = self.INTENT_MAP.get(cmd, "workflow_execution")
            return {
                "intent": intent,
                "confidence": 1.0,
                "is_slash_command": True,
                "slash_command": cmd,
                "raw_text": text,
            }

        text_lower = cleaned.lower()

        # 2. Rule-based keyword classification
        if any(w in text_lower for w in ["discover", "find leads", "prospect", "find companies", "search companies", "lead discovery"]):
            return {"intent": "lead_discovery", "confidence": 0.92, "is_slash_command": False, "raw_text": text}

        if any(w in text_lower for w in ["research", "investigate", "due diligence", "company analysis", "deep dive"]):
            return {"intent": "company_research", "confidence": 0.95, "is_slash_command": False, "raw_text": text}

        if any(w in text_lower for w in ["score", "lead score", "icp fit", "qualification", "qualify"]):
            return {"intent": "lead_scoring", "confidence": 0.90, "is_slash_command": False, "raw_text": text}

        if any(w in text_lower for w in ["sales intelligence", "competitor", "market intelligence", "signals", "funding"]):
            return {"intent": "sales_intelligence", "confidence": 0.91, "is_slash_command": False, "raw_text": text}

        if any(w in text_lower for w in ["outreach", "email", "sequence", "linkedin", "campaign", "pitch"]):
            return {"intent": "outreach", "confidence": 0.93, "is_slash_command": False, "raw_text": text}

        if any(w in text_lower for w in ["report", "executive report", "pdf report", "sales report", "generate report"]):
            return {"intent": "reporting", "confidence": 0.94, "is_slash_command": False, "raw_text": text}

        if any(w in text_lower for w in ["workflow", "run workflow", "pipeline", "automation", "execute"]):
            return {"intent": "workflow_execution", "confidence": 0.88, "is_slash_command": False, "raw_text": text}

        if any(w in text_lower for w in ["update crm", "save to crm", "update lead", "add tag"]):
            return {"intent": "crm_update", "confidence": 0.89, "is_slash_command": False, "raw_text": text}

        if any(w in text_lower for w in ["analytics", "metrics", "performance", "conversion rate"]):
            return {"intent": "analytics", "confidence": 0.85, "is_slash_command": False, "raw_text": text}

        if any(w in text_lower for w in ["help", "what can you do", "commands", "how to use"]):
            return {"intent": "general_question", "confidence": 0.98, "is_slash_command": False, "raw_text": text}

        # Fallback to company research if a company name pattern is present
        if len(cleaned.split()) <= 4 and not cleaned.endswith("?"):
            return {"intent": "company_research", "confidence": 0.70, "is_slash_command": False, "raw_text": text}

        return {"intent": "general_question", "confidence": 0.75, "is_slash_command": False, "raw_text": text}
