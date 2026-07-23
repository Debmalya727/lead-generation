"""
EmailSummaryGenerator — Generates executive follow-up email drafts for meeting attendees.
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("backend.voice.meeting.engine.email")


class EmailSummaryGenerator:
    """Generates formatted executive follow-up emails post-meeting."""

    def generate_followup_email_draft(
        self,
        title: str,
        attendees: List[str],
        executive_summary: str,
        action_items: List[Dict[str, Any]],
    ) -> str:
        """Construct formatted HTML/Text follow-up email body."""
        items_formatted = "\n".join(
            [f"- {item.get('action_text', '')} (Assignee: {item.get('assignee', 'TBD')})" for item in action_items]
        )

        email_text = (
            f"Subject: Follow-up: {title}\n\n"
            f"Hi Everyone,\n\n"
            f"Thank you for attending our session today. Here is a brief summary of what we discussed:\n\n"
            f"Executive Summary:\n{executive_summary}\n\n"
            f"Key Action Items:\n{items_formatted}\n\n"
            f"Best regards,\nLeadForgeAI Sales Assistant"
        )

        logger.info(f"EmailSummaryGenerator: Generated follow-up email draft for {len(attendees)} attendees.")
        return email_text


email_summary_generator = EmailSummaryGenerator()
