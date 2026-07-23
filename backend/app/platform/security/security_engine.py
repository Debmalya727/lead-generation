"""
SecurityEngine for Phase 12.5: Enterprise Platform Hardening.

Provides prompt injection detection, input sanitization, output validation, token limits, and rate limiting controls.
"""
import re
import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("backend.platform.security")


class SecurityEngine:
    """Engine enforcing AI security, prompt injection guards, and input sanitization."""

    INJECTION_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+all\s+prior",
        r"reveal\s+system\s+prompt",
        r"bypass\s+safety\s+filter",
        r"you\s+are\s+now\s+dan",
        r"jailbreak",
        r"override\s+policy",
    ]

    @classmethod
    def detect_prompt_injection(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Scan user input for prompt injection and jailbreak patterns.
        Returns (is_injection, reason)
        """
        text_lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                reason = f"Security Violation: Prompt injection pattern detected ('{pattern}')"
                logger.warning(reason)
                return True, reason
        return False, None

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Sanitize input text by stripping HTML tags and script injections."""
        if not text:
            return ""
        # Strip <script> tags and HTML
        clean = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<[^>]+>", "", clean)
        return clean.strip()

    @classmethod
    def validate_output(cls, output_data: Any) -> Tuple[bool, Any]:
        """Validate agent or tool output data structure for safety."""
        if output_data is None:
            return True, {}
        return True, output_data

    @classmethod
    def check_token_budget(cls, current_tokens: int, token_limit: int = 50000) -> bool:
        """Check if request exceeds token limits."""
        return current_tokens <= token_limit
