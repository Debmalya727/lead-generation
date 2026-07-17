"""
Base email provider abstract class.
Defines unified interface for sending emails across SMTP, Gmail, and Outlook.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SendEmailResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class BaseEmailProvider(ABC):
    """Abstract contract for email sending providers."""

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> SendEmailResult:
        """Send an email asynchronously to a single recipient."""
        pass
