# This file includes AI-generated code - Review and modify as needed
"""
Tool registry for managing available tools.

Maintains a registry of tools from GCM (pass-through, no filtering).
"""

import logging
from typing import Any

from gcm_relay.client.gcm_client import GCMClient
from gcm_relay.exceptions import ToolNotFoundError

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry of available tools from GCM.

    Manages tool discovery and metadata (no policy filtering).
    All tools from GCM are exposed directly - access control is
    enforced by GCM's native RBAC based on the authenticated user.
    """

    def __init__(self, gcm_client: GCMClient):
        """
        Initialize tool registry.

        Args:
            gcm_client: GCM MCP client
        """
        self.gcm_client = gcm_client
        self._tools: dict[str, Any] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize registry by discovering tools from GCM.

        All tools from GCM are registered without filtering.
        Access control is enforced by GCM's RBAC.

        Raises:
            GCMConnectionError: If tool discovery fails
        """
        logger.info("Initializing tool registry...")

        # Discover all tools from GCM
        all_tools = await self.gcm_client.list_tools()
        logger.info(f"Discovered {len(all_tools)} tools from GCM")

        # Build registry (no filtering - pass through all tools)
        # Handle both dict and object (e.g., LangChain StructuredTool)
        self._tools = {}
        for tool in all_tools:
            if isinstance(tool, dict):
                tool_name = tool["name"]
            else:
                # Assume it's an object with .name attribute
                tool_name = tool.name
            self._tools[tool_name] = tool

        self._initialized = True
        logger.info(f"Tool registry initialized with {len(self._tools)} tools")
        logger.info("Access control enforced by GCM RBAC (user-based permissions)")

    def is_initialized(self) -> bool:
        """Check if registry is initialized."""
        return self._initialized

    def get_tool(self, tool_name: str) -> Any:
        """
        Get tool definition by name.

        Args:
            tool_name: Name of tool

        Returns:
            Tool definition (dict or LangChain StructuredTool object)

        Raises:
            ToolNotFoundError: If tool not found in registry
        """
        if not self._initialized:
            raise RuntimeError("Tool registry not initialized")

        tool = self._tools.get(tool_name)
        if not tool:
            raise ToolNotFoundError(tool_name)

        return tool

    def list_tools(self) -> list[Any]:
        """
        List all registered tools.

        Returns:
            List of tool definitions (dict or LangChain StructuredTool objects)
        """
        if not self._initialized:
            raise RuntimeError("Tool registry not initialized")

        return list(self._tools.values())

    def get_tool_names(self) -> list[str]:
        """
        Get list of registered tool names.

        Returns:
            List of tool names
        """
        if not self._initialized:
            raise RuntimeError("Tool registry not initialized")

        return list(self._tools.keys())

    def has_tool(self, tool_name: str) -> bool:
        """
        Check if tool exists in registry.

        Args:
            tool_name: Name of tool

        Returns:
            True if tool exists, False otherwise
        """
        if not self._initialized:
            return False

        return tool_name in self._tools

    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry stats
        """
        if not self._initialized:
            return {
                "initialized": False,
                "total_tools": 0,
            }

        return {
            "initialized": True,
            "total_tools": len(self._tools),
            "access_control": "GCM RBAC (user-based)",
        }


# Made with Bob
