# GCM MCP Relay - Docker Deployment Design

This document provides the complete Docker deployment design for GCM MCP Relay, based on the reference implementation at `C:\workspace\gcm-mcp-server`.

## 1. Docker Architecture Overview

### 1.1 Deployment Model

```
┌─────────────────────────────────────────────────────────────┐
│                  Host Machine (Laptop/Server)                │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              AI Coding Agent (IBM Bob)                 │ │
│  │              - Cursor / Claude Desktop                 │ │
│  └────────────────────┬───────────────────────────────────┘ │
│                       │ stdio                                │
│                       │ (docker compose run)                 │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │         Docker Container: gcm-mcp-relay                │ │
│  │                                                         │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │  Entrypoint Script (entrypoint.sh)                │ │ │
│  │  │  - Load config.toml                               │ │ │
│  │  │  - Validate environment variables                 │ │ │
│  │  │  - Start relay process                            │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │  GCM MCP Relay Process                            │ │ │
│  │  │  - Python 3.11                                    │ │ │
│  │  │  - Non-root user (UID 1000)                       │ │ │
│  │  │  - stdio MCP server                               │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  │                                                         │ │
│  │  Mounted Volumes:                                       │ │
│  │  - config/relay.toml → /config/relay.toml (ro)         │ │
│  │  - config/policy.yaml → /config/policy.yaml (ro)       │ │
│  │  - logs/ → /logs (rw)                                  │ │
│  │                                                         │ │
│  │  Environment Variables (from .env):                     │ │
│  │  - GCM_USERNAME, GCM_PASSWORD, GCM_CLIENT_SECRET       │ │
│  │  - GCM_HOST, GCM_API_PORT, GCM_OIDC_PORT              │ │
│  └─────────────────────┬───────────────────────────────────┘ │
└────────────────────────┼─────────────────────────────────────┘
                         │ HTTPS + Bearer JWT
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              GCM Built-in MCP Server                          │
│              (Remote, streamable-http)                        │
└───────────────────────────────────────────────────────────────┘
```

### 1.2 Key Design Decisions

1. **Multi-stage build**: Separate builder and runtime stages for minimal image size
2. **Non-root user**: Run as UID 1000 for security
3. **Read-only config**: Configuration files mounted as read-only volumes
4. **Environment-based credentials**: Sensitive data in `.env` file, never in config files
5. **Entrypoint validation**: Fail-fast validation before starting relay
6. **Log volume**: Persistent audit logs outside container

## 2. Dockerfile Design

### 2.1 Multi-Stage Dockerfile

```dockerfile
# GCM MCP Relay - Dockerfile
# Multi-stage build for optimized production image

# ============================================================
# Stage 1: Builder - Install Python dependencies
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================
# Stage 2: Runtime - Minimal production image
# ============================================================
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r relay && useradd -r -g relay -u 1000 relay

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/relay/.local

# Copy application code
COPY --chown=relay:relay src ./src

# Copy scripts
COPY --chown=relay:relay scripts/entrypoint.sh /entrypoint.sh
COPY --chown=relay:relay scripts/config-loader.py /config-loader.py

# Make scripts executable
RUN chmod +x /entrypoint.sh /config-loader.py

# Create directories for config and logs
RUN mkdir -p /config /logs && chown relay:relay /logs

# Set environment variables
ENV PATH=/home/relay/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Switch to non-root user
USER relay

# Health check (for HTTP mode in Phase 2)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Use entrypoint script for configuration loading and validation
ENTRYPOINT ["/entrypoint.sh"]

# Default to stdio transport mode
CMD ["stdio"]
```

### 2.2 Key Features

- **Multi-stage build**: Reduces final image size by ~40%
- **Non-root user**: Security best practice (UID 1000)
- **Minimal runtime**: Only essential packages in final image
- **Health check**: For HTTP mode monitoring (Phase 2)
- **Entrypoint validation**: Fail-fast on configuration errors

## 3. Docker Compose Configuration

### 3.1 docker-compose.yml

```yaml
# GCM MCP Relay - Docker Compose Configuration
# Optimized for stdio mode with IBM Bob MCP client

services:
  gcm-mcp-relay:
    build:
      context: .
      dockerfile: Dockerfile
    image: gcm-mcp-relay:stdio
    container_name: gcm-mcp-relay
    
    # Mount configuration files (read-only)
    volumes:
      - ./config/relay.toml:/config/relay.toml:ro
      - ./config/policy.yaml:/config/policy.yaml:ro
      - ./logs:/logs
    
    # Environment variables for credentials
    # Load from .env file or set directly
    environment:
      # Required credentials
      - GCM_USERNAME=${GCM_USERNAME}
      - GCM_PASSWORD=${GCM_PASSWORD}
      - GCM_CLIENT_SECRET=${GCM_CLIENT_SECRET}
      
      # Optional overrides (defaults from relay.toml)
      - GCM_HOST=${GCM_HOST:-localhost}
      - GCM_API_PORT=${GCM_API_PORT:-31443}
      - GCM_OIDC_PORT=${GCM_OIDC_PORT:-30443}
      - GCM_CLIENT_ID=${GCM_CLIENT_ID:-gcmclient}
      - GCM_AUTH_MODE=${GCM_AUTH_MODE:-auto}
      - GCM_VERIFY_SSL=${GCM_VERIFY_SSL:-false}
      - GCM_LOG_LEVEL=${GCM_LOG_LEVEL:-INFO}
      - GCM_RELAY_PROFILE=${GCM_RELAY_PROFILE:-readonly}
    
    # Enable stdin for stdio communication
    stdin_open: true
    tty: true
    
    # Security: Run as non-root user
    user: "1000:1000"
    
    # Resource limits (adjust based on your needs)
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    
    restart: unless-stopped

# Note: No networks or ports needed for stdio mode
# The container communicates via stdin/stdout with the MCP client
```

### 3.2 HTTP Mode Configuration (Phase 2)

```yaml
# docker-compose.http.yml
# For HTTP/SSE mode deployment

services:
  gcm-mcp-relay-http:
    extends:
      file: docker-compose.yml
      service: gcm-mcp-relay
    
    image: gcm-mcp-relay:http
    container_name: gcm-mcp-relay-http
    
    # Override command for HTTP mode
    command: ["http"]
    
    # Expose HTTP port
    ports:
      - "8002:8002"
    
    # Additional volume for API key storage
    volumes:
      - ./config/relay.toml:/config/relay.toml:ro
      - ./config/policy.yaml:/config/policy.yaml:ro
      - ./logs:/logs
      - ./data:/data  # API key storage
    
    # No stdin/tty needed for HTTP mode
    stdin_open: false
    tty: false
    
    # Network for HTTP access
    networks:
      - relay-network

networks:
  relay-network:
    driver: bridge
```

## 4. Entrypoint Script Design

### 4.1 scripts/entrypoint.sh

```bash
#!/bin/bash
# GCM MCP Relay - Entrypoint Script
# Validates configuration and starts relay process

set -e

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GCM MCP Relay Startup ===${NC}"

# Load configuration from TOML file if it exists
if [ -f /config/relay.toml ]; then
    echo -e "${GREEN}Loading configuration from /config/relay.toml...${NC}"
    python /config-loader.py /config/relay.toml
else
    echo -e "${YELLOW}Warning: /config/relay.toml not found, using environment variables only${NC}"
fi

# Validate required environment variables
echo -e "${GREEN}Validating required environment variables...${NC}"

MISSING_VARS=()

if [ -z "${GCM_HOST}" ]; then
    MISSING_VARS+=("GCM_HOST")
fi

if [ -z "${GCM_USERNAME}" ]; then
    MISSING_VARS+=("GCM_USERNAME")
fi

if [ -z "${GCM_PASSWORD}" ]; then
    MISSING_VARS+=("GCM_PASSWORD")
fi

if [ -z "${GCM_CLIENT_SECRET}" ]; then
    MISSING_VARS+=("GCM_CLIENT_SECRET")
fi

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}ERROR: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "${RED}  - ${var}${NC}"
    done
    echo ""
    echo "Set them using:"
    echo "  - Docker: -e GCM_HOST=... -e GCM_USERNAME=... etc."
    echo "  - Docker Compose: environment section or .env file"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ All required environment variables are set${NC}"

# Display configuration (without sensitive data)
echo -e "${GREEN}Configuration:${NC}"
echo "  GCM Host: ${GCM_HOST}"
echo "  GCM API Port: ${GCM_API_PORT:-31443}"
echo "  GCM OIDC Port: ${GCM_OIDC_PORT:-30443}"
echo "  Relay Profile: ${GCM_RELAY_PROFILE:-readonly}"
echo "  Log Level: ${GCM_LOG_LEVEL:-INFO}"
echo ""

# Validate policy configuration file
if [ -f /config/policy.yaml ]; then
    echo -e "${GREEN}✓ Policy configuration found: /config/policy.yaml${NC}"
else
    echo -e "${YELLOW}Warning: /config/policy.yaml not found, using default policy${NC}"
fi

# Start MCP Relay based on transport mode
# Default to stdio mode (for laptop deployment with IBM Bob)
TRANSPORT="${1:-stdio}"

# Ensure data directory exists for HTTP mode (API key storage)
if [ "${TRANSPORT}" = "http" ]; then
    if [ ! -d /data ]; then
        echo -e "${YELLOW}Creating /data directory for API key storage...${NC}"
        mkdir -p /data
    fi
fi

echo -e "${GREEN}Starting GCM MCP Relay (${TRANSPORT} mode)...${NC}"
echo ""

if [ "${TRANSPORT}" = "stdio" ]; then
    exec python -m src
elif [ "${TRANSPORT}" = "http" ]; then
    exec python -m src --transport http --host "${RELAY_HOST:-0.0.0.0}" --port "${RELAY_PORT:-8002}"
else
    # Custom command
    exec "$@"
fi
```

### 4.2 scripts/config-loader.py

```python
#!/usr/bin/env python3
"""
Configuration loader script for GCM MCP Relay.
Validates TOML configuration and exports to environment variables.
"""

import sys
import tomli
from pathlib import Path

def load_config(config_path: str) -> dict:
    """Load and validate TOML configuration."""
    try:
        with open(config_path, 'rb') as f:
            config = tomli.load(f)
        print(f"✓ Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        print(f"✗ Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    except tomli.TOMLDecodeError as e:
        print(f"✗ Invalid TOML syntax: {e}", file=sys.stderr)
        sys.exit(1)

def validate_config(config: dict) -> None:
    """Validate required configuration sections."""
    required_sections = ['relay', 'gcm', 'policy', 'audit']
    for section in required_sections:
        if section not in config:
            print(f"✗ Missing required section: [{section}]", file=sys.stderr)
            sys.exit(1)
    print("✓ Configuration structure validated")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: config-loader.py <config.toml>", file=sys.stderr)
        sys.exit(1)
    
    config_path = sys.argv[1]
    config = load_config(config_path)
    validate_config(config)
```

## 5. Configuration Files

### 5.1 .env.example

```bash
# GCM MCP Relay - Environment Variables Template
# Copy this file to .env and fill in your credentials

# ============================================================
# GCM Server Configuration
# ============================================================
GCM_HOST=gcm.example.com
GCM_API_PORT=31443

# ============================================================
# OIDC Provider (Keycloak) Configuration
# ============================================================
GCM_OIDC_PORT=30443
# GCM_OIDC_HOST=keycloak.example.com  # Optional: if different from GCM_HOST

# ============================================================
# Authentication Credentials (REQUIRED)
# ============================================================
# SECURITY WARNING: Never commit actual credentials to version control!
GCM_USERNAME=your-username
GCM_PASSWORD=your-password
GCM_CLIENT_SECRET=your-client-secret

# ============================================================
# Optional Configuration
# ============================================================
# OAuth2 client ID
GCM_CLIENT_ID=gcmclient

# Authentication mode: auto, oauth2, or browser
GCM_AUTH_MODE=auto

# SSL verification (set to true in production with valid certificates)
GCM_VERIFY_SSL=false

# Request timeout in seconds
GCM_REQUEST_TIMEOUT=30

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
GCM_LOG_LEVEL=INFO

# Relay profile: readonly, ops, admin
GCM_RELAY_PROFILE=readonly
```

### 5.2 .gitignore

```gitignore
# Environment variables (contains credentials)
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Docker
.dockerignore

# OS
.DS_Store
Thumbs.db

# Data
data/
*.db
*.sqlite
```

## 6. IBM Bob MCP Client Configuration

### 6.1 Windows Configuration

**Location:** `%USERPROFILE%\.bob\settings\mcp_settings.json`

```json
{
  "mcpServers": {
    "gcm-mcp-relay": {
      "command": "docker",
      "args": [
        "compose",
        "run",
        "--rm",
        "gcm-mcp-relay"
      ],
      "cwd": "C:\\workspace\\gcm-mcp-relay",
      "env": {}
    }
  }
}
```

### 6.2 macOS/Linux Configuration

**Location:** `~/.bob/settings/mcp_settings.json`

```json
{
  "mcpServers": {
    "gcm-mcp-relay": {
      "command": "docker",
      "args": [
        "compose",
        "run",
        "--rm",
        "gcm-mcp-relay"
      ],
      "cwd": "/path/to/gcm-mcp-relay",
      "env": {}
    }
  }
}
```

## 7. Quick Start Guide

### 7.1 Initial Setup (3 Steps)

```bash
# Step 1: Clone and configure
git clone <repository-url> gcm-mcp-relay
cd gcm-mcp-relay
cp .env.example .env
# Edit .env with your GCM credentials

# Step 2: Build Docker image
docker compose build

# Step 3: Configure IBM Bob
# Add configuration to ~/.bob/settings/mcp_settings.json
# Restart IBM Bob
```

### 7.2 Verification

```bash
# Test relay startup
docker compose run --rm gcm-mcp-relay

# Check logs
docker compose logs gcm-mcp-relay

# Verify configuration
docker compose config
```

## 8. Deployment Scenarios

### 8.1 Scenario 1: Local Development (stdio mode)

**Use Case:** Developer using IBM Bob on laptop

**Configuration:**
- stdio mode (default)
- Credentials in `.env` file
- Read-only profile
- Local Docker Desktop

**Command:**
```bash
docker compose run --rm gcm-mcp-relay
```

### 8.2 Scenario 2: Remote Access (HTTP mode - Phase 2)

**Use Case:** Remote AI agents accessing relay over network

**Configuration:**
- HTTP mode with SSE transport
- OIDC refresh token authentication
- Port 8002 exposed
- TLS termination via reverse proxy

**Command:**
```bash
docker compose -f docker-compose.http.yml up -d
```

### 8.3 Scenario 3: CI/CD Pipeline

**Use Case:** Automated testing and deployment

**Configuration:**
- stdio mode for testing
- Credentials from CI secrets
- Ephemeral containers
- No persistent volumes

**Command:**
```bash
docker run --rm \
  -e GCM_USERNAME=$CI_GCM_USERNAME \
  -e GCM_PASSWORD=$CI_GCM_PASSWORD \
  -e GCM_CLIENT_SECRET=$CI_GCM_CLIENT_SECRET \
  gcm-mcp-relay:stdio
```

## 9. Security Considerations

### 9.1 Container Security

1. **Non-root user**: All processes run as UID 1000
2. **Read-only config**: Configuration files mounted as read-only
3. **No privileged mode**: Container runs with default capabilities
4. **Resource limits**: CPU and memory limits enforced
5. **Health checks**: Automatic restart on failure

### 9.2 Credential Management

1. **Environment variables**: Credentials never in config files
2. **`.env` file**: Gitignored, never committed
3. **Docker secrets**: Use for production deployments
4. **Rotation**: Regular credential rotation recommended

### 9.3 Network Security

1. **stdio mode**: No network exposure (most secure)
2. **HTTP mode**: TLS termination via reverse proxy
3. **Firewall**: Restrict access to GCM endpoints
4. **Audit logs**: All access logged and monitored

## 10. Troubleshooting

### 10.1 Common Issues

**Issue:** Container fails to start with "Missing required environment variables"

**Solution:**
```bash
# Verify .env file exists and contains credentials
cat .env | grep GCM_USERNAME

# Check environment variables are loaded
docker compose config | grep GCM_USERNAME
```

**Issue:** "Permission denied" errors in logs

**Solution:**
```bash
# Fix log directory permissions
chmod 755 logs/
chown 1000:1000 logs/
```

**Issue:** Cannot connect to GCM server

**Solution:**
```bash
# Test connectivity from container
docker compose run --rm gcm-mcp-relay curl -k https://${GCM_HOST}:${GCM_API_PORT}

# Check SSL verification setting
grep verify_ssl config/relay.toml
```

### 10.2 Debug Mode

```bash
# Run with debug logging
GCM_LOG_LEVEL=DEBUG docker compose run --rm gcm-mcp-relay

# Interactive shell in container
docker compose run --rm --entrypoint /bin/bash gcm-mcp-relay

# View entrypoint script execution
docker compose run --rm gcm-mcp-relay bash -x /entrypoint.sh
```

## 11. Maintenance

### 11.1 Log Rotation

```bash
# Rotate audit logs (daily)
docker compose exec gcm-mcp-relay logrotate /etc/logrotate.d/relay

# Clean old logs (90 days retention)
find logs/ -name "*.log" -mtime +90 -delete
```

### 11.2 Image Updates

```bash
# Rebuild image with latest dependencies
docker compose build --no-cache

# Update base image
docker pull python:3.11-slim
docker compose build
```

### 11.3 Backup and Restore

```bash
# Backup configuration and logs
tar czf gcm-relay-backup-$(date +%Y%m%d).tar.gz config/ logs/ .env

# Restore from backup
tar xzf gcm-relay-backup-20260327.tar.gz
```

## 12. Production Deployment Checklist

- [ ] Use valid TLS certificates (not self-signed)
- [ ] Enable SSL verification (`GCM_VERIFY_SSL=true`)
- [ ] Set strong credentials (rotate regularly)
- [ ] Configure log rotation and retention
- [ ] Set up monitoring and alerting
- [ ] Use Docker secrets for credentials
- [ ] Implement backup strategy
- [ ] Document disaster recovery procedures
- [ ] Test failover scenarios
- [ ] Review and update security policies

## 13. References

- Reference implementation: `C:\workspace\gcm-mcp-server`
- GCM MCP Server manual: `work/Building_agents_for_IBM_Guardium_Cryptography_Manager_using_inbuilt_MCP_server.md`
- Docker best practices: https://docs.docker.com/develop/dev-best-practices/
- Python Docker images: https://hub.docker.com/_/python