"""
SMTP Email Provider implementation using aiosmtplib / smtplib.
Sends emails via custom SMTP servers (e.g. Mailgun, SendGrid, Amazon SES, self-hosted).
"""
import asyncio
import email.mime.multipart
import email.mime.text
import logging
import smtplib
from typing import Dict, Optional

from app.email.providers.base_provider import BaseEmailProvider, SendEmailResult

logger = logging.getLogger("backend.email.smtp")


class SMTPProvider(BaseEmailProvider):
    """Async SMTP email provider implementation."""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        default_from_email: str = "noreply@leadforge.ai",
        default_from_name: str = "LeadForgeAI",
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.default_from_email = default_from_email
        self.default_from_name = default_from_name

    def _sync_send(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str],
        from_email: str,
        from_name: str,
        headers: Optional[Dict[str, str]],
    ) -> SendEmailResult:
        """Synchronous SMTP send wrapped for asyncio execution."""
        try:
            msg = email.mime.multipart.MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = to_email

            if headers:
                for k, v in headers.items():
                    msg[k] = v

            if body_text:
                msg.attach(email.mime.text.MIMEText(body_text, "plain", "utf-8"))
            if body_html:
                msg.attach(email.mime.text.MIMEText(body_html, "html", "utf-8"))

            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15)
                if self.use_tls:
                    server.starttls()

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.sendmail(from_email, [to_email], msg.as_string())
            server.quit()

            msg_id = msg.get("Message-ID", f"smtp-{to_email}")
            return SendEmailResult(success=True, message_id=msg_id)

        except Exception as e:
            logger.error(f"SMTP send failed for {to_email}: {e}")
            return SendEmailResult(success=False, error=str(e))

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
        sender_email = from_email or self.default_from_email
        sender_name = from_name or self.default_from_name

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            self._sync_send,
            to_email,
            subject,
            body_html,
            body_text,
            sender_email,
            sender_name,
            headers,
        )
        return result
