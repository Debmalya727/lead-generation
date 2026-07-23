"""
TraceManager for Phase 12.5: Enterprise Platform Hardening.

Manages distributed tracing spans across Gateway, Workflows, Agents, Tools, and RAG components.
"""
import uuid
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.database.mongodb.collections.platform import RequestTraceDocument

logger = logging.getLogger("backend.platform.tracing")


class TraceManager:
    """Manager handling OpenTelemetry-compliant distributed tracing spans."""

    async def record_span(
        self,
        name: str,
        component: str,
        duration_ms: float,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        status: str = "ok",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> RequestTraceDocument:
        """Persist a trace span record."""
        t_id = trace_id or f"trace_{uuid.uuid4().hex[:12]}"
        s_id = span_id or f"span_{uuid.uuid4().hex[:10]}"

        doc = RequestTraceDocument(
            trace_id=t_id,
            span_id=s_id,
            parent_span_id=parent_span_id,
            name=name,
            component=component,
            duration_ms=duration_ms,
            status=status,
            attributes=attributes or {},
            timestamp=datetime.now(timezone.utc),
        )
        try:
            await doc.insert()
        except Exception as e:
            logger.warning(f"Failed to record trace span: {str(e)}")
        return doc

    async def list_traces(
        self,
        trace_id: Optional[str] = None,
        component: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> tuple[List[RequestTraceDocument], int]:
        """List distributed traces."""
        query = []
        if trace_id:
            query.append(RequestTraceDocument.trace_id == trace_id)
        if component:
            query.append(RequestTraceDocument.component == component)

        total = await RequestTraceDocument.find(*query).count()
        docs = await RequestTraceDocument.find(*query).sort("-timestamp").skip(skip).limit(limit).to_list()
        return docs, total
