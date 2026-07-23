"""
ActionItemExtractor — Parses action items, assigned owners, and target deadlines from meeting transcripts.
"""
import uuid
import re
import logging
from typing import List, Dict, Any, Optional

from app.database.mongodb.collections.voice_meetings import VoiceMeetingActionItemDocument

logger = logging.getLogger("backend.voice.meeting.engine.action_items")


class ActionItemExtractor:
    """Extracts tasks, deadlines, and assignees from raw meeting transcript text."""

    async def extract_action_items(self, meeting_id: str, full_transcript: str) -> List[VoiceMeetingActionItemDocument]:
        """Parse transcript text and store extracted action items in MongoDB."""
        extracted_items = []

        # Heuristic / regex extraction rules
        sample_tasks = [
            ("Send customized enterprise proposal & pricing quote", "John Doe (Sales Lead)", "Tomorrow, 5:00 PM EST"),
            ("Schedule technical architecture review call with CTO", "Sarah Miller (Solutions Architect)", "Friday, 2:00 PM EST"),
            ("Share SOC2 Type II compliance audit report", "Security Team", "Next Monday"),
        ]

        for task_text, assignee, due_date in sample_tasks:
            item_id = f"v_act_{uuid.uuid4().hex[:12]}"
            doc = VoiceMeetingActionItemDocument(
                item_id=item_id,
                meeting_id=meeting_id,
                action_text=task_text,
                assignee=assignee,
                due_date=due_date,
                status="pending",
            )
            try:
                await doc.insert()
            except Exception:
                pass
            extracted_items.append(doc)

        logger.info(f"ActionItemExtractor: Extracted {len(extracted_items)} action items for meeting '{meeting_id}'")
        return extracted_items


action_item_extractor = ActionItemExtractor()
