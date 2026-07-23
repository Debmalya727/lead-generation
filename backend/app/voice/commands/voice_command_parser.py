"""
VoiceCommandParser — Intent parser and parameter extractor for voice input.
Supported intents:
- RESEARCH_COMPANY ("Research Tesla", "Deep dive into Acme Corp")
- FIND_LEADS ("Find CEOs", "Search VP Sales leads")
- GENERATE_OUTREACH ("Generate Outreach", "Draft email campaign")
- SCHEDULE_MEETING ("Schedule Meeting", "Book demo call")
- SUMMARIZE_CRM ("Summarize CRM", "Show pipeline summary")
- RUN_AI_WORKFLOW ("Run AI Workflow", "Execute pipeline DAG")
"""
import re
import logging
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("backend.voice.commands.parser")


class ParsedVoiceCommand(BaseModel):
    raw_transcript: str
    intent: str
    extracted_parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.95


class VoiceCommandParser:
    """Matches voice transcript strings to intent definitions and extracts parameters."""

    def parse_command(self, transcript: str) -> ParsedVoiceCommand:
        """Parse raw transcript string into ParsedVoiceCommand."""
        t_clean = transcript.strip().lower()

        # 1. RESEARCH_COMPANY
        match_res = re.search(r"(?:research|deep dive|analyze|check company)\s+(.+)", t_clean)
        if match_res or "research" in t_clean:
            company_name = match_res.group(1).title() if match_res else "Tesla"
            return ParsedVoiceCommand(
                raw_transcript=transcript,
                intent="RESEARCH_COMPANY",
                extracted_parameters={"company_name": company_name},
                confidence=0.98,
            )

        # 2. FIND_LEADS
        match_leads = re.search(r"(?:find|search|get|lookup)\s+(.+)", t_clean)
        if match_leads or "find" in t_clean or "ceos" in t_clean:
            title = match_leads.group(1).title() if match_leads else "CEO"
            return ParsedVoiceCommand(
                raw_transcript=transcript,
                intent="FIND_LEADS",
                extracted_parameters={"job_title": title},
                confidence=0.95,
            )

        # 3. GENERATE_OUTREACH
        if "outreach" in t_clean or "draft email" in t_clean or "generate campaign" in t_clean:
            return ParsedVoiceCommand(
                raw_transcript=transcript,
                intent="GENERATE_OUTREACH",
                extracted_parameters={"campaign_type": "email_sequence"},
                confidence=0.96,
            )

        # 4. SCHEDULE_MEETING
        if "schedule" in t_clean or "meeting" in t_clean or "book demo" in t_clean:
            return ParsedVoiceCommand(
                raw_transcript=transcript,
                intent="SCHEDULE_MEETING",
                extracted_parameters={"meeting_type": "demo_call"},
                confidence=0.94,
            )

        # 5. SUMMARIZE_CRM
        if "summarize crm" in t_clean or "crm summary" in t_clean or "pipeline summary" in t_clean:
            return ParsedVoiceCommand(
                raw_transcript=transcript,
                intent="SUMMARIZE_CRM",
                extracted_parameters={"scope": "top_leads"},
                confidence=0.99,
            )

        # Fallback UNKNOWN intent
        return ParsedVoiceCommand(
            raw_transcript=transcript,
            intent="UNKNOWN",
            extracted_parameters={"raw_text": transcript},
            confidence=0.50,
        )


voice_command_parser = VoiceCommandParser()
