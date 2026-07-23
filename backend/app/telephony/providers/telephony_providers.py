"""
Phase 13.9 — Telephony Provider Registry.
Abstract base + concrete provider stubs for:
- Twilio
- SIP (RFC 3261)
- Zoom Phone
- Microsoft Teams Phone
"""
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("backend.telephony.providers")


# ─────────────────────────────────────────────
# Abstract Provider Base
# ─────────────────────────────────────────────
class TelephonyProvider(ABC):
    """Abstract base class for all telephony providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    @property
    @abstractmethod
    def display_name(self) -> str: ...

    @abstractmethod
    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def accept_inbound_call(
        self,
        call_id: str,
        webhook_payload: Dict[str, Any],
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def transfer_call(
        self,
        call_id: str,
        target_number: str,
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def start_recording(self, call_id: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def stop_recording(self, call_id: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def hangup_call(self, call_id: str) -> Dict[str, Any]: ...

    @abstractmethod
    def is_available(self) -> bool: ...


# ─────────────────────────────────────────────
# Twilio Provider
# ─────────────────────────────────────────────
class TwilioProvider(TelephonyProvider):
    """Twilio Voice API integration."""

    @property
    def provider_id(self) -> str:
        return "twilio"

    @property
    def display_name(self) -> str:
        return "Twilio Voice"

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        call_sid = f"CA{uuid.uuid4().hex[:32]}"
        logger.info(f"[Twilio] Initiating outbound call to '{to_number}' (SID={call_sid})")
        return {
            "call_id": call_sid,
            "provider": "twilio",
            "status": "ringing",
            "to": to_number,
            "from": from_number,
            "direction": "outbound",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    async def accept_inbound_call(
        self,
        call_id: str,
        webhook_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        logger.info(f"[Twilio] Accepting inbound call '{call_id}'")
        return {
            "call_id": call_id,
            "provider": "twilio",
            "status": "in_progress",
            "direction": "inbound",
            "from": webhook_payload.get("From", "unknown"),
            "twiml_response": "<Response><Say>Welcome to LeadForgeAI. Connecting you now.</Say></Response>",
        }

    async def transfer_call(self, call_id: str, target_number: str) -> Dict[str, Any]:
        logger.info(f"[Twilio] Transferring call '{call_id}' → '{target_number}'")
        return {"call_id": call_id, "status": "transferred", "target": target_number}

    async def start_recording(self, call_id: str) -> Dict[str, Any]:
        rec_sid = f"RE{uuid.uuid4().hex[:32]}"
        return {"call_id": call_id, "recording_id": rec_sid, "status": "recording_started"}

    async def stop_recording(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "recording_stopped"}

    async def hangup_call(self, call_id: str) -> Dict[str, Any]:
        logger.info(f"[Twilio] Hanging up call '{call_id}'")
        return {"call_id": call_id, "status": "completed"}

    def is_available(self) -> bool:
        return True


# ─────────────────────────────────────────────
# SIP Provider
# ─────────────────────────────────────────────
class SIPProvider(TelephonyProvider):
    """Generic SIP (RFC 3261) telephony provider via pjsua2 / aiosip."""

    @property
    def provider_id(self) -> str:
        return "sip"

    @property
    def display_name(self) -> str:
        return "SIP / VoIP (RFC 3261)"

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        call_id = f"sip_{uuid.uuid4().hex[:16]}"
        sip_uri = f"sip:{to_number}@{metadata.get('sip_domain', 'sip.leadforgeai.com')}" if metadata else f"sip:{to_number}"
        logger.info(f"[SIP] INVITE → {sip_uri}")
        return {
            "call_id": call_id,
            "provider": "sip",
            "sip_uri": sip_uri,
            "status": "ringing",
            "direction": "outbound",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    async def accept_inbound_call(
        self,
        call_id: str,
        webhook_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        logger.info(f"[SIP] Accepting SIP INVITE call_id='{call_id}'")
        return {"call_id": call_id, "provider": "sip", "status": "in_progress", "direction": "inbound"}

    async def transfer_call(self, call_id: str, target_number: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "transferred", "target": f"sip:{target_number}"}

    async def start_recording(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "recording_id": f"sip_rec_{uuid.uuid4().hex[:12]}", "status": "recording_started"}

    async def stop_recording(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "recording_stopped"}

    async def hangup_call(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "completed"}

    def is_available(self) -> bool:
        return True


# ─────────────────────────────────────────────
# Zoom Phone Provider
# ─────────────────────────────────────────────
class ZoomPhoneProvider(TelephonyProvider):
    """Zoom Phone Cloud PBX API integration."""

    @property
    def provider_id(self) -> str:
        return "zoom_phone"

    @property
    def display_name(self) -> str:
        return "Zoom Phone"

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        call_id = f"zm_{uuid.uuid4().hex[:16]}"
        logger.info(f"[ZoomPhone] Dialing '{to_number}' (call_id={call_id})")
        return {
            "call_id": call_id,
            "provider": "zoom_phone",
            "status": "ringing",
            "to": to_number,
            "from": from_number,
            "direction": "outbound",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    async def accept_inbound_call(
        self,
        call_id: str,
        webhook_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {"call_id": call_id, "provider": "zoom_phone", "status": "in_progress", "direction": "inbound"}

    async def transfer_call(self, call_id: str, target_number: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "transferred", "target": target_number}

    async def start_recording(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "recording_id": f"zm_rec_{uuid.uuid4().hex[:12]}", "status": "recording_started"}

    async def stop_recording(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "recording_stopped"}

    async def hangup_call(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "completed"}

    def is_available(self) -> bool:
        return True


# ─────────────────────────────────────────────
# Microsoft Teams Phone Provider
# ─────────────────────────────────────────────
class MSTeamsPhoneProvider(TelephonyProvider):
    """Microsoft Teams Phone (Direct Routing / Calling Plans) integration."""

    @property
    def provider_id(self) -> str:
        return "teams_phone"

    @property
    def display_name(self) -> str:
        return "Microsoft Teams Phone"

    async def initiate_outbound_call(
        self,
        to_number: str,
        from_number: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        call_id = f"mst_{uuid.uuid4().hex[:16]}"
        logger.info(f"[MSTeamsPhone] Placing call to '{to_number}' via Teams (call_id={call_id})")
        return {
            "call_id": call_id,
            "provider": "teams_phone",
            "status": "ringing",
            "to": to_number,
            "from": from_number,
            "direction": "outbound",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    async def accept_inbound_call(
        self,
        call_id: str,
        webhook_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {"call_id": call_id, "provider": "teams_phone", "status": "in_progress", "direction": "inbound"}

    async def transfer_call(self, call_id: str, target_number: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "transferred", "target": target_number}

    async def start_recording(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "recording_id": f"mst_rec_{uuid.uuid4().hex[:12]}", "status": "recording_started"}

    async def stop_recording(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "recording_stopped"}

    async def hangup_call(self, call_id: str) -> Dict[str, Any]:
        return {"call_id": call_id, "status": "completed"}

    def is_available(self) -> bool:
        return True


# ─────────────────────────────────────────────
# Provider Registry
# ─────────────────────────────────────────────
class TelephonyProviderRegistry:
    """Singleton registry for all telephony providers."""

    def __init__(self):
        self._providers: Dict[str, TelephonyProvider] = {}
        self._register_defaults()

    def _register_defaults(self):
        for p in [TwilioProvider(), SIPProvider(), ZoomPhoneProvider(), MSTeamsPhoneProvider()]:
            self._providers[p.provider_id] = p
        logger.info(f"TelephonyProviderRegistry: Registered {len(self._providers)} providers: {list(self._providers.keys())}")

    def get(self, provider_id: str) -> TelephonyProvider:
        if provider_id not in self._providers:
            raise ValueError(f"Telephony provider '{provider_id}' not registered.")
        return self._providers[provider_id]

    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {
                "provider_id": p.provider_id,
                "display_name": p.display_name,
                "available": p.is_available(),
            }
            for p in self._providers.values()
        ]


telephony_provider_registry = TelephonyProviderRegistry()
