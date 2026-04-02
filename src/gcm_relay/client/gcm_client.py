# This file includes AI-generated code - Review and modify as needed
"""
GCM MCP Client for communicating with GCM's built-in MCP server.

Uses langchain-mcp-adapters with streamable-http transport and Bearer JWT authentication.
Based on IBM GCM MCP Server documentation.
"""

import logging
from typing import Any, Optional

import httpx
from langchain_mcp_adapters.client import MultiServerMCPClient

from gcm_relay.auth.manager import AuthenticationManager
from gcm_relay.config.models import Config
from gcm_relay.exceptions import (
    GCMAPIError,
    GCMConnectionError,
    GCMTimeoutError,
)

logger = logging.getLogger(__name__)


class GCMClient:
    """
    Client for GCM's built-in MCP server.

    Uses langchain-mcp-adapters to communicate with GCM MCP server
    via streamable-http transport with Bearer JWT authentication.
    """

    def __init__(self, config: Config, auth_manager: AuthenticationManager):
        """
        Initialize GCM MCP client.

        Args:
            config: Application configuration
            auth_manager: Authentication manager for token management
        """
        self.config = config
        self.auth_manager = auth_manager
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._gcm_url = config.gcm.get_url()
        self._current_token: Optional[str] = None

    def _create_httpx_client(self, **kwargs) -> httpx.AsyncClient:
        """
        Create httpx client with authentication headers.
        
        This factory is called by langchain-mcp-adapters for each request.
        We inject the Bearer token here.
        
        Note: This is a synchronous function, so we use the pre-fetched token
        stored in self._current_token.
        """
        # Use pre-fetched token
        if not self._current_token:
            raise GCMConnectionError("No access token available - call list_tools() or call_tool() first")
        
        # Remove parameters we'll set explicitly to avoid duplicates
        kwargs.pop("verify", None)
        kwargs.pop("timeout", None)
        
        # Prepare headers with Bearer token
        # Remove headers from kwargs to avoid duplicate argument error
        existing_headers = kwargs.pop("headers", {})
        if isinstance(existing_headers, dict):
            headers = dict(existing_headers)
        else:
            headers = {}
        headers["Authorization"] = f"Bearer {self._current_token}"
        
        # Create client with authentication
        return httpx.AsyncClient(
            verify=self.config.gcm.verify_ssl,
            headers=headers,
            timeout=self.config.gcm.request_timeout,
            **kwargs
        )

    def _build_mcp_config(self) -> dict:
        """
        Build configuration for MultiServerMCPClient.
        
        Returns:
            Configuration dictionary for langchain-mcp-adapters
        """
        return {
            "gcm": {
                "transport": "streamable_http",
                "url": self._gcm_url,
                "httpx_client_factory": self._create_httpx_client,
            }
        }

    async def _get_mcp_client(self) -> MultiServerMCPClient:
        """Get or create MCP client."""
        if self._mcp_client is None:
            logger.info(f"Initializing MCP client for GCM at {self._gcm_url}")
            config = self._build_mcp_config()
            self._mcp_client = MultiServerMCPClient(config)
        return self._mcp_client

    async def close(self) -> None:
        """Close MCP client and cleanup resources."""
        if self._mcp_client:
            # MultiServerMCPClient doesn't have explicit close method
            # Resources are cleaned up automatically
            self._mcp_client = None
            logger.debug("MCP client closed")

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List all available tools from GCM MCP server.

        Returns:
            List of tool definitions from langchain-mcp-adapters

        Raises:
            GCMConnectionError: Connection failed
            GCMAPIError: API returned error
        """
        logger.info("Fetching tool list from GCM MCP server...")
        
        try:
            # Get and store access token for httpx client factory
            self._current_token = await self.auth_manager.get_access_token()
            
            # Get MCP client and fetch tools
            mcp_client = await self._get_mcp_client()
            tools = await mcp_client.get_tools()
            
            logger.info(f"Retrieved {len(tools)} tools from GCM")
            return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools from GCM: {e}")
            raise GCMConnectionError(
                f"Failed to list tools: {e}",
                details={"error": str(e), "url": self._gcm_url}
            )

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Call a tool on GCM MCP server.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            GCMConnectionError: Connection failed
            GCMAPIError: API returned error
        """
        logger.debug(f"Calling tool '{tool_name}' on GCM")

        try:
            # Get and store access token for httpx client factory
            self._current_token = await self.auth_manager.get_access_token()
            
            # Get MCP client
            mcp_client = await self._get_mcp_client()
            
            # Call tool via MCP client
            # Note: langchain-mcp-adapters returns LangChain tool objects
            # We need to invoke them directly
            tools = await mcp_client.get_tools()
            
            # Find the tool
            tool = None
            for t in tools:
                if t.name == tool_name:
                    tool = t
                    break
            
            if not tool:
                raise GCMAPIError(
                    f"Tool '{tool_name}' not found",
                    status_code=404,
                    details={"tool_name": tool_name}
                )
            
            # Invoke the tool
            result = await tool.ainvoke(arguments)
            
            logger.debug(f"Tool '{tool_name}' executed successfully")
            return {"result": result}
            
        except GCMAPIError:
            raise
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}': {e}")
            raise GCMConnectionError(
                f"Failed to call tool: {e}",
                details={"error": str(e), "tool_name": tool_name}
            )

# Made with Bob
