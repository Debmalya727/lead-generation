from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1 import api_router
from app.config.settings import settings
from app.database.mongodb.connection import DatabaseManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle context manager handling MongoDB connections on startup and shutdown."""
    # Startup lifecycle hooks
    await DatabaseManager.initialize()
    yield
    # Shutdown lifecycle hooks
    await DatabaseManager.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    redirect_slashes=False,
)


@app.get("/")
async def root():
    """Service status checking root endpoint."""
    return {
        "application": settings.APP_NAME,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Container health checker target endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/version")
async def version():
    """Application build version checker endpoint."""
    return {
        "version": settings.APP_VERSION,
    }


# Include unified API routing mapping
app.include_router(api_router, prefix="/v1")