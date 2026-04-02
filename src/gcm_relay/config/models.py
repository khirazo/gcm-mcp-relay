# This file includes AI-generated code - Review and modify as needed
"""
Configuration data models using Pydantic.

These models define the structure and validation rules for all configuration.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class RelayConfig(BaseModel):
    """Relay server configuration."""

    mode: Literal["stdio", "http"] = Field(
        default="stdio",
        description="Transport mode: stdio for local, http for remote",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application log level",
    )
    profile: str = Field(
        default="readonly",
        description="Active policy profile (readonly/ops/admin)",
    )


class RelayHttpConfig(BaseModel):
    """HTTP mode configuration (Phase 2)."""

    host: str = Field(default="0.0.0.0", description="HTTP server bind address")
    port: int = Field(default=8002, ge=1, le=65535, description="HTTP server port")
    enable_cors: bool = Field(default=True, description="Enable CORS")
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )


class GCMOIDCConfig(BaseModel):
    """OIDC Provider (Keycloak) configuration."""

    host: str = Field(
        default="",
        description="OIDC host (empty = use GCM host). Can be same as GCM host or different (e.g., keycloak.example.com)",
    )
    port: int = Field(
        default=30443,
        ge=1,
        le=65535,
        description="OIDC provider port",
    )
    realm: str = Field(
        default="master",
        description="Keycloak realm",
    )

    def get_host(self, gcm_host: str) -> str:
        """
        Get OIDC host, using GCM host as fallback.
        
        Args:
            gcm_host: GCM server hostname to use as fallback
            
        Returns:
            OIDC host (either configured or GCM host)
        """
        return self.host if self.host else gcm_host


class GCMAuthConfig(BaseModel):
    """GCM authentication configuration."""

    username: str = Field(
        default="",
        description="GCM username (set via GCM_USERNAME env var)",
    )
    password: str = Field(
        default="",
        description="GCM password (set via GCM_PASSWORD env var)",
    )
    client_id: str = Field(
        default="gcmclient",
        description="OAuth2 client ID",
    )
    client_secret: str = Field(
        default="",
        description="OAuth2 client secret (set via GCM_CLIENT_SECRET env var)",
    )
    auth_mode: Literal["auto", "oauth2", "browser"] = Field(
        default="auto",
        description="Authentication mode",
    )


class GCMConfig(BaseModel):
    """GCM MCP server connection configuration."""

    url: str = Field(
        default="",
        description="GCM MCP server URL (https://host:port/ibm/mcp/mcp)",
    )
    host: str = Field(
        default="localhost",
        description="GCM server hostname",
    )
    api_port: int = Field(
        default=31443,
        ge=1,
        le=65535,
        description="GCM API port",
    )
    verify_ssl: bool = Field(
        default=False,
        description="Verify SSL certificates",
    )
    request_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )
    connection_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="HTTP connection pool size",
    )
    auth: GCMAuthConfig = Field(
        default_factory=GCMAuthConfig,
        description="Authentication configuration",
    )
    oidc: GCMOIDCConfig = Field(
        default_factory=GCMOIDCConfig,
        description="OIDC provider configuration",
    )

    def get_url(self) -> str:
        """Get GCM MCP server URL, building from host/port if needed."""
        if self.url:
            return self.url
        return f"https://{self.host}:{self.api_port}/ibm/mcp/mcp"


class PolicyConfig(BaseModel):
    """Policy engine configuration."""

    config_file: str = Field(
        default="config/policy.yaml",
        description="Policy configuration file path",
    )
    enable_rate_limiting: bool = Field(
        default=True,
        description="Enable rate limiting (Phase 2)",
    )
    enable_restrictions: bool = Field(
        default=True,
        description="Enable policy restrictions",
    )


class AuditConfig(BaseModel):
    """Audit logging configuration."""

    enabled: bool = Field(
        default=True,
        description="Enable audit logging",
    )
    log_file: str = Field(
        default="logs/audit.jsonl",
        description="Audit log file path",
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log format",
    )
    log_rotation: Literal["daily", "weekly", "size"] = Field(
        default="daily",
        description="Log rotation strategy",
    )
    max_file_size_mb: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Max log file size in MB (for size rotation)",
    )
    retention_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Log retention period in days",
    )
    include_arguments: bool = Field(
        default=True,
        description="Include tool arguments in logs",
    )
    include_results: bool = Field(
        default=False,
        description="Include full results in logs (may be large)",
    )


class LoggingConfig(BaseModel):
    """Application logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Log level",
    )
    format: Literal["structured", "simple"] = Field(
        default="structured",
        description="Log format",
    )
    output: Literal["stdout", "file", "both"] = Field(
        default="stdout",
        description="Log output destination",
    )
    file: str = Field(
        default="logs/relay.log",
        description="Log file path (if output includes file)",
    )


class Config(BaseModel):
    """Root configuration model."""

    relay: RelayConfig = Field(
        default_factory=RelayConfig,
        description="Relay server configuration",
    )
    relay_http: RelayHttpConfig = Field(
        default_factory=RelayHttpConfig,
        alias="relay.http",
        description="HTTP mode configuration",
    )
    gcm: GCMConfig = Field(
        default_factory=GCMConfig,
        description="GCM connection configuration",
    )
    policy: PolicyConfig = Field(
        default_factory=PolicyConfig,
        description="Policy engine configuration",
    )
    audit: AuditConfig = Field(
        default_factory=AuditConfig,
        description="Audit logging configuration",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Application logging configuration",
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
        extra = "forbid"  # Reject unknown fields

# Made with Bob
