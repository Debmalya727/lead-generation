"""
Microsoft Outlook / Office365 Email Provider adapter.
Supports Outlook SMTP & Graph API sending endpoints.
"""
import logging
from typing import Dict, Optional

from app.email.providers.base_provider import BaseEmailProvider, SendEmailResult
from app.email.providers.smtp_provider import SMTPProvider

logger = logging.getLogger("backend.email.outlook")


class OutlookProvider(BaseEmailProvider):
    """Outlook / Office365 email provider implementation."""

    def __init__(
        self,
        email_address: str,
        password_or_token: Optional[str] = None,
        display_name: str = "LeadForgeAI Sales",
    ):
        self.email_address = email_address
        # Office365 SMTP endpoint fallback
        self._smtp_provider = SMTPProvider(
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_username=email_address,
            smtp_password=password_or_token or "",
            use_tls=True,
            default_from_email=email_address,
            default_from_name=display_name,
        )

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
        logger.info(f"Sending Outlook/Office365 message to {to_email} via {self.email_address}")
        return await self._smtp_provider.send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            from_email=from_email or self.email_address,
            from_name=from_name,
            headers=headers,
        )
