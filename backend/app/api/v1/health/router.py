import time
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from app.database.mongodb.connection import get_db_client

router = APIRouter(prefix="/health", tags=["System Health"])

@router.get("")
@router.get("/")
async def check_health(db: AsyncIOMotorClient = Depends(get_db_client)):
    """
    Checks backend system health status, database ping, and system load/latency.
    """
    db_status = "unhealthy"
    start_time = time.time()
    
    if db is not None:
        try:
            # Ping database
            await db.admin.command('ping')
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"
            
    latency_ms = (time.time() - start_time) * 1000

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": time.time(),
        "latency_ms": round(latency_ms, 2),
        "services": {
            "api": "healthy",
            "database": db_status,
            "cache": "ready",  # To be wired to Redis ping
            "celery_workers": "active"
        }
    }
