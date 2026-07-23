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
from app.api.v1.sales_intelligence.router import router as sales_intelligence_router
from app.api.v1.research.router import router as research_router
from app.api.v1.vector.router import router as vector_router
from app.api.v1.rag.router import router as rag_router
from app.agents.routers.router import router as agents_router
from app.agents.routers.workflow_router import router as workflow_router
from app.conversation.routers.chat_router import router as chat_router
from app.platform.routers.platform_router import router as platform_router
from app.scheduler.routers.scheduler_router import router as scheduler_router
from app.notifications.routers.notification_router import router as notification_router
from app.plugins.routers.plugin_router import router as plugin_router
from app.ai.routers.ai_router import router as ai_router
from app.ai.routers.ai_router_extended import router as ai_router_extended
from app.ai.routers.ai_router_orchestrator import router as ai_router_orchestrator
from app.voice.routers.voice_router import router as voice_router
from app.speech.routers.speech_router import router as speech_router
from app.tts.routers.tts_router import router as tts_router
from app.voice.routers.bidirectional_router import router as bidirectional_router
from app.voice.routers.command_router import router as command_router
from app.voice.routers.meeting_router import router as meeting_router
from app.voice.routers.voice_agent_router import router as voice_agent_router
from app.telephony.routers.telephony_router import router as telephony_router
from app.voice.analytics.analytics_router import router as voice_analytics_router
from app.knowledge.routers.knowledge_router import router as knowledge_router
from app.knowledge.gateway.router import router as gateway_router

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
api_router.include_router(sales_intelligence_router, prefix="/sales-intelligence", tags=["sales-intelligence"])
api_router.include_router(research_router, prefix="/research", tags=["research"])
api_router.include_router(vector_router, prefix="/vector", tags=["vector"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(workflow_router, tags=["workflows"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(platform_router, tags=["platform"])
api_router.include_router(scheduler_router, tags=["scheduler"])
api_router.include_router(notification_router, tags=["notifications"])
api_router.include_router(plugin_router, tags=["plugins"])
api_router.include_router(ai_router)
api_router.include_router(ai_router_extended)
api_router.include_router(ai_router_orchestrator)
api_router.include_router(voice_router)
api_router.include_router(speech_router)
api_router.include_router(tts_router)
api_router.include_router(bidirectional_router)
api_router.include_router(command_router)
api_router.include_router(meeting_router)
api_router.include_router(voice_agent_router)
api_router.include_router(telephony_router)
api_router.include_router(voice_analytics_router)
api_router.include_router(knowledge_router)
api_router.include_router(gateway_router)




