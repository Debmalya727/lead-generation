"""Engine package for Phase 13.7 Enterprise Voice Meeting Assistant."""
from app.voice.meeting.engine.diarization_engine import diarization_engine
from app.voice.meeting.engine.action_item_extractor import action_item_extractor
from app.voice.meeting.engine.crm_meeting_integrator import crm_meeting_integrator
from app.voice.meeting.engine.email_summary_generator import email_summary_generator
from app.voice.meeting.engine.meeting_assistant import voice_meeting_assistant, VoiceMeetingAssistant

__all__ = [
    "diarization_engine",
    "action_item_extractor",
    "crm_meeting_integrator",
    "email_summary_generator",
    "voice_meeting_assistant",
    "VoiceMeetingAssistant",
]
