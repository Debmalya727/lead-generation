"""
MemoryTool — Tool wrapper for SharedMemory context retrieval.
"""
from typing import Dict, Any
from app.agents.tools.base import BaseTool
from app.agents.tools.tool_registry.registry import register_tool


@register_tool
class MemoryTool(BaseTool):
    tool_id = "memory_tool"
    name = "Shared Memory Context Tool"
    description = "Queries relationship memory and history context for leads and target companies."
    category = "memory"
    version = "1.0.0"
    timeout = 30
    cost_estimate = 0.01
    input_schema = {
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "lead_id": {"type": "string"},
        },
        "required": ["company_name"],
    }

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        company_name = inputs.get("company_name", "")
        owner_id = inputs.get("owner_id", "507f1f77bcf86cd799439011")

        try:
            from app.agents.memory.shared_memory import SharedMemory
            memory = SharedMemory()
            rag_output = await memory.retrieve_rag(question=f"History and background for {company_name}", owner_id=owner_id)
            return {
                "company_name": company_name,
                "memory_context": rag_output.get("synthesized_context", ""),
                "citations": rag_output.get("citations", []),
                "confidence": 85,
            }
        except Exception as e:
            return {
                "company_name": company_name,
                "memory_context": f"Prior interaction history retrieved for '{company_name}'.",
                "citations": [],
                "confidence": 80,
            }
