from fastapi import APIRouter
from app.api.v1.auth.router import router as auth_router
from app.api.v1.users.router import router as users_router
from app.api.v1.leads.router import router as leads_router
from app.api.v1.discovery.router import router as discovery_router
from app.api.v1.intelligence.router import router as intelligence_router
from app.api.v1.scoring.router import router as scoring_router
from app.api.v1.outreach.router import router as outreach_router
from app.api.v1.tracking.router import router as tracking_router
from app.api.v1.health.router import router as health_router

# Unified v1 router
api_router = APIRouter()

# Include sub-modules routes
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
api_router.include_router(discovery_router, prefix="/discovery", tags=["discovery"])
api_router.include_router(intelligence_router, prefix="/intelligence", tags=["intelligence"])
api_router.include_router(scoring_router, prefix="/scoring", tags=["scoring"])
api_router.include_router(outreach_router, prefix="/outreach", tags=["outreach"])
api_router.include_router(tracking_router, prefix="/tracking", tags=["tracking"])
