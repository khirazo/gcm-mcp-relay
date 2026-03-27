# GCM MCP Relay - Design Summary

**Project**: GCM MCP Relay  
**Version**: 1.0.0 (Phase 1)  
**Date**: 2026-03-27  
**Status**: Design Complete - Ready for Implementation

## Executive Summary

GCM MCP Relay is a secure intermediary service that enables safe AI agent integration with IBM Guardium Cryptography Manager's built-in MCP server. It addresses three critical challenges:

1. **Complex Authentication**: Simplifies OAuth2/OIDC authentication flow
2. **Access Control**: Enforces profile-based tool access policies
3. **Audit & Compliance**: Provides comprehensive audit logging

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Python Implementation** | Aligns with GCM examples, strong async support, rich ecosystem |
| **Phased Approach** | Phase 1: stdio mode (MVP), Phase 2: HTTP mode (production) |
| **Selective Tool Exposure** | Safe read-only tools exposed, dangerous tools restricted |
| **Configuration-Driven** | Policy changes without code modifications |
| **Defense in Depth** | Multiple enforcement points (startup, registration, execution) |

## Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Coding Agent                          │
└────────────────────────┬────────────────────────────────────┘
                         │ stdio (Phase 1) / HTTP (Phase 2)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   GCM MCP Relay                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MCP Server Layer                                    │   │
│  │  Tool Facade Layer                                   │   │
│  │  Policy Engine                                       │   │
│  │  Authentication Manager                              │   │
│  │  Audit Logger                                        │   │
│  │  GCM MCP Client                                      │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS + Bearer JWT
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          GCM Built-in MCP Server (26 tools)                  │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **MCP Server Layer**: Protocol handling (stdio/HTTP)
2. **Tool Facade Layer**: Tool discovery and schema enhancement
3. **Policy Engine**: Access control and rate limiting
4. **Authentication Manager**: OAuth2/OIDC token management
5. **Audit Logger**: Structured logging of all operations
6. **GCM MCP Client**: Connection to GCM built-in MCP server

## Design Documents

### Core Design Documents

1. **[Architecture Design](architecture.md)** (717 lines)
   - System architecture and component interactions
   - Transport modes (stdio/HTTP)
   - Tool exposure strategy
   - Authentication flows
   - Security positioning

2. **[Project Structure](project-structure.md)** (485 lines)
   - Directory layout and file organization
   - Module dependencies
   - Development workflow
   - Phase 1 implementation priorities

3. **[Authentication Design](authentication-design.md)** (717 lines)
   - stdio mode authentication (Phase 1)
   - HTTP mode authentication (Phase 2)
   - Token management and caching
   - Credential security
   - Error handling

4. **[Tool Abstraction Design](tool-abstraction-design.md)** (717 lines)
   - Tool classification (read-only vs state-changing)
   - Tool registry implementation
   - Tool execution pipeline
   - Schema enhancement
   - Testing strategy

5. **[Policy Engine Design](policy-engine-design.md)** (817 lines)
   - Policy configuration structure
   - Profile-based access control
   - Rate limiting
   - Policy enforcement points
   - Hot reload support (Phase 2)

6. **[Implementation Guide](implementation-guide.md)** (817 lines)
   - Configuration management
   - Audit logging system
   - Error handling strategy
   - Deployment procedures
   - Security checklist

## Tool Classification

### Read-Only Tools (22 tools) - Safe for AI Agents

**Policy & Violations** (5 tools):
- `search_policies`, `fetch_policy_by_id`
- `get_violation_by_id`, `fetch_policy_violations_ticket`, `policy_violations_dashboard`

**IT Assets** (4 tools):
- `get_filters_by_it_assets`, `fetch_detailed_asset_list_by_it_assets`
- `fetch_individual_asset_detail_by_it_assets`, `get_category_metadata_by_it_assets`

**Crypto Objects** (7 tools):
- `get_filters_by_crypto_objects`, `fetch_detailed_asset_list_by_crypto_objects`
- `fetch_individual_asset_detail_by_crypto_objects`, `get_category_metadata_by_crypto_objects`
- `fetch_bulk_vulnerable_crypto_objects`, `get_vulnerable_crypto_objects_count`
- `get_asset_groups`, `fetch_asset_metadata`

**Certificates & Integration** (4 tools):
- `get_certificate_permissions`, `get_vault_details`, `get_certificate_details`
- `get_all_intergration`

**Users** (1 tool):
- `get_user_details_by_username`

### State-Changing Tools (4 tools) - Restricted

| Tool | Risk Level | Default Access |
|------|------------|----------------|
| `create_policy` | HIGH | admin only |
| `create_violation_ticket` | MODERATE | ops, admin |
| `renew_ca_signed_certificate` | HIGH | admin only |
| `renew_self_signed_certificate` | HIGH | admin only |

## Access Control Profiles

### Profile: `readonly` (Default)
- **Purpose**: Safe AI agent access
- **Tools**: All 22 read-only tools
- **Use Case**: General AI coding assistance, data queries

### Profile: `ops`
- **Purpose**: Operations team access
- **Tools**: All readonly tools + `create_violation_ticket`
- **Use Case**: Incident management, ticket creation

### Profile: `admin`
- **Purpose**: Full administrative access
- **Tools**: All 26 tools
- **Use Case**: System administration, policy management

## Authentication Flows

### stdio Mode (Phase 1)

```
Startup → Load Credentials → Authenticate to Keycloak → 
Authorize with GCM → Cache Token → Ready to Serve
```

**Key Points**:
- Credentials from environment variables or config file
- Token cached in memory
- Automatic token refresh before expiry
- No credentials exposed to AI agent

### HTTP Mode (Phase 2)

```
Request with Refresh Token → Validate Token → 
Check Cache → Exchange for Access Token → 
Call GCM → Return Result
```

**Key Points**:
- AI agent holds refresh token
- Relay exchanges for access token
- Access token cached (TTL-based)
- Refresh token never sent to GCM

## Configuration Management

### Configuration Hierarchy

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **Configuration file** (TOML)
4. **Default values** (lowest priority)

### Key Configuration Files

- `config/relay.toml`: Relay server configuration
- `config/tools.yaml`: Tool access policies
- `.env`: Environment variables (gitignored)

### Critical Environment Variables

```bash
GCM_USERNAME          # GCM username (required)
GCM_PASSWORD          # GCM password (required)
GCM_CLIENT_SECRET     # OIDC client secret (required)
GCM_RELAY_PROFILE     # Active profile (optional, default: readonly)
```

## Security Architecture

### Defense in Depth

1. **Startup Validation**
   - Configuration validation
   - Credential verification
   - GCM connectivity test

2. **Registration-Time Filtering**
   - Only allowed tools registered
   - Profile-based filtering

3. **Execution-Time Enforcement**
   - Tool allowlist check
   - Argument validation
   - Rate limiting (Phase 2)

4. **Audit Logging**
   - All operations logged
   - Structured JSON format
   - Tamper-evident logs

### Credential Security

**Storage**:
- Environment variables (preferred)
- Config files with 600 permissions
- Never in version control
- Separate per environment

**Transmission**:
- TLS required for all connections
- Certificate verification (production)
- Bearer token authentication
- Short-lived access tokens

## Audit & Compliance

### Audit Log Format

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
    "duration_ms": 234,
    "response_size_bytes": 1024
  }
}
```

### Logged Events

- Tool invocations (success/failure)
- Authentication events
- Policy violations
- Rate limit violations
- System events (startup, shutdown, errors)

### Log Management

- Structured JSON format
- Daily rotation
- 90-day retention (configurable)
- SIEM integration ready

## Implementation Roadmap

### Phase 1: stdio Mode (MVP) - 4-6 weeks

**Week 1-2: Core Infrastructure**
- [ ] Configuration loader
- [ ] Authentication manager
- [ ] GCM MCP client
- [ ] Basic error handling

**Week 3-4: Policy & Tools**
- [ ] Policy engine
- [ ] Tool registry
- [ ] Tool executor
- [ ] Audit logger

**Week 5-6: Integration & Testing**
- [ ] stdio MCP server
- [ ] End-to-end testing
- [ ] Documentation
- [ ] Example configurations

### Phase 2: HTTP Mode - 3-4 weeks

**Week 1-2: HTTP Server**
- [ ] HTTP/SSE transport
- [ ] OIDC refresh token handling
- [ ] API key management

**Week 3-4: Advanced Features**
- [ ] Rate limiting
- [ ] Hot reload
- [ ] Metrics endpoint
- [ ] Docker deployment

## Testing Strategy

### Unit Tests
- Configuration loading
- Policy engine logic
- Token caching
- Tool classification
- Argument validation

### Integration Tests
- GCM authentication flow
- Tool execution end-to-end
- Policy enforcement
- Audit logging

### Security Tests
- Credential handling
- Policy bypass attempts
- Rate limit enforcement
- Injection attacks

## Deployment Options

### Local Development
```bash
python -m gcm_relay --mode stdio
```

### Docker (Phase 2)
```bash
docker run -p 8002:8002 gcm-mcp-relay:latest
```

### Kubernetes (Future)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gcm-mcp-relay
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: relay
        image: gcm-mcp-relay:latest
```

## Success Criteria

### Phase 1 Success Metrics

- ✅ AI agent can query GCM data without authentication complexity
- ✅ Dangerous tools are not accessible in readonly profile
- ✅ All tool invocations are logged
- ✅ Configuration changes don't require code changes
- ✅ Startup time < 5 seconds
- ✅ Tool execution latency < 500ms overhead

### Phase 2 Success Metrics

- ✅ Remote agents can connect via HTTP
- ✅ Rate limiting prevents abuse
- ✅ Hot reload works without downtime
- ✅ Metrics available for monitoring
- ✅ Docker deployment works out-of-box

## Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| GCM API changes | Version pinning, integration tests |
| Token expiry issues | Proactive refresh, retry logic |
| Performance overhead | Connection pooling, caching |
| Configuration errors | Validation at startup, fail-fast |

### Security Risks

| Risk | Mitigation |
|------|------------|
| Credential exposure | Environment variables, file permissions |
| Policy bypass | Multiple enforcement points |
| Audit log tampering | Structured logs, SIEM integration |
| Unauthorized access | Profile-based access control |

## Future Enhancements

### Phase 3: Advanced Features
- Tool composition (logical tools)
- Multi-tenant support
- Web UI for monitoring
- Advanced rate limiting (per-user, per-IP)
- Webhook notifications

### Phase 4: Enterprise Features
- LDAP/AD integration
- SSO support
- High availability
- Disaster recovery
- Compliance reporting

## References

### Internal Documentation
- [Architecture Design](architecture.md)
- [Project Structure](project-structure.md)
- [Authentication Design](authentication-design.md)
- [Tool Abstraction Design](tool-abstraction-design.md)
- [Policy Engine Design](policy-engine-design.md)
- [Implementation Guide](implementation-guide.md)

### External References
- [GCM MCP Server Manual](../work/Building_agents_for_IBM_Guardium_Cryptography_Manager_using_inbuilt_MCP_server.md)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [IBM Guardium Cryptography Manager](https://www.ibm.com/products/guardium-cryptography-manager)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)

## Approval & Sign-off

### Design Review Checklist

- [x] Architecture reviewed and approved
- [x] Security considerations documented
- [x] Implementation plan defined
- [x] Testing strategy established
- [x] Deployment strategy documented
- [x] Risk mitigation planned

### Next Steps

1. **Review this design summary** with stakeholders
2. **Approve design** and proceed to implementation
3. **Set up development environment**
4. **Begin Phase 1 implementation**
5. **Schedule regular design reviews** during implementation

---

**Design Status**: ✅ Complete - Ready for Implementation  
**Estimated Implementation Time**: 4-6 weeks (Phase 1)  
**Target Release**: Q2 2026
