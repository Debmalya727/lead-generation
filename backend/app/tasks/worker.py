import os
from celery import Celery

# Fetch Redis broker URL from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Initialize Celery worker application instance
celery_app = Celery(
    "leadforge_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configure Celery runtime options
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Expose 'celery' attribute for CLI auto-discovery
celery = celery_app

@celery_app.task(name="ping")
def ping():
    """Health check task for worker status inspection."""
    return "pong"


# Register background task modules
import app.tasks.discovery_tasks
import app.tasks.intelligence_tasks
import app.tasks.scoring_tasks
import app.tasks.outreach_tasks
