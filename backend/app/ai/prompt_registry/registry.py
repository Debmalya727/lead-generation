"""
Prompt Registry for Phase 12.7B AI Gateway.
Manages prompt lifecycle: Draft → Review → Approved → Production → Deprecated → Archived.
"""
import uuid
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.database.mongodb.collections.ai_gateway_extended import (
    PromptRegistryDocument,
    PromptApprovalDocument,
)

logger = logging.getLogger("backend.ai.prompt_registry.registry")

LIFECYCLE_TRANSITIONS = {
    "draft": ["review"],
    "review": ["approved", "draft"],
    "approved": ["production", "review"],
    "production": ["deprecated"],
    "deprecated": ["archived", "production"],
    "archived": [],
}


class PromptRegistryManager:
    """Manages full prompt lifecycle with versioning and approval audit trail."""

    async def create(
        self,
        name: str,
        user_prompt_template: str,
        category: str = "conversation",
        system_prompt: Optional[str] = None,
        variables: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        created_by: str = "system",
    ) -> PromptRegistryDocument:
        """Create a new prompt in Draft status."""
        registry_id = f"preg_{uuid.uuid4().hex[:12]}"
        doc = PromptRegistryDocument(
            registry_id=registry_id,
            name=name,
            category=category,
            tags=tags or [],
            description=description,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            variables=variables or [],
            status="draft",
            version=1,
            created_by=created_by,
        )
        await doc.insert()
        await self._record_action(registry_id, "create", "system", None, "draft", "draft", 1)
        logger.info(f"PromptRegistry: Created '{name}' (id={registry_id})")
        return doc

    async def transition(
        self,
        registry_id: str,
        action: str,
        performed_by: str = "system",
        comments: Optional[str] = None,
    ) -> PromptRegistryDocument:
        """Transition a prompt through lifecycle states."""
        doc = await PromptRegistryDocument.find_one(PromptRegistryDocument.registry_id == registry_id)
        if not doc:
            raise ValueError(f"Prompt registry entry '{registry_id}' not found.")

        # Map action to target status
        action_to_status = {
            "submit_review": "review",
            "approve": "approved",
            "reject": "draft",
            "promote": "production",
            "deprecate": "deprecated",
            "archive": "archived",
        }

        if action == "rollback":
            # rollback is handled in rollback.py
            raise ValueError("Use rollback() for version rollback.")

        to_status = action_to_status.get(action)
        if not to_status:
            raise ValueError(f"Unknown action '{action}'.")

        allowed = LIFECYCLE_TRANSITIONS.get(doc.status, [])
        if to_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{doc.status}' to '{to_status}' via '{action}'. "
                f"Allowed transitions: {allowed}"
            )

        from_status = doc.status
        doc.status = to_status
        doc.updated_at = datetime.now(timezone.utc)

        if action == "approve":
            doc.approved_by = performed_by
            doc.approved_at = datetime.now(timezone.utc)
        elif action == "promote":
            doc.promoted_to_production_by = performed_by

        await doc.save()
        await self._record_action(registry_id, action, performed_by, comments, from_status, to_status, doc.version)
        return doc

    async def update_content(
        self,
        registry_id: str,
        user_prompt_template: str,
        system_prompt: Optional[str] = None,
        variables: Optional[List[str]] = None,
        performed_by: str = "system",
        changes_description: Optional[str] = None,
    ) -> PromptRegistryDocument:
        """Update prompt content and auto-increment version. Resets status to draft."""
        doc = await PromptRegistryDocument.find_one(PromptRegistryDocument.registry_id == registry_id)
        if not doc:
            raise ValueError(f"Prompt registry entry '{registry_id}' not found.")

        from_status = doc.status
        doc.user_prompt_template = user_prompt_template
        if system_prompt is not None:
            doc.system_prompt = system_prompt
        if variables is not None:
            doc.variables = variables
        doc.version += 1
        doc.status = "draft"  # Reset to draft on content change
        doc.updated_at = datetime.now(timezone.utc)
        await doc.save()

        await self._record_action(
            registry_id, "update_content", performed_by,
            changes_description or f"Content updated to v{doc.version}",
            from_status, "draft", doc.version
        )
        return doc

    async def list_all(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[PromptRegistryDocument]:
        """List prompts with optional status/category filters."""
        query = PromptRegistryDocument.find()
        if status:
            query = PromptRegistryDocument.find(PromptRegistryDocument.status == status)
        if category:
            query = PromptRegistryDocument.find(PromptRegistryDocument.category == category)
        return await query.to_list()

    async def get_history(self, registry_id: str) -> List[PromptApprovalDocument]:
        """Return lifecycle event history for a prompt."""
        return await PromptApprovalDocument.find(
            PromptApprovalDocument.registry_id == registry_id
        ).sort("-timestamp").to_list()

    async def _record_action(
        self,
        registry_id: str,
        action: str,
        performed_by: str,
        comments: Optional[str],
        from_status: str,
        to_status: str,
        version: int,
    ) -> None:
        """Record a lifecycle event in the approval audit log."""
        approval = PromptApprovalDocument(
            approval_id=f"appr_{uuid.uuid4().hex[:12]}",
            registry_id=registry_id,
            action=action,
            performed_by=performed_by,
            comments=comments,
            from_status=from_status,
            to_status=to_status,
            version=version,
        )
        await approval.insert()


prompt_registry_manager = PromptRegistryManager()
