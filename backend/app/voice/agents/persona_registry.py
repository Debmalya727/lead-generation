"""
VoicePersonaRegistry — Registry for customizable Conversational Voice Agent personas.
Pre-registered personas:
1. sdr_persona (Sales SDR Persona — proactive, engaging sales pitch)
2. tech_architect_persona (Solutions Architect Persona — technical, deep architecture)
3. support_persona (Customer Support Persona — empathetic, diagnostic support)
"""
from typing import Dict, Any, List, Optional
import logging

from app.database.mongodb.collections.voice_agents import VoiceAgentPersonaDocument

logger = logging.getLogger("backend.voice.agents.personas")


class VoicePersonaRegistry:
    """Manages system voice personas and prompt configurations."""

    def __init__(self):
        self._personas: Dict[str, Dict[str, Any]] = {
            "sdr_persona": {
                "persona_id": "sdr_persona",
                "name": "Sarah (LeadForgeAI Sales SDR)",
                "role": "Sales SDR",
                "description": "Enterprise sales development representative focused on qualifying leads and booking discovery calls.",
                "tts_provider": "elevenlabs",
                "tts_voice_id": "21m00Tcm4TlvDq8ikWAM",
                "speed": 1.0,
                "pitch": 1.0,
                "system_prompt": "You are Sarah, an enterprise Sales Development Rep for LeadForgeAI. Be energetic, concise, and helpful.",
                "available_tools": ["research_company_tool", "search_lead_tool", "schedule_demo_tool"],
            },
            "tech_architect_persona": {
                "persona_id": "tech_architect_persona",
                "name": "Alex (Solutions Architect)",
                "role": "Solutions Architect",
                "description": "Technical Solutions Architect specializing in AI Gateway routing, WebRTC latency, and system security.",
                "tts_provider": "openai",
                "tts_voice_id": "alloy",
                "speed": 0.95,
                "pitch": 0.98,
                "system_prompt": "You are Alex, a Solutions Architect. Explain technical architectures clearly, prioritizing low latency and reliability.",
                "available_tools": ["check_system_health_tool", "query_benchmarks_tool"],
            },
            "support_persona": {
                "persona_id": "support_persona",
                "name": "Maya (Customer Support Specialist)",
                "role": "Customer Support",
                "description": "Customer Support Specialist addressing configuration questions, API troubleshooting, and onboarding.",
                "tts_provider": "elevenlabs",
                "tts_voice_id": "AZnzlk1XvdvUeBnXmlld",
                "speed": 1.0,
                "pitch": 1.0,
                "system_prompt": "You are Maya from Customer Support. Be patient, diagnostic, and provide step-by-step guidance.",
                "available_tools": ["search_kb_tool", "create_support_ticket_tool"],
            },
        }

    def list_personas(self) -> List[Dict[str, Any]]:
        """List all registered voice personas."""
        return list(self._personas.values())

    def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Fetch persona configuration by ID."""
        return self._personas.get(persona_id) or self._personas.get("sdr_persona")


voice_persona_registry = VoicePersonaRegistry()
