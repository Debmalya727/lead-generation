"""
MessageBusTool — Tool wrapper for AgentMessageBus.
"""
from typing import Dict, Any
from app.agents.tools.base import BaseTool
from app.agents.tools.tool_registry.registry import register_tool


@register_tool
class MessageBusTool(BaseTool):
    tool_id = "message_bus_tool"
    name = "Agent Message Bus Tool"
    description = "Posts and retrieves agent-to-agent messages and broadcast notifications."
    category = "messaging"
    version = "1.0.0"
    timeout = 20
    cost_estimate = 0.01
    input_schema = {
        "type": "object",
        "properties": {
            "job_id": {"type": "string"},
            "action": {"type": "string", "enum": ["send", "history"]},
            "from_agent": {"type": "string"},
            "to_agent": {"type": "string"},
            "payload": {"type": "object"},
        },
        "required": ["job_id", "action"],
    }

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        job_id = inputs.get("job_id", "")
        action = inputs.get("action", "history")
        from_ag = inputs.get("from_agent", "System")
        to_ag = inputs.get("to_agent", "broadcast")
        payload = inputs.get("payload", {})

        from app.agents.collaboration.messages.bus import AgentMessageBus
        from app.agents.collaboration.messages.message import AgentMessage
        bus = AgentMessageBus.get_instance()

        if action == "send":
            msg = AgentMessage(job_id=job_id, from_agent=from_ag, to_agent=to_ag, payload=payload)
            sent = await bus.send(msg)
            return {"action": "send", "message_id": sent.message_id, "status": sent.status}
        else:
            history = await bus.history(job_id=job_id)
            return {"action": "history", "total_messages": len(history), "messages": [m.model_dump() for m in history]}
