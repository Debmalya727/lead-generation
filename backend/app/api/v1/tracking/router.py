"""
Tracking REST API Router.

Public endpoints for:
- 1x1 Transparent pixel open tracking (/open/{token}.png)
- Click redirect tracking (/click/{token})
"""
import urllib.parse
from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from app.api.deps import get_tracking_module
from app.modules.outreach.outreach_module import TrackingModule

router = APIRouter()


@router.get("/open/{token}.png", summary="1x1 Transparent tracking pixel")
async def track_email_open(
    token: str,
    request: Request,
    tracking_module: TrackingModule = Depends(get_tracking_module),
):
    """Record email open event and return 1x1 transparent PNG/GIF."""
    user_agent = request.headers.get("user-agent", "")
    client_ip = request.client.host if request.client else ""

    gif_bytes = await tracking_module.track_open(token, user_agent=user_agent, ip=client_ip)

    return Response(
        content=gif_bytes,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/click/{token}", summary="Click link tracking redirect")
async def track_email_click(
    token: str,
    request: Request,
    target: str = Query(..., description="Target encoded URL"),
    tracking_module: TrackingModule = Depends(get_tracking_module),
):
    """Record email link click event and redirect to target URL."""
    user_agent = request.headers.get("user-agent", "")
    client_ip = request.client.host if request.client else ""
    target_url = urllib.parse.unquote(target)

    dest_url = await tracking_module.track_click(
        token=token,
        target_url=target_url,
        user_agent=user_agent,
        ip=client_ip,
    )

    return RedirectResponse(url=dest_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
