"""
Celery Background Worker Tasks for Phase 11 — Milestone 1: Enterprise Agent Runtime.
"""
import asyncio
import logging
from celery import shared_task

logger = logging.getLogger("backend.agents.tasks")


async def _async_run_agent_job(job_id_str: str, owner_id_str: str):
    """Internal async task executing DAG scheduler for job_id."""
    from app.database.mongodb.connection import DatabaseManager
    from app.database.mongodb.repositories.agent_repository import AgentRepository
    from app.agents.execution.execution_engine import ExecutionEngine

    # Force re-initialization of motor DB client for worker thread
    DatabaseManager.client = None
    await DatabaseManager.initialize()

    agent_repo = AgentRepository()
    engine = ExecutionEngine(agent_repo)

    try:
        await engine.execute_job(job_id_str, owner_id_str)
        logger.info(f"Celery worker finished execute_job for '{job_id_str}'")
    except Exception as e:
        logger.exception(f"Error executing agent job task for '{job_id_str}': {str(e)}")


@shared_task(name="app.agents.tasks.agent_tasks.run_agent_job_task", bind=True, max_retries=2)
def run_agent_job_task(self, job_id_str: str, owner_id_str: str):
    """Celery task entrypoint executing DAG Task Graph."""
    logger.info(f"Celery worker received run_agent_job_task for job_id '{job_id_str}'")
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_async_run_agent_job(job_id_str, owner_id_str))
