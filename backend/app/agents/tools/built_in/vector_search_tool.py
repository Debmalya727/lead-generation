"""
VectorSearchTool — Tool wrapper for Vector Search and RAG pipeline.
"""
from typing import Dict, Any
from app.agents.tools.base import BaseTool
from app.agents.tools.tool_registry.registry import register_tool


@register_tool
class VectorSearchTool(BaseTool):
    tool_id = "vector_search_tool"
    name = "Vector Search & RAG Tool"
    description = "Executes multi-query semantic vector search over LeadForgeAI enterprise knowledge base."
    category = "knowledge"
    version = "1.0.0"
    timeout = 30
    cost_estimate = 0.02
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer"},
        },
        "required": ["query"],
    }

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        query = inputs.get("query", "")
        owner_id = inputs.get("owner_id", "507f1f77bcf86cd799439011")
        top_k = inputs.get("top_k", 5)

        try:
            from app.agents.memory.shared_memory import SharedMemory
            memory = SharedMemory()
            results = await memory.search(query=query, owner_id=owner_id, top_k=top_k)
            return {
                "query": query,
                "total_results": len(results),
                "chunks": [r.model_dump() if hasattr(r, 'model_dump') else dict(r) for r in results],
                "confidence": 88,
            }
        except Exception as e:
            return {
                "query": query,
                "total_results": 0,
                "chunks": [],
                "error": str(e),
                "confidence": 50,
            }
