# GCM MCP Relay

A secure, Docker-based relay service that sits between AI coding agents and IBM Guardium Cryptography Manager's built-in MCP server, providing simplified authentication, policy-based access control, and audit logging.

## Overview

IBM Guardium Cryptography Manager (GCM) 2.0.1 includes a built-in MCP server with 26 tools for managing cryptographic assets, certificates, and policies. However, direct access from AI agents is challenging due to:

- Complex OAuth2/OIDC authentication flow
- Mixed exposure of safe read-only and dangerous state-changing tools
- No built-in access control or audit logging

**GCM MCP Relay** solves these problems by:

- ✅ **Docker-first deployment**: Containerized for consistent, portable deployment
- ✅ **Transparent authentication**: Handles OAuth2/OIDC flow automatically
- ✅ **Profile-based access control**: readonly/ops/admin profiles
- ✅ **Comprehensive audit logging**: All tool invocations logged
- ✅ **stdio transport mode**: Local AI agent integration
- ✅ **Safe AI integration**: Selective tool exposure with policy enforcement

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  PC / Laptop (Docker Host)                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         AI Coding Agent (IBM Bob / Cursor)             │  │
│  └────────────────────────┬───────────────────────────────┘  │
│                           │ stdio                             │
│  ┌────────────────────────▼───────────────────────────────┐  │
│  │       Docker Container: GCM MCP Relay                  │  │
│  │  - Authentication management                           │  │
│  │  - Policy enforcement                                  │  │
│  │  - Tool abstraction                                    │  │
│  │  - Audit logging                                       │  │
│  └────────────────────────┬───────────────────────────────┘  │
└────────────────────────────┼─────────────────────────────────┘
                             │ HTTPS + Bearer JWT
┌────────────────────────────▼─────────────────────────────────┐
│          GCM Built-in MCP Server                              │
│          (streamable-http, 26 tools)                          │
└───────────────────────────────────────────────────────────────┘
```

## Features

- ✅ **Docker deployment**: Multi-stage build, non-root user, minimal image
- ✅ **stdio mode**: Local development with AI coding agents
- ✅ **Authentication**: Automatic OAuth2/OIDC token management
- ✅ **Policy Engine**: Profile-based access control (readonly/ops/admin)
- ✅ **Tool Filtering**: Selective exposure of GCM tools
- ✅ **Audit Logging**: Comprehensive structured logging (JSONL)
- ✅ **Configuration**: TOML config + environment variables

> **Note**: This is Phase 1 implementation (stdio mode). For future enhancement plans, see [docs/FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md).

## 🚀 Quick Start

> **📖 For detailed setup instructions, see [QUICKSTART.md](QUICKSTART.md)**

### Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose)
- **IBM Bob** or other MCP client
- **GCM credentials** (username, password, client secret)
- **Git** (for cloning the repository)

### Setup (3 Steps)

1. **Clone and configure**: Copy `.env.example` to `.env` and add your GCM credentials
2. **Build container**: `docker compose build`
3. **Configure IBM Bob**: Add relay to `mcp_settings.json`

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

### Testing

Test the relay locally before connecting to IBM Bob:

```bash
# Make test script executable (Linux/macOS/WSL)
chmod +x scripts/test-mcp.sh

# Run MCP protocol test
./scripts/test-mcp.sh
```

Expected output:
```
=== GCM MCP Relay Test Script ===

Test 1: Initialize
{
  "protocolVersion": "2024-11-05",
  "serverInfo": {
    "name": "gcm-mcp-relay",
    "version": "0.1.0"
  },
  "capabilities": {
    "tools": {}
  }
}

Test 2: List Tools
Found 22 tools

{
  "name": "search_policies",
  "description": "Retrieve policies filtered by policy_type..."
}
{
  "name": "fetch_policy_by_id",
  "description": "Retrieve one or more policies by their unique policy IDs..."
}
... (showing first 10 tools)

Summary:
- Initialize: ✓ Success
- Tools List: ✓ Success (22 tools)
```

### Verification

```bash
# Test relay startup
docker compose run --rm gcm-mcp-relay

# Check logs
docker compose logs gcm-mcp-relay

# Verify configuration
docker compose config
```

## Alternative: Native Python Installation

If you prefer to run without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GCM_USERNAME="your-username"
export GCM_PASSWORD="your-password"
export GCM_CLIENT_SECRET="your-client-secret"

# Run relay
python -m src --mode stdio

# With custom config
python -m gcm_relay --mode stdio --config config/relay.toml
```

### MCP Client Configuration

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

## 📚 Documentation

### Getting Started
- **[How to Obtain GCM_CLIENT_SECRET](docs/KEYCLOAK_CLIENT_SECRET.md)** - Step-by-step guide to get Keycloak client secret

### Architecture & Design
- **[Architecture Design](docs/architecture.md)** - System architecture and component design
- **[Docker Deployment](docs/docker-deployment.md)** - Complete Docker deployment guide
- **[Implementation Guide](docs/implementation-guide.md)** - Configuration, logging, and error handling
- **[Authentication Design](docs/authentication-design.md)** - OAuth2/OIDC authentication flows
- **[Tool Abstraction Design](docs/tool-abstraction-design.md)** - Tool classification and exposure
- **[Policy Engine Design](docs/policy-engine-design.md)** - Access control and policy enforcement
- **[Project Structure](docs/project-structure.md)** - Directory layout and file organization

## Configuration

### Relay Configuration (`config/relay.toml`)

```toml
[relay]
mode = "stdio"
log_level = "INFO"
profile = "readonly"

[gcm]
url = "https://gcm.example.com:31443/ibm/mcp/mcp"
verify_ssl = false

[gcm.auth]
username = ""  # Set via GCM_USERNAME
password = ""  # Set via GCM_PASSWORD
client_id = "gcmclient"
client_secret = ""  # Set via GCM_CLIENT_SECRET

[gcm.oidc]
host = "gcm.example.com"
port = 30443
realm = "gcmrealm"

[audit]
enabled = true
log_file = "logs/audit.jsonl"
```

### Policy Configuration (`config/tools.yaml`)

```yaml
profile: readonly

profiles:
  readonly:
    description: "Read-only access to GCM data"
    allow:
      - search_policies
      - fetch_policy_by_id
      - get_violation_by_id
      # ... 22 read-only tools total

  ops:
    description: "Operations team access"
    allow:
      - "*readonly"
      - create_violation_ticket

  admin:
    description: "Full administrative access"
    allow:
      - "*"
```

## Available Tools

### Read-Only Tools (22 tools)

Safe tools that only query data:

- **Policy**: `search_policies`, `fetch_policy_by_id`
- **Violations**: `get_violation_by_id`, `fetch_policy_violations_ticket`, `policy_violations_dashboard`
- **Assets**: `fetch_detailed_asset_list_by_it_assets`, `get_asset_groups`, etc.
- **Crypto Objects**: `fetch_detailed_asset_list_by_crypto_objects`, `get_vulnerable_crypto_objects_count`, etc.
- **Certificates**: `get_certificate_details`, `get_vault_details`, etc.
- **Users**: `get_user_details_by_username`

### State-Changing Tools (4 tools)

Restricted tools that modify GCM state:

- `create_policy` (admin only)
- `create_violation_ticket` (ops, admin)
- `renew_ca_signed_certificate` (admin only)
- `renew_self_signed_certificate` (admin only)

## Security

### Credential Management

**DO**:
- ✅ Use environment variables for credentials
- ✅ Set restrictive file permissions (600) on config files
- ✅ Add config files to `.gitignore`
- ✅ Use separate credentials per environment

**DON'T**:
- ❌ Commit credentials to version control
- ❌ Log credentials (even in debug mode)
- ❌ Store credentials in plaintext in shared locations
- ❌ Reuse credentials across environments

### Access Control

- Default profile: `readonly` (most restrictive)
- Profile-based tool access control
- Comprehensive audit logging

### Network Security

- TLS required for GCM connections
- Certificate verification (production)
- Configurable timeouts
- Connection pooling

## Audit Logging

All tool invocations are logged in structured JSON format:

```json
{
  "timestamp": "2026-03-27T08:00:00.123Z",
  "event_type": "tool_invocation",
  "tool_name": "search_policies",
  "profile": "readonly",
  "user": "ai-agent-001",
  "arguments": {"query": "TLS"},
  "result": {
    "status": "success",
    "duration_ms": 234
  }
}
```

Logs include:
- Tool invocations (success/failure)
- Authentication events
- Policy violations
- System events

## Development

### Project Structure

```
gcm-mcp-relay/
├── src/gcm_relay/          # Source code
│   ├── server/             # MCP server (stdio)
│   ├── tools/              # Tool management
│   ├── policy/             # Policy engine
│   ├── auth/               # Authentication
│   ├── client/             # GCM MCP client
│   ├── audit/              # Audit logging
│   └── config/             # Configuration
├── scripts/                # Utility scripts
│   └── test-mcp.sh        # MCP protocol test
├── docs/                   # Documentation
├── config/                 # Configuration files
└── logs/                   # Log files
```

### Testing

The project includes an MCP protocol test script to verify relay functionality:

```bash
# Make test script executable (Linux/macOS/WSL)
chmod +x scripts/test-mcp.sh

# Run MCP protocol test
./scripts/test-mcp.sh
```

This tests:
- MCP protocol initialization (2024-11-05)
- Tool listing (22 tools in readonly profile)
- JSON-RPC communication over stdio

See [Testing](#testing) section above for expected output.

> **Note**: Unit tests with pytest are planned for future implementation. Currently, use the MCP protocol test script for validation.

## Documentation

- [Architecture Design](docs/architecture.md) - System architecture and design principles
- [Project Structure](docs/project-structure.md) - Directory layout and module organization
- [Authentication Design](docs/authentication-design.md) - Authentication flows and token management
- [Tool Abstraction Design](docs/tool-abstraction-design.md) - Tool classification and execution
- [Policy Engine Design](docs/policy-engine-design.md) - Access control and policy enforcement
- [Implementation Guide](docs/implementation-guide.md) - Configuration, logging, errors, deployment

## Troubleshooting

### Authentication Fails

```bash
# Check credentials
echo $GCM_USERNAME
echo $GCM_PASSWORD
echo $GCM_CLIENT_SECRET

# Test GCM connectivity
python scripts/test_gcm_connection.py

# Check Keycloak is accessible
curl -k https://gcm.example.com:30443/realms/gcmrealm/.well-known/openid-configuration
```

### Tool Not Allowed

```bash
# Check active profile
grep "profile:" config/tools.yaml

# Check tool is in profile allowlist
grep -A 20 "readonly:" config/tools.yaml

# Switch to different profile
export GCM_RELAY_PROFILE=ops
```

### Connection Timeout

```bash
# Increase timeout in config
[gcm]
request_timeout = 60

# Check network connectivity
ping gcm.example.com
telnet gcm.example.com 31443
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[License information]

## References

- [GCM MCP Server Documentation](work/Building_agents_for_IBM_Guardium_Cryptography_Manager_using_inbuilt_MCP_server.md)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [IBM Guardium Cryptography Manager](https://www.ibm.com/products/guardium-cryptography-manager)

## Support

For issues and questions:
- GitHub Issues: https://github.com/khirazo/gcm-mcp-relay/issues
- Documentation: https://github.com/khirazo/gcm-mcp-relay/tree/main/docs

---

**Made with ❤️ for secure AI integration with IBM Guardium Cryptography Manager**