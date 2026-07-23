"""
PluginRegistry for Section 14: Plugin SDK Architecture.

Manages automatic discovery, lifecycle management (install, enable, disable, upgrade, uninstall),
and ToolRegistry integration.
"""
import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime, timezone

from app.plugins.base_plugin import BasePluginTool
from app.plugins.plugins_impl import (
    SalesforcePlugin,
    HubSpotPlugin,
    GmailPlugin,
    SlackPlugin,
    JiraPlugin,
    CustomWebhookPlugin,
)
from app.agents.tools.tool_registry.registry import ToolRegistry
from app.database.mongodb.collections.platform_extended import (
    InstalledPluginDocument,
    PluginSettingsDocument,
)

logger = logging.getLogger("backend.plugins.registry")


class PluginRegistry:
    """Central registry managing enterprise plugin SDK lifecycle."""

    _instance: Optional["PluginRegistry"] = None

    BUILTIN_PLUGINS: Dict[str, Type[BasePluginTool]] = {
        "salesforce": SalesforcePlugin,
        "hubspot": HubSpotPlugin,
        "gmail": GmailPlugin,
        "slack": SlackPlugin,
        "jira": JiraPlugin,
        "custom": CustomWebhookPlugin,
    }

    def __init__(self):
        self._instances: Dict[str, BasePluginTool] = {}
        self._register_builtin_tools()

    @classmethod
    def get_instance(cls) -> "PluginRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _register_builtin_tools(self):
        """Instantiate and register all built-in plugins into ToolRegistry."""
        for plugin_id, plugin_cls in self.BUILTIN_PLUGINS.items():
            instance = plugin_cls()
            self._instances[plugin_id] = instance
            ToolRegistry.register(plugin_cls)
            logger.info(f"PluginRegistry: Registered tool '{instance.name}' (plugin: '{plugin_id}') into ToolRegistry")

    async def list_available_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins and their installation status."""
        result = []
        for plugin_id, instance in self._instances.items():
            installed_doc = None
            try:
                installed_doc = await InstalledPluginDocument.find_one(InstalledPluginDocument.plugin_id == plugin_id)
            except Exception:
                pass

            result.append({
                "plugin_id": plugin_id,
                "name": instance.name.replace("_", " ").title(),
                "description": instance.description,
                "version": instance.version,
                "category": instance.category,
                "is_installed": installed_doc is not None,
                "is_enabled": installed_doc.is_enabled if installed_doc else True,
            })
        return result

    async def install_plugin(self, plugin_id: str, user_id: str) -> InstalledPluginDocument:
        """Install a plugin and register it in MongoDB."""
        if plugin_id not in self._instances:
            raise ValueError(f"Plugin with ID '{plugin_id}' not found in SDK registry.")

        instance = self._instances[plugin_id]
        instance.install(user_id)

        doc = await InstalledPluginDocument.find_one(InstalledPluginDocument.plugin_id == plugin_id)
        if not doc:
            doc = InstalledPluginDocument(
                plugin_id=plugin_id,
                name=instance.name.replace("_", " ").title(),
                version=instance.version,
                category=instance.category,
                is_enabled=True,
                status="installed",
                installed_by=user_id,
                installed_at=datetime.now(timezone.utc),
            )
            await doc.insert()

        logger.info(f"PluginRegistry: Installed plugin '{plugin_id}' by user '{user_id}'")
        return doc

    async def toggle_plugin(self, plugin_id: str, is_enabled: bool) -> InstalledPluginDocument:
        """Enable or disable an installed plugin."""
        doc = await InstalledPluginDocument.find_one(InstalledPluginDocument.plugin_id == plugin_id)
        if not doc:
            raise ValueError(f"Installed plugin '{plugin_id}' not found.")

        doc.is_enabled = is_enabled
        doc.status = "active" if is_enabled else "disabled"
        await doc.save()

        logger.info(f"PluginRegistry: Toggled plugin '{plugin_id}' is_enabled={is_enabled}")
        return doc


# Global singleton instance
plugin_registry = PluginRegistry.get_instance()
