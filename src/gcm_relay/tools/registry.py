# This file includes AI-generated code - Review and modify as needed
"""
Tool registry for managing available tools.

Maintains a registry of tools from GCM with policy-based filtering.
"""

import logging
from typing import Any, Optional

from gcm_relay.client.gcm_client import GCMClient
from gcm_relay.exceptions import ToolNotFoundError
from gcm_relay.policy.engine import PolicyEngine

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry of available tools from GCM.

    Manages tool discovery, filtering, and metadata.
    """

    def __init__(self, gcm_client: GCMClient, policy_engine: PolicyEngine):
        """
        Initialize tool registry.

        Args:
            gcm_client: GCM MCP client
            policy_engine: Policy engine for filtering
        """
        self.gcm_client = gcm_client
        self.policy_engine = policy_engine
        self._tools: dict[str, dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize registry by discovering tools from GCM.

        Raises:
            GCMConnectionError: If tool discovery fails
        """
        logger.info("Initializing tool registry...")

        # Discover tools from GCM
        all_tools = await self.gcm_client.list_tools()
        logger.info(f"Discovered {len(all_tools)} tools from GCM")

        # Filter tools based on policy
        allowed_tools = self.policy_engine.filter_tools(all_tools)
        logger.info(f"Policy allows {len(allowed_tools)} tools")

        # Build registry
        # Handle both dict and object (e.g., LangChain StructuredTool)
        self._tools = {}
        for tool in allowed_tools:
            if isinstance(tool, dict):
                tool_name = tool["name"]
            else:
                # Assume it's an object with .name attribute
                tool_name = tool.name
            self._tools[tool_name] = tool
        self._initialized = True

        logger.info(f"Tool registry initialized with {len(self._tools)} tools")

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

    def get_tools_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Get tools filtered by category.

        Args:
            category: Tool category (readonly, state-changing)

        Returns:
            List of tools in category
        """
        if not self._initialized:
            raise RuntimeError("Tool registry not initialized")

        return [
            tool
            for tool in self._tools.values()
            if tool.get("metadata", {}).get("category") == category
        ]

    def get_tools_by_risk_level(self, risk_level: str) -> list[dict[str, Any]]:
        """
        Get tools filtered by risk level.

        Args:
            risk_level: Risk level (safe, moderate, high)

        Returns:
            List of tools with specified risk level
        """
        if not self._initialized:
            raise RuntimeError("Tool registry not initialized")

        return [
            tool
            for tool in self._tools.values()
            if tool.get("metadata", {}).get("risk_level") == risk_level
        ]

    def get_readonly_tools(self) -> list[dict[str, Any]]:
        """
        Get all read-only tools.

        Returns:
            List of read-only tools
        """
        return self.get_tools_by_category("readonly")

    def get_state_changing_tools(self) -> list[dict[str, Any]]:
        """
        Get all state-changing tools.

        Returns:
            List of state-changing tools
        """
        return self.get_tools_by_category("state-changing")

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

        readonly_count = len(self.get_readonly_tools())
        state_changing_count = len(self.get_state_changing_tools())

        return {
            "initialized": True,
            "total_tools": len(self._tools),
            "readonly_tools": readonly_count,
            "state_changing_tools": state_changing_count,
            "active_profile": self.policy_engine.config.profile,
        }

# Made with Bob
