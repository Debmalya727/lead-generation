"""
SSMLParser — Parses and validates SSML (Speech Synthesis Markup Language) tags.
Supports: <speak>, <break time="..."/>, <prosody rate="..." pitch="...">, <emphasis level="...">.
"""
import re
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger("backend.tts.gateway.ssml")


class SSMLParser:
    """Parses SSML markup tags and extracts raw plain text fallback."""

    def parse_ssml(self, text_or_ssml: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Check if input contains SSML tags.
        Returns: (is_ssml, plain_text_clean, ssml_metadata)
        """
        if not text_or_ssml:
            return False, "", {}

        is_ssml = "<speak>" in text_or_ssml or "</speak>" in text_or_ssml or "<break" in text_or_ssml
        if not is_ssml:
            return False, text_or_ssml, {}

        # Strip SSML tags to obtain clean plain text
        clean_text = re.sub(r"<[^>]+>", " ", text_or_ssml)
        clean_text = " ".join(clean_text.split())

        metadata = {
            "has_break": "<break" in text_or_ssml,
            "has_prosody": "<prosody" in text_or_ssml,
            "has_emphasis": "<emphasis" in text_or_ssml,
        }
        return True, clean_text, metadata


ssml_parser = SSMLParser()
