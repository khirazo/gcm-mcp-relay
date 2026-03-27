# GCM MCP Relay - Architecture Design

## 1. Executive Summary

GCM MCP Relay is a secure relay service that sits between AI coding agents and IBM Guardium Cryptography Manager (GCM) built-in MCP server. It simplifies authentication, enforces access control policies, and provides comprehensive audit logging.

### Design Principles

- **Phased Implementation**: Phase 1 (stdio mode), Phase 2 (HTTP mode)
- **Selective Exposure**: Safe read-only tools directly exposed, dangerous tools restricted
- **Configuration-Driven**: Policy changes without code modifications
- **Security-First**: Defense in depth, least privilege principle

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Coding Agent                          │
│              (Cursor / Claude Desktop / etc.)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ stdio (Phase 1)
                         │ HTTP + OIDC Refresh Token (Phase 2)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   GCM MCP Relay                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MCP Server Layer (stdio / HTTP)                     │   │
│  └──────────────────────┬───────────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │  Tool Facade Layer                                   │   │
│  │  - Tool mapping & abstraction                        │   │
│  │  - Schema transformation                             │   │
│  └──────────────────────┬───────────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │  Policy Engine                                       │   │
│  │  - Tool allowlist enforcement                        │   │
│  │  - Profile-based access control                      │   │
│  │  - Argument validation                               │   │
│  └──────────────────────┬───────────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │  Authentication Manager                              │   │
│  │  - OAuth2/OIDC token management                      │   │
│  │  - Token caching & refresh                           │   │
│  │  - Credential storage (stdio mode)                   │   │
│  └──────────────────────┬───────────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │  Audit Logger                                        │   │
│  │  - Tool invocation logging                           │   │
│  │  - Security event tracking                           │   │
│  └──────────────────────┬───────────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │  GCM MCP Client                                      │   │
│  │  - streamable-http transport                         │   │
│  │  - Bearer JWT authentication                         │   │
│  └──────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          │ HTTPS + Bearer JWT
                          │
┌─────────────────────────▼───────────────────────────────────┐
│          GCM Built-in MCP Server                             │
│          (streamable-http, 26 tools)                         │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

#### MCP Server Layer
- **stdio mode**: JSON-RPC over stdin/stdout (Phase 1)
- **HTTP mode**: SSE-based MCP protocol (Phase 2)
- MCP protocol handling (initialize, list_tools, call_tool)
- Transport-agnostic tool execution

#### Tool Facade Layer
- Selective exposure of GCM tools
- Tool name and schema transformation (if needed)
- Input parameter normalization
- Output format standardization

#### Policy Engine
- Load tool allowlist at startup
- Validate tool calls at execution time
- Profile-based access control (readonly/ops/admin)
- Parameter validation

#### Authentication Manager
- **stdio mode**: Load credentials from environment/config
- **HTTP mode**: Validate OIDC Refresh Token and obtain Access Token
- Token caching (TTL-based)
- Automatic re-authentication

#### Audit Logger
- Log all tool invocations
- Record timestamp, user, tool name, parameters, result
- Structured logging (JSON format)
- Log rotation support

#### GCM MCP Client
- Connect to GCM built-in MCP server
- streamable-http transport
- Bearer JWT authentication
- Error handling

## 3. Tool Exposure Strategy

### 3.1 GCM Built-in MCP Tools (26 tools)

Classification of 26 tools from the manual:

#### Read-Only Tools (Safe - Direct Exposure)
1. `search_policies` - Search policies
2. `fetch_policy_by_id` - Get policy details
3. `get_violation_by_id` - Get violation details
4. `fetch_policy_violations_ticket` - List violation tickets
5. `policy_violations_dashboard` - Violations dashboard
6. `get_filters_by_it_assets` - Get IT asset filters
7. `fetch_detailed_asset_list_by_it_assets` - List IT assets
8. `fetch_individual_asset_detail_by_it_assets` - Get IT asset details
9. `get_category_metadata_by_it_assets` - Get IT asset metadata
10. `get_filters_by_crypto_objects` - Get crypto object filters
11. `fetch_detailed_asset_list_by_crypto_objects` - List crypto objects
12. `fetch_individual_asset_detail_by_crypto_objects` - Get crypto object details
13. `get_category_metadata_by_crypto_objects` - Get crypto object metadata
14. `get_asset_groups` - List asset groups
15. `fetch_asset_metadata` - Get asset metadata
16. `fetch_bulk_vulnerable_crypto_objects` - List vulnerable crypto objects
17. `get_vulnerable_crypto_objects_count` - Count vulnerable crypto objects
18. `get_all_intergration` - List integrations
19. `get_certificate_permissions` - Get certificate permissions
20. `get_vault_details` - Get vault details
21. `get_certificate_details` - Get certificate details
22. `get_user_details_by_username` - Get user details

#### State-Changing Tools (Dangerous - Restricted or Hidden)
23. `create_policy` - Create policy ⚠️
24. `create_violation_ticket` - Create violation ticket ⚠️
25. `renew_ca_signed_certificate` - Renew CA-signed certificate ⚠️
26. `renew_self_signed_certificate` - Renew self-signed certificate ⚠️

### 3.2 Tool Exposure Profiles

#### Profile: `readonly` (Default)
- Exposes Read-Only Tools (1-22) only
- Optimal for normal AI coding agent use
- Most secure profile

#### Profile: `ops`
- Read-Only Tools + `create_violation_ticket`
- For operations teams creating tickets

#### Profile: `admin`
- All tools (1-26)
- For administrators only
- Requires strict access control

### 3.3 Tool Mapping Strategy

Phase 1: Expose GCM tools **as-is** (no renaming). Add metadata:

- Add `category` tag to each tool (`readonly` / `state-changing`)
- Add `risk_level` (`safe` / `moderate` / `high`)
- Enhance tool descriptions with safety information

Phase 2+: Add abstraction layer if needed.

## 4. Authentication Flow

### 4.1 stdio Mode Authentication (Phase 1)

```
┌─────────────┐
│ Relay Start │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│ Load credentials from:          │
│ 1. Environment variables        │
│ 2. Config file (config.toml)    │
│ 3. .env file                    │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Authenticate to GCM:            │
│ 1. Get OAuth2 token (Keycloak)  │
│ 2. Authorize with GCM           │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Cache Access Token              │
│ (in-memory, TTL-based)          │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Ready to serve MCP requests     │
└─────────────────────────────────┘
```

**Key Points:**
- Credentials held in Relay process (not exposed to AI agent)
- Automatic token refresh (before expiry)
- Fail fast on authentication errors

### 4.2 HTTP Mode Authentication (Phase 2)

```
┌─────────────┐
│ AI Agent    │
└──────┬──────┘
       │ Authorization: Bearer <refresh_token>
       ▼
┌─────────────────────────────────┐
│ Relay: Validate Refresh Token   │
│ - Token introspection           │
│ - Signature verification        │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Exchange for Access Token       │
│ - refresh_token grant           │
│ - Cache with TTL                │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Call GCM MCP with Access Token  │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Return result to AI Agent       │
└─────────────────────────────────┘
```

**Key Points:**
- Refresh Token held by AI agent (long-lived)
- Access Token obtained by Relay (short-lived)
- Refresh Token never sent to GCM
- Token cache for performance

## 5. Configuration Management

### 5.1 Configuration File Structure

```toml
# config/relay.toml

[relay]
mode = "stdio"  # "stdio" or "http"
log_level = "INFO"
profile = "readonly"  # "readonly", "ops", "admin"

[relay.http]
# HTTP mode settings (Phase 2)
host = "0.0.0.0"
port = 8002
enable_cors = true

[gcm]
# GCM connection settings
url = "https://gcm.example.com:31443/ibm/mcp/mcp"
verify_ssl = false
request_timeout = 30

[gcm.auth]
# Authentication settings (stdio mode)
username = ""  # Override with GCM_USERNAME env var
password = ""  # Override with GCM_PASSWORD env var
client_id = "gcmclient"
client_secret = ""  # Override with GCM_CLIENT_SECRET env var

[gcm.oidc]
# OIDC Provider settings
host = "gcm.example.com"
port = 30443
realm = "gcmrealm"

[policy]
# Tool access policy
config_file = "config/tools.yaml"

[audit]
# Audit logging
enabled = true
log_file = "logs/audit.jsonl"
log_rotation = "daily"
retention_days = 90
```

### 5.2 Tool Policy Configuration

```yaml
# config/tools.yaml

# Active profile
profile: readonly

# Profile definitions
profiles:
  readonly:
    description: "Read-only access to GCM data"
    allow:
      - search_policies
      - fetch_policy_by_id
      - get_violation_by_id
      - fetch_policy_violations_ticket
      - policy_violations_dashboard
      - get_filters_by_it_assets
      - fetch_detailed_asset_list_by_it_assets
      - fetch_individual_asset_detail_by_it_assets
      - get_category_metadata_by_it_assets
      - get_filters_by_crypto_objects
      - fetch_detailed_asset_list_by_crypto_objects
      - fetch_individual_asset_detail_by_crypto_objects
      - get_category_metadata_by_crypto_objects
      - get_asset_groups
      - fetch_asset_metadata
      - fetch_bulk_vulnerable_crypto_objects
      - get_vulnerable_crypto_objects_count
      - get_all_intergration
      - get_certificate_permissions
      - get_vault_details
      - get_certificate_details
      - get_user_details_by_username

  ops:
    description: "Operations team access"
    allow:
      - "*readonly"  # Include all readonly tools
      - create_violation_ticket

  admin:
    description: "Full administrative access"
    allow:
      - "*"  # All tools

# Tool-specific restrictions (optional)
tool_restrictions:
  create_policy:
    max_calls_per_hour: 10
    require_confirmation: true
    
  renew_ca_signed_certificate:
    max_calls_per_hour: 5
    require_confirmation: true
```

## 6. Security Considerations

### 6.1 Defense in Depth

1. **Startup Checks**
   - Validate configuration files
   - Verify required environment variables
   - Test GCM connection
   - Validate credentials

2. **Runtime Checks**
   - Validate tool calls against allowlist
   - Validate parameters against schema
   - Sanitize inputs
   - Rate limiting (Phase 2)

3. **Audit Logging**
   - Log all tool invocations
   - Log authentication events
   - Log error events
   - Regular log review

### 6.2 Credential Management

#### stdio Mode
- Environment variables preferred (`GCM_USERNAME`, `GCM_PASSWORD`, `GCM_CLIENT_SECRET`)
- Config file as fallback
- Config file in `.gitignore`
- File permissions: 600 (owner read/write only)

#### HTTP Mode (Phase 2)
- Refresh Token only distributed to clients
- Access Token held server-side only
- Token rotation recommended
- Minimize token scope

### 6.3 Network Security

- TLS required (GCM connection)
- Certificate verification (production)
- Self-signed certificate support (development only)
- Timeout configuration

## 7. Error Handling Strategy

### 7.1 Error Categories

1. **Configuration Errors**
   - Detected at startup
   - Immediate exit (fail fast)
   - Clear error messages

2. **Authentication Errors**
   - Automatic retry (once)
   - Clear error on failure
   - Suggest credential issues

3. **Authorization Errors**
   - Tool not in allowlist
   - Profile lacks permission
   - Clear rejection reason

4. **GCM API Errors**
   - Return GCM error as-is
   - Timeout handling
   - Connection error retry

5. **Validation Errors**
   - Parameter validation failure
   - Schema mismatch
   - Detailed error message

### 7.2 Error Response Format

```json
{
  "error": {
    "code": "TOOL_NOT_ALLOWED",
    "message": "Tool 'create_policy' is not allowed in profile 'readonly'",
    "details": {
      "tool": "create_policy",
      "profile": "readonly",
      "allowed_tools": ["search_policies", "fetch_policy_by_id", ...],
      "required_profile": "admin"
    }
  }
}
```

## 8. Deployment Strategy

### 8.1 Phase 1: stdio Mode (MVP)

**Target Users:**
- Local developers
- AI coding agents (Cursor, Claude Desktop)

**Deployment:**
```bash
# Installation
pip install -r requirements.txt

# Configuration
cp config/relay.example.toml config/relay.toml
# Edit config/relay.toml with your GCM settings

# Set credentials
export GCM_USERNAME="your-username"
export GCM_PASSWORD="your-password"
export GCM_CLIENT_SECRET="your-client-secret"

# Run
python -m gcm_relay --mode stdio
```

**MCP Client Configuration (Cursor/Claude):**
```json
{
  "mcpServers": {
    "gcm": {
      "command": "python",
      "args": ["-m", "gcm_relay", "--mode", "stdio"],
      "env": {
        "GCM_USERNAME": "your-username",
        "GCM_PASSWORD": "your-password",
        "GCM_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

### 8.2 Phase 2: HTTP Mode

**Target Users:**
- Remote AI agents
- CI/CD pipelines
- Long-running automation

**Deployment:**
```bash
# Run as HTTP server
python -m gcm_relay --mode http --host 0.0.0.0 --port 8002

# Or with Docker
docker run -p 8002:8002 \
  -e GCM_USERNAME=admin \
  -e GCM_PASSWORD=secret \
  -e GCM_CLIENT_SECRET=secret \
  gcm-mcp-relay:latest
```

**Client Configuration:**
```json
{
  "mcpServers": {
    "gcm": {
      "transport": "sse",
      "url": "http://relay.example.com:8002/mcp",
      "headers": {
        "Authorization": "Bearer <refresh_token>"
      }
    }
  }
}
```

## 9. Monitoring and Observability

### 9.1 Metrics (Phase 2)

- Tool invocation count (per tool)
- Tool invocation latency
- Authentication success/failure rate
- Token refresh count
- Error rate (per error type)

### 9.2 Logging

**Structured Logging Format:**
```json
{
  "timestamp": "2026-03-27T08:00:00Z",
  "level": "INFO",
  "component": "tool_executor",
  "event": "tool_invocation",
  "tool": "fetch_policy_by_id",
  "user": "ai-agent-001",
  "duration_ms": 234,
  "success": true
}
```

**Log Levels:**
- `DEBUG`: Detailed debug information
- `INFO`: Normal operation logs
- `WARNING`: Warnings (successful retry, etc.)
- `ERROR`: Errors (failed operations)
- `CRITICAL`: Critical errors (startup failure, etc.)

### 9.3 Audit Trail

All tool invocations logged:
```json
{
  "timestamp": "2026-03-27T08:00:00Z",
  "user": "ai-agent-001",
  "tool": "fetch_policy_by_id",
  "arguments": {"policy_id": "POL-123"},
  "result": "success",
  "duration_ms": 234,
  "gcm_response_code": 200
}
```

## 10. Testing Strategy

### 10.1 Unit Tests
- Component unit tests
- Mock GCM API calls
- Policy engine logic tests

### 10.2 Integration Tests
- Real GCM environment integration
- Authentication flow tests
- End-to-end tool invocation tests

### 10.3 Security Tests
- Unauthorized tool call rejection tests
- Authentication failure behavior tests
- Parameter injection protection tests

## 11. Future Enhancements

### Phase 3+
1. **Tool Abstraction Layer**
   - Logical tool names (`crypto.list_assets`, etc.)
   - Combine multiple GCM tools into high-level operations

2. **Advanced Policy Engine**
   - Time-based access control
   - IP address-based restrictions
   - Tool invocation frequency limits

3. **Multi-Tenant Support**
   - Multiple GCM environment connections
   - Tenant-specific policy settings

4. **Web UI**
   - Tool invocation history visualization
   - Policy configuration GUI
   - Real-time monitoring

## 12. References

- [GCM MCP Server Manual](../work/Building_agents_for_IBM_Guardium_Cryptography_Manager_using_inbuilt_MCP_server.md)
- [MCP Relay Design Summary](../work/MCP_Relay_Design_Summary_for_GCM_MCP_Server.md)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [GCM MCP Server Reference Implementation](c:/workspace/gcm-mcp-server)