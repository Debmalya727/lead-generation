from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
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
    description=(
        "## Authentication\n\n"
        "This API uses **JWT Bearer** authentication.\n\n"
        "1. Call `POST /v1/auth/login` with your `email` and `password`.\n"
        "2. Copy the `access_token` from the response.\n"
        "3. Click **Authorize** (🔒) above and paste the token — **without** any `Bearer ` prefix.\n"
    ),
    lifespan=lifespan,
    redirect_slashes=False,
)


def custom_openapi():
    """Override the default OpenAPI schema to expose a single clean HTTP Bearer
    security scheme (RFC 6750).

    FastAPI's HTTPBearer() dependency auto-generates an 'HTTPBearer' scheme entry.
    This function:
      1. Removes that auto-generated entry (and any stale OAuth2 schemes).
      2. Inserts a single, well-described 'BearerAuth' scheme with JWT metadata.
      3. Rewrites every protected operation's security block to reference it.

    Result: Swagger UI shows one 'Authorize' lock with a single 'Value' text field
    for the raw JWT token — no username/password/client_id/client_secret form.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    security_schemes = schema.setdefault("components", {}).setdefault("securitySchemes", {})

    # Remove the auto-generated 'HTTPBearer' scheme FastAPI adds from the
    # HTTPBearer() dependency, and any stale OAuth2 schemes, so only one
    # canonical entry remains in the final spec.
    for stale_key in list(security_schemes.keys()):
        if stale_key != "BearerAuth":
            del security_schemes[stale_key]

    # Declare the single canonical Bearer scheme with full JWT metadata.
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": (
            "Paste the JWT access token returned by `POST /v1/auth/login`. "
            "Do **not** include the `Bearer ` prefix — Swagger adds it automatically."
        ),
    }

    # Rewrite every protected endpoint's security block to reference BearerAuth.
    # Endpoints with no security dependency (login, signup, health) are untouched.
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict) and operation.get("security") is not None:
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


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