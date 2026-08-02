"""
Resend Email Provider implementing BaseEmailProvider contract.
"""
import os
import httpx
import logging
from typing import Dict, Optional
from app.email.providers.base_provider import BaseEmailProvider, SendEmailResult
from app.config.settings import settings

logger = logging.getLogger("backend.email.resend")


class ResendProvider(BaseEmailProvider):
    """Resend REST API email provider adapter."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RESEND_API_KEY", "") or settings.RESEND_API_KEY
        self.base_url = "https://api.resend.com/emails"

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
        if not self.api_key:
            logger.error("[ResendProvider] Missing RESEND_API_KEY")
            return SendEmailResult(success=False, error="Missing RESEND_API_KEY configuration.")

        sender = from_email or "onboarding@resend.dev"
        if from_name:
            sender = f"{from_name} <{sender}>"

        req_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "from": sender,
            "to": [to_email],
            "subject": subject,
            "html": body_html,
        }
        if body_text:
            payload["text"] = body_text
        if headers:
            payload["headers"] = headers

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(self.base_url, headers=req_headers, json=payload)
                if res.status_code not in (200, 201):
                    err_msg = res.text
                    logger.error(f"[ResendProvider] Failed to send email: {err_msg}")
                    return SendEmailResult(success=False, error=err_msg)

                data = res.json()
                msg_id = data.get("id")
                logger.info(f"[ResendProvider] Email sent successfully to {to_email} (ID: {msg_id})")
                return SendEmailResult(success=True, message_id=msg_id)
        except Exception as e:
            logger.error(f"[ResendProvider] Exception sending email: {e}")
            return SendEmailResult(success=False, error=str(e))
