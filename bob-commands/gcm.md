---
description: "Always use the gcm-mcp-relay to execute GCM commands and operations"
---

# GCM MCP Relay Command

This slash command ensures that all GCM-related operations are executed through the **gcm-mcp-relay**, providing secure access to IBM Guardium Cryptography Manager APIs.

## Purpose

When you use `/gcm` followed by any command or request, IBM Bob will:

1. **Route to gcm-mcp-relay**: All operations use the configured gcm-mcp-relay
2. **Access GCM Tools**: Full access to GCM MCP server tools
3. **Audit All Operations**: Comprehensive logging of tool invocations

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

When you use `/gcm`, Bob has access to GCM MCP server tools across these categories:

### Tool Categories
1. **Policy Management** - Search and view policies
2. **Violation Management** - Query violations and create tickets
3. **IT Asset Management** - List and view IT assets
4. **Crypto Object Management** - Manage certificates, keys, and protocols
5. **Certificate Lifecycle** - Certificate permissions and renewal
6. **Integration Management** - View integration configurations
7. **User Management** - Query user details

**Note**: The specific tools available depend on the GCM MCP server version and configuration.

## Workflow Example

```
User: /gcm List all AES keys in production

Bob internally executes:
  1. Calls gcm-mcp-relay with appropriate tool
  2. Filters results for AES keys
  3. Formats and presents results
  4. Logs operation to audit trail
```

## Technical Details

- **MCP Relay**: gcm-mcp-relay (Docker container)
- **Transport**: stdio (Phase 1) / HTTP (Phase 2)
- **Authentication**: OAuth2/OIDC via Keycloak
- **GCM Backend**: IBM Guardium Cryptography Manager
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
- All operations are logged for compliance and audit purposes
- State-changing operations should be used with caution

## Error Handling

If you encounter errors:

1. **"Authentication failed"** - Verify credentials in `.env` file
2. **"Connection refused"** - Ensure gcm-mcp-relay container is running
3. **"Tool execution failed"** - Check GCM server logs for details

---

**Made with Bob**