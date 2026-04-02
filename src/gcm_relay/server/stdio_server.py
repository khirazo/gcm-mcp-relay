# This file includes AI-generated code - Review and modify as needed
"""
stdio MCP server implementation.

Implements MCP protocol over stdin/stdout for local AI agents.
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from typing import Any, Optional

from gcm_relay.audit.logger import AuditLogger
from gcm_relay.auth.manager import AuthenticationManager
from gcm_relay.client.gcm_client import GCMClient
from gcm_relay.config.models import Config
from gcm_relay.exceptions import RelayError, ToolNotAllowedError
from gcm_relay.policy.engine import PolicyEngine
from gcm_relay.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class StdioMCPServer:
    """
    stdio MCP server for local AI agents.

    Implements MCP protocol over stdin/stdout.
    """

    def __init__(
        self,
        config: Config,
        auth_manager: AuthenticationManager,
        gcm_client: GCMClient,
        policy_engine: PolicyEngine,
        tool_registry: ToolRegistry,
        audit_logger: AuditLogger,
    ):
        """
        Initialize stdio MCP server.

        Args:
            config: Application configuration
            auth_manager: Authentication manager
            gcm_client: GCM MCP client
            policy_engine: Policy engine
            tool_registry: Tool registry
            audit_logger: Audit logger
        """
        self.config = config
        self.auth_manager = auth_manager
        self.gcm_client = gcm_client
        self.policy_engine = policy_engine
        self.tool_registry = tool_registry
        self.audit_logger = audit_logger
        self._running = False

    async def initialize(self) -> None:
        """Initialize server components."""
        logger.info("Initializing stdio MCP server...")

        # Initialize tool registry
        await self.tool_registry.initialize()

        logger.info("stdio MCP server initialized")

    async def handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Handle MCP initialize request.

        Args:
            params: Initialize parameters

        Returns:
            Initialize response
        """
        logger.info("Handling initialize request")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": "gcm-mcp-relay",
                "version": "0.1.0",
            },
        }

    async def handle_list_tools(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Handle MCP list_tools request.

        Args:
            params: Request parameters

        Returns:
            List of available tools
        """
        logger.info("Handling list_tools request")

        tools = self.tool_registry.list_tools()

        # Convert to MCP tool format
        # Handle both dict and object (e.g., LangChain StructuredTool)
        mcp_tools = []
        for tool in tools:
            if isinstance(tool, dict):
                # Tool is already a dict
                mcp_tool = {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "inputSchema": tool.get("inputSchema", {"type": "object"}),
                }
            else:
                # Tool is an object (e.g., StructuredTool)
                # Extract properties from the object
                mcp_tool = {
                    "name": getattr(tool, "name", "unknown"),
                    "description": getattr(tool, "description", ""),
                    "inputSchema": getattr(tool, "args_schema", {
                        "type": "object",
                        "properties": {},
                    }),
                }
                # Convert Pydantic schema to JSON schema if needed
                if hasattr(mcp_tool["inputSchema"], "schema"):
                    mcp_tool["inputSchema"] = mcp_tool["inputSchema"].schema()
            
            mcp_tools.append(mcp_tool)

        return {"tools": mcp_tools}

    async def handle_call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Handle MCP call_tool request.

        Args:
            params: Request parameters with tool name and arguments

        Returns:
            Tool execution result
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        request_id = str(uuid.uuid4())

        logger.info(f"Handling call_tool request: {tool_name}")

        # Validate tool is allowed
        try:
            self.policy_engine.validate_tool_call(tool_name)
        except ToolNotAllowedError as e:
            # Log policy violation
            self.audit_logger.log_policy_violation(
                tool_name=tool_name,
                user_id=self.config.gcm.auth.username,
                profile=self.policy_engine.config.profile,
                reason=str(e),
            )
            raise

        # Log invocation start
        start_time = time.time()
        self.audit_logger.log_tool_invocation_start(
            tool_name=tool_name,
            arguments=arguments,
            user_id=self.config.gcm.auth.username,
            request_id=request_id,
        )

        try:
            # Call tool on GCM
            result = await self.gcm_client.call_tool(tool_name, arguments)

            # Log invocation end (success)
            duration_ms = (time.time() - start_time) * 1000
            self.audit_logger.log_tool_invocation_end(
                tool_name=tool_name,
                request_id=request_id,
                success=True,
                result=result,
                duration_ms=duration_ms,
            )

            # Return result in MCP format
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2),
                    }
                ]
            }

        except Exception as e:
            # Log invocation end (failure)
            duration_ms = (time.time() - start_time) * 1000
            self.audit_logger.log_tool_invocation_end(
                tool_name=tool_name,
                request_id=request_id,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )
            raise

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Handle MCP request.

        Args:
            request: MCP request

        Returns:
            MCP response
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_list_tools(params)
            elif method == "tools/call":
                result = await self.handle_call_tool(params)
            else:
                raise ValueError(f"Unknown method: {method}")

            # Success response
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }

        except RelayError as e:
            # Known error
            logger.error(f"Request failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": e.message,
                    "data": e.to_dict(),
                },
            }

        except Exception as e:
            # Unknown error
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"error": str(e)},
                },
            }

    async def run(self) -> None:
        """Run stdio MCP server."""
        logger.info("Starting stdio MCP server...")
        self._running = True

        try:
            # Read from stdin, write to stdout
            while self._running:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    # EOF reached
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON-RPC request
                    request = json.loads(line)

                    # Handle request
                    response = await self.handle_request(request)

                    # Write response to stdout
                    response_line = json.dumps(response)
                    print(response_line, flush=True)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                            "data": {"error": str(e)},
                        },
                    }
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self._running = False
            logger.info("stdio MCP server stopped")

    async def stop(self) -> None:
        """Stop stdio MCP server."""
        logger.info("Stopping stdio MCP server...")
        self._running = False

# Made with Bob
