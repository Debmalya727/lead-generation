"""
AI Workflow Orchestrator — WorkflowRegistry for templates and workflows.
"""
from typing import Dict, List, Optional, Any
import logging

from app.ai.orchestrator.workflow_templates import BUILTIN_PIPELINE_TEMPLATES
from app.database.mongodb.collections.ai_orchestrator import (
    AIWorkflowDocument,
    AIPipelineTemplateDocument,
)

logger = logging.getLogger("backend.ai.orchestrator.registry")


class WorkflowRegistry:
    """Manages workflow definitions and pipeline template registries."""

    _templates: Dict[str, Dict[str, Any]] = {
        t["template_id"]: t for t in BUILTIN_PIPELINE_TEMPLATES
    }

    async def seed(self) -> None:
        """Seed pipeline templates into MongoDB if empty."""
        count = await AIPipelineTemplateDocument.count()
        if count == 0:
            for tpl in BUILTIN_PIPELINE_TEMPLATES:
                doc = AIPipelineTemplateDocument(
                    template_id=tpl["template_id"],
                    name=tpl["name"],
                    description=tpl["description"],
                    category=tpl["category"],
                    workflow_spec=tpl["workflow_spec"],
                    is_built_in=True,
                )
                await doc.insert()
            logger.info(f"WorkflowRegistry: Seeded {len(BUILTIN_PIPELINE_TEMPLATES)} pipeline templates.")

    def list_templates(self) -> List[Dict[str, Any]]:
        """Return all built-in pipeline templates."""
        return list(self._templates.values())

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID."""
        return self._templates.get(template_id)

    async def register_workflow(
        self,
        workflow_id: str,
        name: str,
        initial_node_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        description: Optional[str] = None,
        category: str = "custom",
    ) -> AIWorkflowDocument:
        """Register a new custom workflow in MongoDB."""
        doc = AIWorkflowDocument(
            workflow_id=workflow_id,
            name=name,
            description=description,
            category=category,
            initial_node_id=initial_node_id,
            nodes=nodes,
            edges=edges,
        )
        await doc.insert()
        logger.info(f"WorkflowRegistry: Registered workflow '{workflow_id}'")
        return doc

    async def get_workflow_spec(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Lookup workflow spec by ID or template_id."""
        if workflow_id in self._templates:
            return self._templates[workflow_id]["workflow_spec"]

        doc = await AIWorkflowDocument.find_one(AIWorkflowDocument.workflow_id == workflow_id)
        if doc:
            return {
                "workflow_id": doc.workflow_id,
                "name": doc.name,
                "initial_node_id": doc.initial_node_id,
                "nodes": doc.nodes,
                "edges": doc.edges,
            }
        return None

    async def list_workflows(self) -> List[AIWorkflowDocument]:
        """List custom workflows in MongoDB."""
        return await AIWorkflowDocument.find_all().to_list()



workflow_registry = WorkflowRegistry()
