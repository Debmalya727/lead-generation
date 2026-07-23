"""
WorkflowEngine for Phase 11 — Milestone 4: Autonomous Workflow & Tool Orchestration Engine.

Orchestrates sequential, parallel, conditional, and tool-driven workflows with:
- Checkpointing & crash recovery
- Policy evaluation
- Step execution tracking
- Resume & cancel states
"""
import uuid
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from bson import ObjectId

from app.agents.tools.tool_executor.executor import ToolExecutor
from app.agents.workflow.checkpoints.checkpoint_engine import CheckpointEngine
from app.agents.workflow.policies.policy_engine import PolicyEngine
from app.agents.workflow.workflow_templates.templates import PREBUILT_WORKFLOW_TEMPLATES
from app.database.mongodb.collections.agent_workflow import (
    WorkflowTemplateDocument,
    WorkflowExecutionDocument,
    WorkflowStepDocument,
)

logger = logging.getLogger("backend.agents.workflow.engine")


class WorkflowEngine:
    """Master Autonomous Workflow Orchestration Engine."""

    def __init__(self):
        self.tool_executor = ToolExecutor()
        self.checkpoint_engine = CheckpointEngine()
        self.policy_engine = PolicyEngine()

    async def run_workflow(
        self,
        workflow_id: str,
        owner_id: str,
        company_name: Optional[str] = None,
        lead_id: Optional[str] = None,
        custom_inputs: Optional[Dict[str, Any]] = None,
        policy_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> WorkflowExecutionDocument:
        """Initialize and execute a workflow by template ID or specification."""
        # 1. Resolve steps from template
        template = next((t for t in PREBUILT_WORKFLOW_TEMPLATES if t["template_id"] == workflow_id), None)
        steps_spec = template["steps"] if template else []
        if not steps_spec:
            # Check DB template
            db_tmpl = await WorkflowTemplateDocument.find_one(WorkflowTemplateDocument.template_id == workflow_id)
            if db_tmpl:
                steps_spec = db_tmpl.steps

        if not steps_spec:
            # Fallback default steps
            steps_spec = [
                {"step_id": "step_01_intel", "name": "Company Intelligence", "step_type": "tool", "target": "company_intelligence_tool", "inputs": {"company_name": "{{company_name}}"}},
                {"step_id": "step_02_research", "name": "Company Research", "step_type": "tool", "target": "research_tool", "inputs": {"company_name": "{{company_name}}"}},
                {"step_id": "step_03_report", "name": "Executive Sales Report", "step_type": "tool", "target": "executive_report_tool", "inputs": {"company_name": "{{company_name}}"}},
            ]

        execution_id = f"wfexec_{uuid.uuid4().hex[:12]}"
        owner_obj_id = ObjectId(owner_id) if ObjectId.is_valid(owner_id) else ObjectId()

        # Build initial context
        context_data = dict(custom_inputs or {})
        if company_name:
            context_data["company_name"] = company_name
        if lead_id:
            context_data["lead_id"] = lead_id

        # 2. Create WorkflowExecutionDocument
        execution_doc = WorkflowExecutionDocument(
            execution_id=execution_id,
            workflow_id=workflow_id,
            owner_id=owner_obj_id,
            job_id=job_id,
            lead_id=lead_id,
            company_name=company_name,
            status="running",
            progress=0.0,
            context_data=context_data,
            started_at=datetime.now(timezone.utc),
        )
        await execution_doc.insert()

        # 3. Create WorkflowStepDocuments
        step_docs: List[WorkflowStepDocument] = []
        for sspec in steps_spec:
            s_doc = WorkflowStepDocument(
                step_execution_id=f"steprec_{uuid.uuid4().hex[:10]}",
                execution_id=execution_id,
                step_id=sspec["step_id"],
                name=sspec["name"],
                step_type=sspec.get("step_type", "tool"),
                target=sspec["target"],
                status="pending",
                inputs=sspec.get("inputs", {}),
            )
            await s_doc.insert()
            step_docs.append(s_doc)

        logger.info(f"WorkflowEngine started execution '{execution_id}' with {len(step_docs)} steps")

        # 4. Execute steps sequentially
        completed_step_ids: List[str] = []
        total_steps = len(step_docs)

        for idx, s_doc in enumerate(step_docs):
            # Refresh execution status check
            refreshed_exec = await WorkflowExecutionDocument.find_one(WorkflowExecutionDocument.execution_id == execution_id)
            if refreshed_exec and refreshed_exec.status in ("cancelled", "paused"):
                logger.info(f"Workflow '{execution_id}' stopped due to status '{refreshed_exec.status}'")
                return refreshed_exec

            execution_doc.current_step_id = s_doc.step_id
            s_doc.status = "running"
            s_doc.started_at = datetime.now(timezone.utc)
            await s_doc.save()

            # Substitute input variables e.g. {{company_name}}
            raw_inputs = dict(s_doc.inputs)
            substituted_inputs = self._substitute_variables(raw_inputs, execution_doc.context_data)

            # Policy check
            pol_res = await self.policy_engine.evaluate_step_policy(
                policy_id=policy_id,
                tool_id=s_doc.target,
                step_inputs=substituted_inputs,
                current_step_count=idx + 1,
            )

            if not pol_res["allowed"]:
                s_doc.status = "failed"
                s_doc.error_message = pol_res["reason"]
                await s_doc.save()
                execution_doc.status = "failed"
                execution_doc.error_message = pol_res["reason"]
                await execution_doc.save()
                return execution_doc

            if pol_res["approval_required"]:
                s_doc.status = "paused_for_approval"
                await s_doc.save()
                execution_doc.status = "paused"
                await execution_doc.save()
                await self.checkpoint_engine.save_checkpoint(
                    execution_id=execution_id,
                    step_id=s_doc.step_id,
                    state_snapshot=execution_doc.context_data,
                    completed_step_ids=completed_step_ids,
                    pending_step_ids=[st.step_id for st in step_docs[idx:]],
                    reason="approval_pause",
                )
                return execution_doc

            # Execute tool
            try:
                res = await self.tool_executor.execute_tool(
                    tool_id=s_doc.target,
                    inputs=substituted_inputs,
                    execution_id=execution_id,
                    step_id=s_doc.step_id,
                )

                if res.get("status") == "success":
                    s_doc.status = "completed"
                    s_doc.outputs = res.get("outputs", {})
                    s_doc.execution_time_seconds = res.get("execution_time_seconds", 0.0)
                    s_doc.completed_at = datetime.now(timezone.utc)
                    await s_doc.save()

                    # Merge outputs into global context_data
                    execution_doc.context_data[f"{s_doc.step_id}_outputs"] = s_doc.outputs
                    execution_doc.context_data.update(s_doc.outputs)
                    completed_step_ids.append(s_doc.step_id)

                    # Update progress
                    progress = round(((idx + 1) / total_steps) * 100.0, 1)
                    execution_doc.progress = progress
                    await execution_doc.save()

                    # Save intermediate checkpoint
                    await self.checkpoint_engine.save_checkpoint(
                        execution_id=execution_id,
                        step_id=s_doc.step_id,
                        state_snapshot=execution_doc.context_data,
                        completed_step_ids=completed_step_ids,
                        pending_step_ids=[st.step_id for st in step_docs[idx+1:]],
                        reason="step_complete",
                    )
                else:
                    s_doc.status = "failed"
                    s_doc.error_message = res.get("error_message", "Step execution failed.")
                    await s_doc.save()
                    execution_doc.status = "failed"
                    execution_doc.error_message = s_doc.error_message
                    await execution_doc.save()
                    return execution_doc

            except Exception as step_err:
                s_doc.status = "failed"
                s_doc.error_message = str(step_err)
                await s_doc.save()
                execution_doc.status = "failed"
                execution_doc.error_message = str(step_err)
                await execution_doc.save()
                return execution_doc

        # Mark execution completed
        execution_doc.status = "completed"
        execution_doc.progress = 100.0
        execution_doc.completed_at = datetime.now(timezone.utc)
        await execution_doc.save()
        logger.info(f"WorkflowEngine execution '{execution_id}' completed successfully")

        return execution_doc

    async def resume_workflow(self, execution_id: str, owner_id: str) -> WorkflowExecutionDocument:
        """Resume a paused or checkpointed workflow execution from its latest checkpoint."""
        execution = await WorkflowExecutionDocument.find_one(WorkflowExecutionDocument.execution_id == execution_id)
        if not execution:
            raise ValueError(f"Workflow execution '{execution_id}' not found.")

        checkpoint = await self.checkpoint_engine.get_latest_checkpoint(execution_id)
        if not checkpoint:
            raise ValueError(f"No checkpoint snapshot found for execution '{execution_id}'.")

        execution.status = "running"
        execution.context_data = checkpoint["state_snapshot"]
        await execution.save()
        logger.info(f"WorkflowEngine resumed execution '{execution_id}' from step '{checkpoint['step_id']}'")

        # Resume pending steps
        pending_step_ids = checkpoint.get("pending_step_ids", [])
        for step_id in pending_step_ids:
            s_doc = await WorkflowStepDocument.find_one(
                WorkflowStepDocument.execution_id == execution_id,
                WorkflowStepDocument.step_id == step_id,
            )
            if not s_doc:
                continue

            s_doc.status = "running"
            await s_doc.save()

            substituted_inputs = self._substitute_variables(s_doc.inputs, execution.context_data)
            res = await self.tool_executor.execute_tool(
                tool_id=s_doc.target,
                inputs=substituted_inputs,
                execution_id=execution_id,
                step_id=s_doc.step_id,
            )

            if res.get("status") == "success":
                s_doc.status = "completed"
                s_doc.outputs = res.get("outputs", {})
                s_doc.completed_at = datetime.now(timezone.utc)
                await s_doc.save()

                execution.context_data.update(s_doc.outputs)
                await execution.save()
            else:
                s_doc.status = "failed"
                await s_doc.save()
                execution.status = "failed"
                await execution.save()
                return execution

        execution.status = "completed"
        execution.progress = 100.0
        execution.completed_at = datetime.now(timezone.utc)
        await execution.save()
        return execution

    async def cancel_workflow(self, execution_id: str, owner_id: str) -> WorkflowExecutionDocument:
        """Cancel a running or pending workflow execution."""
        execution = await WorkflowExecutionDocument.find_one(WorkflowExecutionDocument.execution_id == execution_id)
        if not execution:
            raise ValueError(f"Workflow execution '{execution_id}' not found.")

        execution.status = "cancelled"
        await execution.save()
        logger.info(f"WorkflowEngine cancelled execution '{execution_id}'")
        return execution

    def _substitute_variables(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute string variables like {{company_name}} with context memory values."""
        result = {}
        for k, v in inputs.items():
            if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                var_name = v[2:-2].strip()
                result[k] = context.get(var_name, v)
            else:
                result[k] = v
        return result
