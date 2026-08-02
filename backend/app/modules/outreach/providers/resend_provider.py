"""
Resend Email Provider Integration for LeadForgeAI Outreach Module.
Sends campaign emails and transactional messages via Resend REST API v1.
"""
import os
import httpx
import logging
from typing import Dict, Any, List, Optional
from app.config.settings import settings

logger = logging.getLogger("backend.outreach.resend")


class ResendEmailProvider:
    """Production provider adapter for Resend Email API."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("RESEND_API_KEY", "") or settings.RESEND_API_KEY
        self.base_url = "https://api.resend.com/emails"

    async def send_email(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Send single email via Resend API."""
        if not self.api_key:
            raise ValueError("Missing RESEND_API_KEY configuration.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload: Dict[str, Any] = {
            "from": from_email or "LeadForgeAI Outreach <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        if text_content:
            payload["text"] = text_content
        if tags:
            payload["tags"] = tags

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(self.base_url, headers=headers, json=payload)
            if res.status_code not in (200, 201):
                logger.error(f"[ResendProvider] Error sending email to {to_email}: {res.text}")
                res.raise_for_status()
            
            data = res.json()
            logger.info(f"[ResendProvider] Successfully sent email to {to_email} (ID: {data.get('id')})")
            return data


resend_email_provider = ResendEmailProvider()
