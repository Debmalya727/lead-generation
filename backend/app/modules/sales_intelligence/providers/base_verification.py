"""
Base abstract interface for Contact Verification Providers.
Designed so paid providers (Hunter, NeverBounce, Dropcontact) can be plugged in seamlessly.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseVerificationProvider(ABC):
    """Abstract base class for email/phone/domain verification providers."""

    @abstractmethod
    async def verify_email(self, email: str) -> Dict[str, Any]:
        """Verify email address syntax, domain MX, and disposable status."""
        pass

    @abstractmethod
    async def verify_phone(self, phone: str) -> Dict[str, Any]:
        """Verify phone number format and country validity."""
        pass

    @abstractmethod
    async def verify_domain(self, domain: str) -> Dict[str, Any]:
        """Verify domain accessibility and SSL status."""
        pass
