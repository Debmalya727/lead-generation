"""
ArtifactTool — Tool wrapper for ArtifactStore.
"""
from typing import Dict, Any
from app.agents.tools.base import BaseTool
from app.agents.tools.tool_registry.registry import register_tool


@register_tool
class ArtifactTool(BaseTool):
    tool_id = "artifact_tool"
    name = "Shared Artifact Store Tool"
    description = "Saves, versions, and queries shared artifacts across the LeadForgeAI platform."
    category = "artifacts"
    version = "1.0.0"
    timeout = 20
    cost_estimate = 0.01
    input_schema = {
        "type": "object",
        "properties": {
            "job_id": {"type": "string"},
            "action": {"type": "string", "enum": ["save", "get", "list"]},
            "artifact_type": {"type": "string"},
            "content": {"type": "object"},
            "owner_agent": {"type": "string"},
        },
        "required": ["job_id", "action"],
    }

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        job_id = inputs.get("job_id", "")
        action = inputs.get("action", "list")
        art_type = inputs.get("artifact_type")
        content = inputs.get("content", {})
        owner = inputs.get("owner_agent", "System")

        from app.agents.collaboration.artifacts.store import ArtifactStore
        store = ArtifactStore()

        if action == "save" and art_type:
            saved = await store.save_artifact(job_id=job_id, owner_agent=owner, artifact_type=art_type, content=content)
            return {"action": "save", "artifact": saved}
        elif action == "get" and art_type:
            latest = await store.get_latest_artifact(job_id, art_type)
            return {"action": "get", "artifact": latest}
        else:
            items = await store.list_artifacts(job_id, artifact_type=art_type)
            return {"action": "list", "total_artifacts": len(items), "artifacts": items}
