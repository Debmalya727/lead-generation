"""
CollaborationMetricsService for Multi-Agent Collaboration Engine.

Calculates operational metrics:
- Agent utilization %
- Execution latency
- Delegation & message counts
- Artifact count
- Consensus & conflict frequencies
- Parallel efficiency
"""
import logging
from typing import Dict, List, Any, Optional

from app.database.mongodb.collections.agent_runtime import AgentJob
from app.database.mongodb.collections.agent_collaboration import (
    AgentMessageDocument,
    AgentArtifactDocument,
    AgentConsensusDocument,
    AgentCollaborationDocument,
)

logger = logging.getLogger("backend.agents.collaboration.metrics")


class CollaborationMetricsService:
    """Service computing multi-agent collaboration metrics."""

    async def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """Compute comprehensive metrics for a specific agent job."""
        msg_count = await AgentMessageDocument.find(AgentMessageDocument.job_id == job_id).count()
        artifact_count = await AgentArtifactDocument.find(AgentArtifactDocument.job_id == job_id).count()
        consensus_count = await AgentConsensusDocument.find(AgentConsensusDocument.job_id == job_id).count()
        conflict_count = await AgentConsensusDocument.find(
            AgentConsensusDocument.job_id == job_id,
            AgentConsensusDocument.is_conflict == True,
        ).count()

        # Fetch AgentJob to inspect execution times and task graph
        from app.database.mongodb.repositories.agent_repository import AgentRepository
        repo = AgentRepository()
        job = await repo.get_job_by_id_no_auth(job_id)

        task_durations: Dict[str, float] = {}
        total_sequential_time = 0.0
        total_job_time = 0.0
        agent_utilization: Dict[str, float] = {}

        if job and job.plan:
            for t in job.plan.tasks:
                task_durations[t.agent_name] = task_durations.get(t.agent_name, 0.0) + t.execution_time_seconds
                total_sequential_time += t.execution_time_seconds

            if job.started_at and job.completed_at:
                total_job_time = (job.completed_at - job.started_at).total_seconds()
            elif job.execution_stats.get("total_duration"):
                total_job_time = float(job.execution_stats["total_duration"])
            else:
                total_job_time = total_sequential_time

            # Compute utilization %
            if total_job_time > 0:
                for agent_name, duration in task_durations.items():
                    agent_utilization[agent_name] = round(min(100.0, (duration / total_job_time) * 100.0), 1)

        # Parallel efficiency: ratio of sequential baseline vs actual parallel time
        parallel_efficiency = round((total_sequential_time / max(0.1, total_job_time)), 2) if total_job_time > 0 else 1.0

        return {
            "job_id": job_id,
            "message_count": msg_count,
            "artifact_count": artifact_count,
            "consensus_count": consensus_count,
            "conflict_count": conflict_count,
            "delegation_count": msg_count // 3 if msg_count > 0 else 0,
            "total_sequential_latency_seconds": round(total_sequential_time, 2),
            "actual_job_latency_seconds": round(total_job_time, 2),
            "parallel_efficiency": parallel_efficiency,
            "agent_utilization_percent": agent_utilization,
        }
