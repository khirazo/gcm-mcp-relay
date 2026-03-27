# GCM MCP Relay - Implementation Guide

This document consolidates the remaining design areas: Configuration Management, Audit Logging, Error Handling, Deployment Strategy, and Security Considerations.

## 1. Configuration Management System

### 1.1 Configuration Sources (Priority Order)

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration file** (TOML)
4. **Default values** (lowest priority)

### 1.2 Configuration File Structure

```toml
# config/relay.toml

[relay]
# Operational mode
mode = "stdio"  # "stdio" or "http"
log_level = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Active profile
profile = "readonly"  # Can be overridden by GCM_RELAY_PROFILE env var

[relay.http]
# HTTP mode settings (Phase 2)
host = "0.0.0.0"
port = 8002
enable_cors = true
cors_origins = ["*"]

[gcm]
# GCM MCP server connection
url = "https://gcm.example.com:31443/ibm/mcp/mcp"
verify_ssl = false
request_timeout = 30
connection_pool_size = 10

[gcm.auth]
# Authentication credentials (prefer environment variables)
username = ""  # Override with GCM_USERNAME
password = ""  # Override with GCM_PASSWORD
client_id = "gcmclient"
client_secret = ""  # Override with GCM_CLIENT_SECRET
auth_mode = "auto"  # "auto", "oauth2", "browser"

[gcm.oidc]
# OIDC Provider (Keycloak) settings
host = "gcm.example.com"
port = 30443
realm = "gcmrealm"

[policy]
# Policy configuration
config_file = "config/tools.yaml"
enable_rate_limiting = true
enable_restrictions = true

[audit]
# Audit logging
enabled = true
log_file = "logs/audit.jsonl"
log_format = "json"  # "json" or "text"
log_rotation = "daily"  # "daily", "weekly", "size"
max_file_size_mb = 100
retention_days = 90
include_arguments = true
include_results = false  # Don't log full results (may be large)

[logging]
# Application logging
level = "INFO"
format = "structured"  # "structured" or "simple"
output = "stdout"  # "stdout", "file", "both"
file = "logs/relay.log"
```

### 1.3 Configuration Loader Implementation

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import tomli
from typing import Optional

class RelayConfig(BaseModel):
    """Relay server configuration."""
    mode: str = "stdio"
    log_level: str = "INFO"
    profile: str = "readonly"

class RelayHttpConfig(BaseModel):
    """HTTP mode configuration."""
    host: str = "0.0.0.0"
    port: int = 8002
    enable_cors: bool = True
    cors_origins: list[str] = ["*"]

class GCMConfig(BaseModel):
    """GCM connection configuration."""
    url: str
    verify_ssl: bool = False
    request_timeout: int = 30
    connection_pool_size: int = 10

class GCMAuthConfig(BaseModel):
    """GCM authentication configuration."""
    username: str = ""
    password: str = ""
    client_id: str = "gcmclient"
    client_secret: str = ""
    auth_mode: str = "auto"

class GCMOIDCConfig(BaseModel):
    """OIDC Provider configuration."""
    host: str
    port: int = 30443
    realm: str = "gcmrealm"

class PolicyConfig(BaseModel):
    """Policy engine configuration."""
    config_file: str = "config/tools.yaml"
    enable_rate_limiting: bool = True
    enable_restrictions: bool = True

class AuditConfig(BaseModel):
    """Audit logging configuration."""
    enabled: bool = True
    log_file: str = "logs/audit.jsonl"
    log_format: str = "json"
    log_rotation: str = "daily"
    max_file_size_mb: int = 100
    retention_days: int = 90
    include_arguments: bool = True
    include_results: bool = False

class LoggingConfig(BaseModel):
    """Application logging configuration."""
    level: str = "INFO"
    format: str = "structured"
    output: str = "stdout"
    file: str = "logs/relay.log"

class Config(BaseSettings):
    """Complete application configuration."""
    relay: RelayConfig = Field(default_factory=RelayConfig)
    relay_http: RelayHttpConfig = Field(default_factory=RelayHttpConfig, alias="relay.http")
    gcm: GCMConfig
    gcm_auth: GCMAuthConfig = Field(default_factory=GCMAuthConfig, alias="gcm.auth")
    gcm_oidc: GCMOIDCConfig = Field(alias="gcm.oidc")
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    class Config:
        env_prefix = "GCM_RELAY_"
        env_nested_delimiter = "__"

class ConfigLoader:
    """Load configuration from multiple sources."""
    
    @staticmethod
    def load(config_path: Optional[str] = None) -> Config:
        """
        Load configuration with priority:
        1. Command-line arguments (passed as config_path)
        2. Environment variables
        3. Configuration file
        4. Defaults
        """
        # Load from TOML file
        if config_path and os.path.exists(config_path):
            with open(config_path, 'rb') as f:
                toml_data = tomli.load(f)
        else:
            toml_data = {}
        
        # Merge with environment variables (higher priority)
        # Pydantic-settings handles this automatically
        config = Config(**toml_data)
        
        # Validate configuration
        ConfigLoader._validate(config)
        
        return config
    
    @staticmethod
    def _validate(config: Config):
        """Validate configuration."""
        # Check required fields
        if not config.gcm.url:
            raise ValueError("GCM URL is required")
        
        if not config.gcm_auth.username:
            raise ValueError("GCM username is required (set GCM_USERNAME)")
        
        if not config.gcm_auth.password:
            raise ValueError("GCM password is required (set GCM_PASSWORD)")
        
        if not config.gcm_auth.client_secret:
            raise ValueError("GCM client secret is required (set GCM_CLIENT_SECRET)")
        
        # Validate mode
        if config.relay.mode not in ["stdio", "http"]:
            raise ValueError(f"Invalid mode: {config.relay.mode}")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.relay.log_level not in valid_levels:
            raise ValueError(f"Invalid log level: {config.relay.log_level}")
```

### 1.4 Environment Variable Mapping

```bash
# Relay settings
export GCM_RELAY_MODE=stdio
export GCM_RELAY_LOG_LEVEL=INFO
export GCM_RELAY_PROFILE=readonly

# GCM connection
export GCM_RELAY_GCM__URL=https://gcm.example.com:31443/ibm/mcp/mcp
export GCM_RELAY_GCM__VERIFY_SSL=false

# GCM authentication
export GCM_USERNAME=admin
export GCM_PASSWORD=secret
export GCM_CLIENT_SECRET=client-secret

# OIDC Provider
export GCM_RELAY_GCM__OIDC__HOST=gcm.example.com
export GCM_RELAY_GCM__OIDC__PORT=30443

# Policy
export GCM_RELAY_POLICY__CONFIG_FILE=config/tools.yaml

# Audit
export GCM_RELAY_AUDIT__ENABLED=true
export GCM_RELAY_AUDIT__LOG_FILE=logs/audit.jsonl
```

## 2. Audit Logging System

### 2.1 Audit Log Format

```json
{
  "timestamp": "2026-03-27T08:00:00.123Z",
  "event_type": "tool_invocation",
  "tool_name": "search_policies",
  "profile": "readonly",
  "user": "ai-agent-001",
  "session_id": "sess_abc123",
  "arguments": {
    "query": "TLS"
  },
  "result": {
    "status": "success",
    "duration_ms": 234,
    "response_size_bytes": 1024
  },
  "metadata": {
    "relay_version": "1.0.0",
    "gcm_version": "2.0.1",
    "client_ip": "127.0.0.1"
  }
}
```

### 2.2 Audit Logger Implementation

```python
import structlog
from datetime import datetime
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

class AuditLogger:
    """
    Structured audit logger for GCM MCP Relay.
    
    Logs all tool invocations, authentication events, and policy violations.
    """
    
    def __init__(self, config: AuditConfig):
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup structured logger with rotation."""
        # Create logs directory
        log_path = Path(self.config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
        )
        
        return structlog.get_logger("audit")
    
    async def log_tool_invocation(
        self,
        tool_name: str,
        arguments: dict,
        profile: str,
        status: str,
        duration_ms: Optional[float] = None,
        result_size: Optional[int] = None,
        error: Optional[str] = None,
        user: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Log a tool invocation."""
        event = {
            "event_type": "tool_invocation",
            "tool_name": tool_name,
            "profile": profile,
            "status": status,
        }
        
        if self.config.include_arguments:
            event["arguments"] = arguments
        
        if duration_ms is not None:
            event["duration_ms"] = duration_ms
        
        if result_size is not None:
            event["response_size_bytes"] = result_size
        
        if error:
            event["error"] = error
        
        if user:
            event["user"] = user
        
        if session_id:
            event["session_id"] = session_id
        
        self.logger.info("tool_invocation", **event)
    
    async def log_authentication(
        self,
        status: str,
        username: str,
        auth_method: str,
        error: Optional[str] = None
    ):
        """Log an authentication event."""
        event = {
            "event_type": "authentication",
            "status": status,
            "username": username,
            "auth_method": auth_method,
        }
        
        if error:
            event["error"] = error
        
        self.logger.info("authentication", **event)
    
    async def log_policy_violation(
        self,
        tool_name: str,
        profile: str,
        reason: str,
        user: Optional[str] = None
    ):
        """Log a policy violation."""
        event = {
            "event_type": "policy_violation",
            "tool_name": tool_name,
            "profile": profile,
            "reason": reason,
        }
        
        if user:
            event["user"] = user
        
        self.logger.warning("policy_violation", **event)
    
    async def log_system_event(
        self,
        event_type: str,
        message: str,
        **kwargs
    ):
        """Log a system event."""
        event = {
            "event_type": event_type,
            "message": message,
            **kwargs
        }
        
        self.logger.info("system_event", **event)
```

### 2.3 Log Rotation

```python
class LogRotationManager:
    """Manage audit log rotation and retention."""
    
    def __init__(self, config: AuditConfig):
        self.config = config
    
    def setup_rotation(self):
        """Setup log rotation based on configuration."""
        if self.config.log_rotation == "daily":
            handler = TimedRotatingFileHandler(
                self.config.log_file,
                when='midnight',
                interval=1,
                backupCount=self.config.retention_days
            )
        elif self.config.log_rotation == "size":
            handler = RotatingFileHandler(
                self.config.log_file,
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=10
            )
        else:
            handler = logging.FileHandler(self.config.log_file)
        
        return handler
    
    async def cleanup_old_logs(self):
        """Remove logs older than retention period."""
        log_dir = Path(self.config.log_file).parent
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        for log_file in log_dir.glob("audit.jsonl.*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                logger.info(f"Deleted old audit log: {log_file}")
```

## 3. Error Handling Strategy

### 3.1 Error Hierarchy

```python
class RelayError(Exception):
    """Base exception for all relay errors."""
    def __init__(self, message: str, code: str, details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict:
        """Convert error to dictionary for JSON response."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }

# Configuration errors
class ConfigurationError(RelayError):
    """Configuration-related errors."""
    pass

class MissingConfigError(ConfigurationError):
    """Required configuration is missing."""
    pass

# Authentication errors
class AuthenticationError(RelayError):
    """Authentication-related errors."""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""
    pass

class TokenExpiredError(AuthenticationError):
    """Access token has expired."""
    pass

# Authorization errors
class AuthorizationError(RelayError):
    """Authorization-related errors."""
    pass

class ToolNotAllowedError(AuthorizationError):
    """Tool not allowed for current profile."""
    pass

class RateLimitExceededError(AuthorizationError):
    """Rate limit exceeded."""
    pass

# Validation errors
class ValidationError(RelayError):
    """Input validation errors."""
    pass

class InvalidArgumentError(ValidationError):
    """Invalid tool argument."""
    pass

# GCM errors
class GCMError(RelayError):
    """Errors from GCM MCP server."""
    pass

class GCMConnectionError(GCMError):
    """Failed to connect to GCM."""
    pass

class GCMTimeoutError(GCMError):
    """GCM request timed out."""
    pass
```

### 3.2 Error Handler

```python
class ErrorHandler:
    """Centralized error handling."""
    
    @staticmethod
    async def handle_error(error: Exception, audit_logger: AuditLogger) -> dict:
        """
        Handle an error and return appropriate response.
        
        Args:
            error: The exception that occurred
            audit_logger: Audit logger for logging errors
            
        Returns:
            Error response dictionary
        """
        # Log error
        await audit_logger.log_system_event(
            "error",
            str(error),
            error_type=type(error).__name__
        )
        
        # Convert to RelayError if needed
        if isinstance(error, RelayError):
            relay_error = error
        else:
            relay_error = RelayError(
                message=str(error),
                code="INTERNAL_ERROR",
                details={"original_error": type(error).__name__}
            )
        
        # Return error response
        return relay_error.to_dict()
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """Determine if operation should be retried."""
        # Retry on transient errors
        return isinstance(error, (
            GCMConnectionError,
            GCMTimeoutError,
            TokenExpiredError
        ))
```

### 3.3 Retry Logic

```python
class RetryHandler:
    """Handle retries with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ):
        """Execute function with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if not ErrorHandler.should_retry(e):
                    raise
                
                if attempt < self.max_retries:
                    delay = min(
                        self.initial_delay * (self.exponential_base ** attempt),
                        self.max_delay
                    )
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
        
        raise last_error
```

## 4. Deployment Strategy

### 4.1 Local Development Deployment

```bash
# 1. Clone repository
git clone <repository-url>
cd gcm-mcp-relay

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .

# 4. Configure
cp config/relay.example.toml config/relay.toml
cp config/tools.example.yaml config/tools.yaml
# Edit config files with your GCM settings

# 5. Set credentials
export GCM_USERNAME=admin
export GCM_PASSWORD=secret
export GCM_CLIENT_SECRET=client-secret

# 6. Run
python -m gcm_relay --mode stdio
```

### 4.2 MCP Client Configuration

**Cursor / Claude Desktop:**
```json
{
  "mcpServers": {
    "gcm": {
      "command": "python",
      "args": ["-m", "gcm_relay", "--mode", "stdio"],
      "env": {
        "GCM_USERNAME": "admin",
        "GCM_PASSWORD": "secret",
        "GCM_CLIENT_SECRET": "client-secret"
      }
    }
  }
}
```

### 4.3 Docker Deployment (Phase 2)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Create logs directory
RUN mkdir -p /app/logs

# Run as non-root user
RUN useradd -m -u 1000 relay && chown -R relay:relay /app
USER relay

# Expose HTTP port (Phase 2)
EXPOSE 8002

# Entry point
ENTRYPOINT ["python", "-m", "gcm_relay"]
CMD ["--mode", "stdio"]
```

```bash
# Build
docker build -t gcm-mcp-relay:latest .

# Run stdio mode
docker run -it --rm \
  -e GCM_USERNAME=admin \
  -e GCM_PASSWORD=secret \
  -e GCM_CLIENT_SECRET=secret \
  gcm-mcp-relay:latest --mode stdio

# Run HTTP mode (Phase 2)
docker run -d \
  -p 8002:8002 \
  -e GCM_USERNAME=admin \
  -e GCM_PASSWORD=secret \
  -e GCM_CLIENT_SECRET=secret \
  -v $(pwd)/logs:/app/logs \
  gcm-mcp-relay:latest --mode http
```

## 5. Security Considerations

### 5.1 Credential Security

**Best Practices:**
- Use environment variables for credentials
- Never commit credentials to version control
- Use separate credentials per environment
- Rotate credentials regularly
- Use least-privilege accounts

**File Permissions:**
```bash
# Configuration files
chmod 600 config/relay.toml
chmod 600 config/tools.yaml

# Log files
chmod 640 logs/audit.jsonl
chmod 640 logs/relay.log
```

### 5.2 Network Security

**TLS Configuration:**
- Always use TLS for GCM connections
- Verify server certificates in production
- Use strong cipher suites
- Set appropriate timeouts

**Firewall Rules:**
```bash
# Allow outbound to GCM (HTTPS)
iptables -A OUTPUT -p tcp --dport 31443 -j ACCEPT

# Allow outbound to Keycloak (HTTPS)
iptables -A OUTPUT -p tcp --dport 30443 -j ACCEPT

# Block all other outbound (optional)
iptables -A OUTPUT -j DROP
```

### 5.3 Audit and Monitoring

**Security Monitoring:**
- Monitor failed authentication attempts
- Alert on policy violations
- Track rate limit violations
- Review audit logs regularly

**SIEM Integration:**
```python
class SIEMIntegration:
    """Send security events to SIEM."""
    
    async def send_security_event(self, event: dict):
        """Send security event to SIEM."""
        # Format for your SIEM (Splunk, ELK, etc.)
        siem_event = {
            "source": "gcm-mcp-relay",
            "severity": self._map_severity(event),
            "event": event
        }
        
        # Send to SIEM endpoint
        await self._send_to_siem(siem_event)
```

### 5.4 Security Checklist

**Pre-Deployment:**
- [ ] All credentials in environment variables
- [ ] Config files have restrictive permissions
- [ ] TLS verification enabled (production)
- [ ] Audit logging enabled
- [ ] Policy configuration reviewed
- [ ] Default profile is readonly
- [ ] Rate limiting configured
- [ ] Log rotation configured

**Post-Deployment:**
- [ ] Monitor authentication failures
- [ ] Review audit logs daily
- [ ] Check for policy violations
- [ ] Verify rate limits working
- [ ] Test credential rotation
- [ ] Review access patterns
- [ ] Update dependencies regularly

## 6. References

- [Architecture Design](architecture.md)
- [Project Structure](project-structure.md)
- [Authentication Design](authentication-design.md)
- [Tool Abstraction Design](tool-abstraction-design.md)
- [Policy Engine Design](policy-engine-design.md)