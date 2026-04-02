---
description: "Always use the gcm-mcp-relay to execute GCM commands and operations"
---

# GCM MCP Relay Command

This slash command ensures that all GCM-related operations are executed through the **gcm-mcp-relay**, providing secure, policy-controlled access to IBM Guardium Cryptography Manager APIs.

## Purpose

When you use `/gcm` followed by any command or request, IBM Bob will:

1. **Route to gcm-mcp-relay**: All operations use the configured gcm-mcp-relay
2. **Access 26 GCM Tools**: Full access to GCM MCP server tools (subject to policy)
3. **Enforce Access Control**: Profile-based restrictions (readonly/ops/admin)
4. **Audit All Operations**: Comprehensive logging of tool invocations

## Usage

### Basic Syntax

```
/gcm <your request or command>
```

### Examples

**List cryptographic keys:**
```
/gcm List all cryptographic keys
```

**Search for specific tools:**
```
/gcm Search for key management tools
```

**Execute specific tool:**
```
/gcm Execute list_keys tool
```

**Check system status:**
```
/gcm Show system health status
```

**Create violation ticket (ops/admin only):**
```
/gcm Create a violation ticket for unauthorized key access
```

**Key lifecycle operations (admin only):**
```
/gcm Generate a new AES-256 key
/gcm Rotate encryption keys for database XYZ
```

## What It Does

The `/gcm` command acts as a **routing directive** that tells IBM Bob to:

- Use the `gcm-mcp-relay` for all tool calls
- Follow the GCM workflow: discover → validate → execute
- Apply proper authentication (OAuth2/OIDC)
- Enforce profile-based access control
- Log all operations for audit compliance

## MCP Tools Available

When you use `/gcm`, Bob has access to these tool categories:

### Read-Only Tools (22 tools - readonly profile)
1. **Key Management** - List, search, and view key details
2. **Policy Management** - View policies and compliance status
3. **Audit & Compliance** - Query audit logs and violation reports
4. **System Information** - View system health and configuration

### State-Changing Tools (4 tools - ops/admin profiles)
1. **create_violation_ticket** - Create compliance violation tickets (ops+)
2. **generate_key** - Generate new cryptographic keys (admin only)
3. **rotate_key** - Rotate existing keys (admin only)
4. **delete_key** - Delete keys (admin only)

## Access Profiles

The relay enforces three access profiles:

| Profile | Tools Available | Use Case |
|---------|----------------|----------|
| **readonly** | 22 read-only tools | Default, safe operations |
| **ops** | readonly + create_violation_ticket | Operations team |
| **admin** | All 26 tools | Full administrative access |

## Workflow Example

```
User: /gcm List all AES keys in production

Bob internally executes:
  1. Validates user profile (readonly sufficient)
  2. Calls gcm-mcp-relay with list_keys tool
  3. Filters results for AES keys
  4. Formats and presents results
  5. Logs operation to audit trail
```

## Technical Details

- **MCP Relay**: gcm-mcp-relay (Docker container)
- **Transport**: stdio (Phase 1) / HTTP (Phase 2)
- **Authentication**: OAuth2/OIDC via Keycloak
- **GCM Backend**: IBM Guardium Cryptography Manager
- **Tools**: 26 GCM MCP server tools (22 safe, 4 dangerous)
- **Audit**: JSONL format logs in `/logs/audit.jsonl`

## Security Features

- **Defense in Depth**: Multiple policy enforcement points
- **Least Privilege**: Default readonly profile
- **Credential Isolation**: Credentials never exposed to AI agent
- **Audit Trail**: All operations logged with timestamps
- **Token Management**: Automatic token refresh and caching

## Notes

- This command is a **routing directive**, not a tool itself
- All actual operations are performed by the gcm-mcp-relay
- Access is controlled by the configured profile in `policy.yaml`
- Dangerous operations require explicit admin profile configuration
- All operations are logged for compliance and audit purposes

## Error Handling

If you encounter errors:

1. **"Tool not allowed"** - Check your profile in `policy.yaml`
2. **"Authentication failed"** - Verify credentials in `.env` file
3. **"Connection refused"** - Ensure gcm-mcp-relay container is running

---

**Made with Bob**