# This file includes AI-generated code - Review and modify as needed
"""
Exception hierarchy for GCM MCP Relay.

All exceptions inherit from RelayError for easy catching and handling.
"""

from typing import Any, Optional


class RelayError(Exception):
    """Base exception for all GCM MCP Relay errors."""

    def __init__(
        self,
        message: str,
        code: str = "RELAY_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize relay error.

        Args:
            message: Human-readable error message
            code: Machine-readable error code
            details: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# Configuration Errors
class ConfigurationError(RelayError):
    """Configuration loading or validation error."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="CONFIG_ERROR", details=details)


class MissingCredentialsError(ConfigurationError):
    """Required credentials not found in environment."""

    def __init__(self, missing_vars: list[str]):
        message = f"Missing required credentials: {', '.join(missing_vars)}"
        super().__init__(
            message,
            details={"missing_variables": missing_vars},
        )


# Authentication Errors
class AuthenticationError(RelayError):
    """Authentication failure."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="AUTH_ERROR", details=details)


class TokenExpiredError(AuthenticationError):
    """Access token has expired."""

    def __init__(self, message: str = "Access token expired"):
        super().__init__(message, details={"retryable": True})


class TokenRefreshError(AuthenticationError):
    """Failed to refresh access token."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details=details)


# GCM Connection Errors
class GCMConnectionError(RelayError):
    """Failed to connect to GCM MCP server."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="GCM_CONNECTION_ERROR", details=details)


class GCMTimeoutError(GCMConnectionError):
    """GCM request timed out."""

    def __init__(self, message: str = "GCM request timed out"):
        super().__init__(message, details={"retryable": True})


class GCMAPIError(RelayError):
    """GCM API returned an error."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        details = details or {}
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, code="GCM_API_ERROR", details=details)


# Policy Errors
class PolicyError(RelayError):
    """Policy enforcement error."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="POLICY_ERROR", details=details)


class ToolNotAllowedError(PolicyError):
    """Tool not allowed by current policy."""

    def __init__(self, tool_name: str, profile: str):
        message = f"Tool '{tool_name}' not allowed in profile '{profile}'"
        super().__init__(
            message,
            details={"tool_name": tool_name, "profile": profile},
        )


class InvalidToolArgumentsError(PolicyError):
    """Tool arguments failed validation."""

    def __init__(self, tool_name: str, errors: list[str]):
        message = f"Invalid arguments for tool '{tool_name}': {', '.join(errors)}"
        super().__init__(
            message,
            details={"tool_name": tool_name, "validation_errors": errors},
        )


# Tool Errors
class ToolError(RelayError):
    """Tool execution error."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="TOOL_ERROR", details=details)


class ToolNotFoundError(ToolError):
    """Requested tool not found."""

    def __init__(self, tool_name: str):
        message = f"Tool not found: {tool_name}"
        super().__init__(message, details={"tool_name": tool_name})


class ToolExecutionError(ToolError):
    """Tool execution failed."""

    def __init__(
        self,
        tool_name: str,
        error_message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        message = f"Tool '{tool_name}' execution failed: {error_message}"
        details = details or {}
        details["tool_name"] = tool_name
        super().__init__(message, details=details)


# Audit Errors
class AuditError(RelayError):
    """Audit logging error."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="AUDIT_ERROR", details=details)

# Made with Bob
