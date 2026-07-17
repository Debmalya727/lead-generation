"""
Email Provider Factory.
Dynamically resolves and instantiates the appropriate provider (SMTP, Gmail, Outlook)
from an EmailAccount configuration object.
"""
import logging
from typing import Optional

from app.database.mongodb.collections.outreach import EmailAccount
from app.email.providers.base_provider import BaseEmailProvider
from app.email.providers.smtp_provider import SMTPProvider
from app.email.providers.gmail_provider import GmailProvider
from app.email.providers.outlook_provider import OutlookProvider

logger = logging.getLogger("backend.email.factory")


def get_email_provider(account: Optional[EmailAccount] = None) -> BaseEmailProvider:
    """
    Instantiate and return an email provider instance based on account settings.
    Falls back to local SMTP / mock if account is None.
    """
    if not account:
        logger.info("No EmailAccount provided. Using default fallback SMTPProvider.")
        return SMTPProvider()

    ptype = (account.provider_type or "smtp").lower().strip()

    if ptype == "gmail":
        return GmailProvider(
            email_address=account.email_address,
            app_password_or_token=account.smtp_password or account.api_key,
            display_name=account.name,
        )
    elif ptype == "outlook":
        return OutlookProvider(
            email_address=account.email_address,
            password_or_token=account.smtp_password or account.api_key,
            display_name=account.name,
        )
    else:
        # Standard SMTP
        return SMTPProvider(
            smtp_host=account.smtp_host or "localhost",
            smtp_port=account.smtp_port or 587,
            smtp_username=account.smtp_username or account.email_address,
            smtp_password=account.smtp_password,
            use_tls=account.use_tls,
            default_from_email=account.email_address,
            default_from_name=account.name,
        )
