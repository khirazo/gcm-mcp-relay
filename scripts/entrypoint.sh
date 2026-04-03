#!/bin/bash
# This file includes AI-generated code - Review and modify as needed
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
if [ -n "${GCM_OIDC_HOST}" ]; then
    echo "  GCM OIDC Host: ${GCM_OIDC_HOST}"
else
    echo "  GCM OIDC Host: ${GCM_HOST} (using GCM host)"
fi
echo "  GCM OIDC Port: ${GCM_OIDC_PORT:-30443}"
echo "  Access Control: GCM RBAC (user-based)"
echo "  Log Level: ${GCM_LOG_LEVEL:-INFO}"
echo ""

# Start MCP Relay based on transport mode
# Default to stdio mode (for laptop deployment with IBM Bob)
TRANSPORT="${1:-stdio}"

echo -e "${GREEN}Starting GCM MCP Relay (${TRANSPORT} mode)...${NC}"
echo ""

if [ "${TRANSPORT}" = "stdio" ]; then
    exec python -m gcm_relay
elif [ "${TRANSPORT}" = "http" ]; then
    exec python -m gcm_relay --transport http
else
    # Custom command
    exec "$@"
fi

# Made with Bob
