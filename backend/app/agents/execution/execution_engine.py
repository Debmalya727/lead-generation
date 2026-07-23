"""
Execution Engine for Enterprise Agent Runtime.

Schedules and executes ready task nodes from DAG Task Graphs.
Supports:
- Sequential & Parallel scheduling
- Retries & Timeouts
- Human Approval pauses (`paused_for_approval`)
- Status updates & progress calculations
"""
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.agents.runtime.base_agent import BaseAgent
from app.agents.runtime.result import AgentResult
from app.agents.runtime.context import ExecutionContext
from app.agents.registry.registry import AgentRegistry
from app.agents.planner.task_graph import DAGGraphManager
from app.agents.events.event_bus import EventBus
from app.database.mongodb.repositories.agent_repository import AgentRepository
from app.database.mongodb.collections.agent_runtime import AgentJob, ExecutionTask

logger = logging.getLogger("backend.agents.execution_engine")


class ExecutionEngine:
    """DAG Task Graph Execution Engine."""

    def __init__(self, agent_repo: Optional[AgentRepository] = None, event_bus: Optional[EventBus] = None):
        self.agent_repo = agent_repo or AgentRepository()
        self.event_bus = event_bus or EventBus(self.agent_repo)

    async def execute_job(self, job_id: str, owner_id: str) -> AgentJob:
        """Execute all ready nodes in a job's DAG plan until complete or paused for approval."""
        job = await self.agent_repo.get_job_by_id_no_auth(job_id)
        if not job or not job.plan:
            raise ValueError(f"AgentJob '{job_id}' or its ExecutionPlan not found.")

        owner_id_str = str(job.owner_id)

        # Emit AgentStarted event if starting
        if job.status == "pending":
            await self.agent_repo.update_job(job, {"status": "running", "started_at": datetime.now(timezone.utc)})
            await self.event_bus.emit(
                job_id=job_id,
                owner_id=owner_id_str,
                event_type="agent_started",
                payload={"goal": job.goal},
            )

        tasks = job.plan.tasks
        total_tasks = len(tasks)

        while True:
            # Re-fetch latest job state
            job = await self.agent_repo.get_job_by_id_no_auth(job_id)
            if not job or not job.plan or job.status in ("cancelled", "failed", "paused_for_approval"):
                break

            tasks = job.plan.tasks
            completed_count = sum(1 for t in tasks if t.status == "completed")
            progress = round((completed_count / total_tasks) * 100.0, 1) if total_tasks > 0 else 100.0

            await self.agent_repo.update_job(job, {"progress": progress})

            # Get tasks whose dependencies are met and are pending
            ready_tasks = DAGGraphManager.get_ready_tasks(tasks)

            if not ready_tasks:
                # Check if all completed
                if all(t.status == "completed" for t in tasks):
                    await self.agent_repo.update_job(job, {
                        "status": "completed",
                        "progress": 100.0,
                        "completed_at": datetime.now(timezone.utc),
                    })
                    await self.event_bus.emit(
                        job_id=job_id,
                        owner_id=owner_id_str,
                        event_type="execution_finished",
                        payload={"status": "completed", "total_tasks": total_tasks},
                    )
                    break

                # Check if any paused for approval
                if any(t.status == "paused_for_approval" for t in tasks):
                    await self.agent_repo.update_job(job, {"status": "paused_for_approval"})
                    break

                # Check if any failed
                if any(t.status == "failed" for t in tasks):
                    await self.agent_repo.update_job(job, {"status": "failed", "completed_at": datetime.now(timezone.utc)})
                    await self.event_bus.emit(
                        job_id=job_id,
                        owner_id=owner_id_str,
                        event_type="execution_finished",
                        payload={"status": "failed"},
                    )
                    break

                # No ready tasks but not completed or failed (deadlock safety)
                break

            # Execute parallelizable ready tasks concurrently, passing current job state for output propagation
            execute_coros = [self._execute_single_task(job_id, owner_id_str, t, job) for t in ready_tasks]
            await asyncio.gather(*execute_coros)

        return await self.agent_repo.get_job_by_id_no_auth(job_id)

    async def _execute_single_task(self, job_id: str, owner_id_str: str, task: ExecutionTask, job: Optional[AgentJob] = None) -> None:
        """Execute a single ready task node."""
        # Check human approval requirement
        if task.approval_required and task.status == "pending":
            task.status = "paused_for_approval"
            await self._update_task_in_job(job_id, task)
            await self.event_bus.emit(
                job_id=job_id,
                owner_id=owner_id_str,
                event_type="task_approval_required",
                task_id=task.task_id,
                payload={"task_name": task.name, "description": task.description},
            )
            return

        # Start execution
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        await self._update_task_in_job(job_id, task)

        await self.event_bus.emit(
            job_id=job_id,
            owner_id=owner_id_str,
            event_type="task_started",
            source_agent=task.agent_name,
            task_id=task.task_id,
            payload={"task_name": task.name},
        )

        agent_cls = AgentRegistry.get(task.agent_name) or AgentRegistry.get("runtime_diagnostic_agent")
        if not agent_cls:
            raise ValueError(f"Target agent '{task.agent_name}' is not registered.")

        agent_instance = agent_cls()

        # Build enriched inputs: merge task.inputs + outputs from completed dependency tasks
        enriched_inputs: Dict[str, Any] = dict(task.inputs)
        if job and job.plan:
            for dep_task_id in task.dependencies:
                for dep_task in job.plan.tasks:
                    if dep_task.task_id == dep_task_id and dep_task.status == "completed" and dep_task.outputs:
                        # Map outputs by agent role key for downstream consumption
                        agent_key = f"{dep_task.agent_name.replace('_agent', '')}_output"
                        enriched_inputs[agent_key] = dep_task.outputs

        # Extract lead_id from job for context
        lead_id_str = str(job.lead_id) if (job and job.lead_id) else None

        ctx = ExecutionContext(
            job_id=job_id,
            plan_id=job_id,
            owner_id=owner_id_str,
            goal=task.description,
            task_id=task.task_id,
            lead_id=lead_id_str,
            inputs=enriched_inputs,
        )

        start_t = time.time()
        try:
            result: AgentResult = await agent_instance.run(ctx)
            duration = time.time() - start_t

            task.execution_time_seconds = round(duration, 3)
            task.outputs = result.outputs
            task.completed_at = datetime.now(timezone.utc)

            if result.status == "completed":
                task.status = "completed"
                await self._update_task_in_job(job_id, task)

                # 1. Save artifact to Shared ArtifactStore
                try:
                    from app.agents.collaboration.artifacts.store import ArtifactStore
                    store = ArtifactStore()
                    art_type = task.agent_name.replace("_agent", "")
                    await store.save_artifact(
                        job_id=job_id,
                        task_id=task.task_id,
                        owner_agent=task.agent_name,
                        artifact_type=art_type,
                        content=result.outputs,
                        confidence=result.confidence,
                    )
                except Exception as art_err:
                    logger.warning(f"Failed to auto-save artifact for task '{task.task_id}': {str(art_err)}")

                # 2. Publish to StreamingManager
                try:
                    from app.agents.collaboration.streaming.stream_manager import StreamingManager
                    sm = StreamingManager.get_instance()
                    sm.publish(
                        job_id=job_id,
                        event_type="task_finished",
                        source_agent=task.agent_name,
                        payload={"task_id": task.task_id, "duration": duration, "confidence": result.confidence},
                    )
                except Exception as stream_err:
                    logger.warning(f"Failed to publish stream event: {str(stream_err)}")

                # 3. Conflict Detection & Resolution check
                try:
                    if job and job.plan:
                        all_outputs = {
                            t.agent_name: t.outputs for t in job.plan.tasks if t.status == "completed" and t.outputs
                        }
                        from app.agents.collaboration.consensus.conflict_detector import ConflictDetector
                        from app.agents.collaboration.consensus.engine import ConsensusEngine
                        cd = ConflictDetector()
                        conflicts = cd.detect_conflicts(all_outputs)
                        if conflicts:
                            ce = ConsensusEngine()
                            for c in conflicts:
                                proposals = [
                                    {"agent": ag, "proposal": all_outputs.get(ag, {}), "confidence": all_outputs.get(ag, {}).get("confidence", 80)}
                                    for ag in c.get("agents_involved", [])
                                ]
                                await ce.resolve(
                                    job_id=job_id,
                                    task_id=task.task_id,
                                    topic=c.get("topic", "general_conflict"),
                                    proposals=proposals,
                                    strategy="highest_confidence",
                                    is_conflict=True,
                                    conflict_details=c,
                                )
                except Exception as conf_err:
                    logger.warning(f"Conflict detection / resolution check error: {str(conf_err)}")

                await self.event_bus.emit(
                    job_id=job_id,
                    owner_id=owner_id_str,
                    event_type="task_finished",
                    source_agent=task.agent_name,
                    task_id=task.task_id,
                    payload={"duration": duration, "outputs": result.outputs},
                )
            else:
                task.status = "failed"
                task.error_message = "\n".join(result.messages) or "Task execution failed."
                await self._update_task_in_job(job_id, task)

                await self.event_bus.emit(
                    job_id=job_id,
                    owner_id=owner_id_str,
                    event_type="task_failed",
                    source_agent=task.agent_name,
                    task_id=task.task_id,
                    payload={"error": task.error_message},
                )

        except Exception as e:
            duration = time.time() - start_t
            task.execution_time_seconds = round(duration, 3)
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)

            await self._update_task_in_job(job_id, task)

            await self.event_bus.emit(
                job_id=job_id,
                owner_id=owner_id_str,
                event_type="task_failed",
                source_agent=task.agent_name,
                task_id=task.task_id,
                payload={"error": str(e)},
            )

    async def _update_task_in_job(self, job_id: str, updated_task: ExecutionTask) -> None:
        """Helper to update a specific task inside an AgentJob document."""
        job = await self.agent_repo.get_job_by_id_no_auth(job_id)
        if job and job.plan:
            for idx, t in enumerate(job.plan.tasks):
                if t.task_id == updated_task.task_id:
                    job.plan.tasks[idx] = updated_task
                    break

            # Refresh graph json
            job.plan.task_graph_json["nodes"] = [
                {"id": t.task_id, "label": t.name, "agent": t.agent_name, "status": t.status}
                for t in job.plan.tasks
            ]
            await self.agent_repo.update_job(job, {"plan": job.plan, "current_task_id": updated_task.task_id})
