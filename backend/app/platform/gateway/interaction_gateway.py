"""
InteractionGateway for Phase 12.5: Enterprise Platform Hardening.

Universal entry-point managing authentication, context creation, security checks, RBAC, tracing, and routing.
"""
import time
import logging
from typing import Dict, Any, Optional, Tuple

from app.platform.context.request_context import RequestContext
from app.platform.rbac.rbac_engine import RBACEngine
from app.platform.audit.audit_logger import AuditLogger
from app.platform.security.security_engine import SecurityEngine
from app.platform.tracing.trace_manager import TraceManager

logger = logging.getLogger("backend.platform.gateway")


class InteractionGateway:
    """Universal interaction gateway for all platform entry-points."""

    SUPPORTED_CLIENTS = ["web", "rest", "chat", "voice", "mobile", "sdk", "extension"]

    def __init__(self):
        self.audit_logger = AuditLogger()
        self.security_engine = SecurityEngine()
        self.trace_manager = TraceManager()

    async def process_request(
        self,
        user_id: Optional[str],
        action: str,
        payload: Dict[str, Any],
        client_type: str = "web",
        role: str = "Owner",
        required_permission: str = "workflow:execute",
        session_id: Optional[str] = None,
    ) -> Tuple[RequestContext, Dict[str, Any]]:
        """
        Process request through gateway pipeline:
        1. Client validation & Context Loading (Correlation ID)
        2. Prompt Injection & Input Security Check
        3. RBAC Authorization Check
        4. Audit Log Event Creation
        5. Span Tracing Recording
        """
        start_t = time.time()
        client = client_type if client_type in self.SUPPORTED_CLIENTS else "web"

        # 1. Build RequestContext
        ctx = RequestContext(
            user_id=user_id,
            role=role,
            client_type=client,
            session_id=session_id,
        )

        # 2. Security Checks
        input_text = payload.get("message") or payload.get("company_name") or ""
        if isinstance(input_text, str) and input_text:
            is_inj, reason = self.security_engine.detect_prompt_injection(input_text)
            if is_inj:
                await self.audit_logger.log_event(
                    event_type="security_injection_blocked",
                    resource_type="gateway",
                    actor_id=user_id or "System",
                    details={"reason": reason, "raw_input": input_text},
                    status="rejected",
                    context=ctx,
                )
                raise ValueError(reason)

            # Sanitize input
            payload["sanitized_text"] = self.security_engine.sanitize_input(input_text)

        # 3. RBAC Authorization Check
        authorized = RBACEngine.authorize(ctx, required_permission)
        if not authorized:
            await self.audit_logger.log_event(
                event_type="rbac_rejected",
                resource_type="gateway",
                actor_id=user_id or "System",
                details={"action": action, "required_permission": required_permission},
                status="rejected",
                context=ctx,
            )
            raise PermissionError(f"RBAC Enforcement: Role '{role}' lacks permission '{required_permission}'")

        # 4. Log Audit Trail
        await self.audit_logger.log_event(
            event_type=f"gateway_{action}",
            resource_type="gateway",
            actor_id=user_id or "System",
            details={"action": action, "client": client},
            status="success",
            context=ctx,
        )

        # 5. Record Trace Span
        duration_ms = round((time.time() - start_t) * 1000, 2)
        await self.trace_manager.record_span(
            name=f"Gateway.{action}",
            component="gateway",
            duration_ms=duration_ms,
            trace_id=ctx.correlation_id,
            attributes={"client_type": client, "role": role},
        )

        logger.info(f"InteractionGateway: Processed action '{action}' for client '{client}' (correlation: '{ctx.correlation_id}')")
        return ctx, payload
