"""
REST API Router for Plugin SDK Marketplace.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.database.mongodb.collections.user import User
from app.plugins.plugin_registry import plugin_registry

router = APIRouter()


class InstallPluginRequest(BaseModel):
    plugin_id: str


class TogglePluginRequest(BaseModel):
    is_enabled: bool


@router.get(
    "/plugins",
    summary="List Marketplace Plugins",
    description="Fetches all available and installed enterprise SDK plugins.",
)
async def list_plugins(current_user: User = Depends(get_current_user)):
    """List available plugins."""
    return await plugin_registry.list_available_plugins()


@router.post(
    "/plugins/install",
    summary="Install Enterprise Plugin",
    description="Installs a plugin tool into the user's platform workspace.",
)
async def install_plugin(payload: InstallPluginRequest, current_user: User = Depends(get_current_user)):
    """Install plugin."""
    try:
        return await plugin_registry.install_plugin(plugin_id=payload.plugin_id, user_id=str(current_user.id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/plugins/{plugin_id}/toggle",
    summary="Toggle Plugin Status",
    description="Enables or disables an installed plugin.",
)
async def toggle_plugin(plugin_id: str, payload: TogglePluginRequest, current_user: User = Depends(get_current_user)):
    """Toggle plugin status."""
    try:
        return await plugin_registry.toggle_plugin(plugin_id=plugin_id, is_enabled=payload.is_enabled)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
