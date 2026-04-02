# IBM Bob Slash Command for GCM MCP Relay

This directory contains the `/gcm` slash command configuration for IBM Bob to provide secure, policy-controlled access to IBM Guardium Cryptography Manager operations.

## Overview

IBM Bob uses **Markdown-based slash commands** (`.md` files) to define custom commands. The `/gcm` command routes all GCM operations through the gcm-mcp-relay with proper authentication, access control, and audit logging.

## Command Details

### `/gcm` - GCM Operations Router

**File**: `gcm.md`

**Purpose**: Routes all GCM operations through the gcm-mcp-relay with authentication, access control, and audit logging.

**Usage**:
```
/gcm <your request or command>
```

**Examples**:
```
/gcm List all cryptographic keys
/gcm Search for key management tools
/gcm Show system health status
/gcm Create a violation ticket for unauthorized access
```

## Installation

### Prerequisites

1. **GCM MCP Relay Running**: Ensure the gcm-mcp-relay Docker container is running
   ```bash
   cd /path/to/gcm-mcp-relay
   docker compose up -d
   ```

2. **Configuration Files**: Verify `config/relay.toml` and `config/policy.yaml` are properly configured

3. **Credentials**: Ensure `.env` file contains required credentials:
   ```bash
   GCM_USERNAME=your_username
   GCM_PASSWORD=your_password
   GCM_CLIENT_SECRET=your_client_secret
   ```

### For IBM Bob Users

1. **Create Bob commands directory** (if it doesn't exist):
   ```bash
   mkdir -p ~/.bob/commands
   ```

2. **Copy the command file** to your Bob configuration directory:
   ```bash
   cp bob-commands/gcm.md ~/.bob/commands/
   ```

3. **Restart IBM Bob** to load the new command

4. **Verify installation**:
   - Type `/` in Bob to see the list of available commands
   - `gcm` should appear in the list

### For IBM Bob Administrators

If you manage Bob for multiple users, place the command file in the shared commands directory:

```bash
cp bob-commands/gcm.md /opt/ibm-bob/commands/
```

## Usage Examples

### Example 1: List Cryptographic Keys

```
/gcm List all AES-256 keys
```

### Example 2: Search for Tools

```
/gcm What tools are available for key management?
```

### Example 3: Check System Status

```
/gcm Show system health
```

### Example 4: View Policy Information

```
/gcm Show all security policies
```

### Example 5: Query Audit Logs

```
/gcm Show recent audit events
```

### Example 6: Create Violation Ticket (ops profile required)

```
/gcm Create a violation ticket for unauthorized key access attempt
```

## Access Profiles

The gcm-mcp-relay enforces three access profiles:

### readonly (Default)
- **Tools**: 22 read-only tools
- **Use Case**: Safe operations, information retrieval
- **Examples**: list_keys, get_key_details, search_keys, view_policies

### ops (Operations Team)
- **Tools**: readonly + create_violation_ticket
- **Use Case**: Operations team with incident management
- **Examples**: All readonly tools + create compliance tickets

### admin (Full Access)
- **Tools**: All 26 tools
- **Use Case**: Full administrative access
- **Examples**: All tools including generate_key, rotate_key, delete_key

## Configuration

### Changing Your Profile

Edit `config/policy.yaml` in the gcm-mcp-relay directory:

```yaml
profiles:
  readonly:
    allowed_tools:
      - "*readonly"  # All 22 read-only tools
  
  ops:
    allowed_tools:
      - "*readonly"
      - "create_violation_ticket"
  
  admin:
    allowed_tools:
      - "*"  # All 26 tools

# Set your default profile
default_profile: "readonly"  # Change to "ops" or "admin" as needed
```

After changing the profile:
```bash
docker compose restart
```

## Troubleshooting

### Command Not Found

**Problem:** `/gcm` returns "Unknown command"

**Solution:**
1. Verify the command file is in `~/.bob/commands/gcm.md`
2. Restart IBM Bob
3. Check Bob's command loading logs

### MCP Relay Not Connected

**Problem:** "Cannot connect to gcm-mcp-relay"

**Solution:**
1. Verify gcm-mcp-relay container is running:
   ```bash
   docker compose ps
   ```
2. Check container logs:
   ```bash
   docker compose logs gcm-mcp-relay
   ```
3. Verify network connectivity

### Authentication Failed

**Problem:** "Authentication failed" or "Invalid credentials"

**Solution:**
1. Check `.env` file contains correct credentials
2. Verify GCM server is accessible
3. Check Keycloak configuration in `relay.toml`
4. Review authentication logs:
   ```bash
   docker compose logs gcm-mcp-relay | grep -i auth
   ```

### Tool Not Allowed

**Problem:** "Tool not allowed for profile 'readonly'"

**Solution:**
1. Check your current profile in `policy.yaml`
2. Request profile upgrade from administrator if needed
3. Verify the tool is in the allowed_tools list for your profile


## How It Works

1. **User invokes command**: `/gcm <request>`
2. **Bob routes to relay**: Sends request to gcm-mcp-relay
3. **Relay validates**: Checks profile and tool permissions
4. **Relay authenticates**: Obtains OAuth2 token from Keycloak
5. **Relay executes**: Calls GCM MCP server with Bearer token
6. **Relay logs**: Records operation in audit log
7. **Bob displays result**: Formats and presents response

## Technical Architecture

```
┌─────────────────┐
│   IBM Bob       │
│   /gcm command  │
└────────┬────────┘
         │ stdio/HTTP
         ▼
┌─────────────────┐
│  GCM MCP Relay  │
│  (Docker)       │
│  - Auth Manager │
│  - Policy Engine│
│  - Audit Logger │
└────────┬────────┘
         │ HTTPS + JWT
         ▼
┌─────────────────┐
│  GCM MCP Server │
│  (26 tools)     │
└─────────────────┘
```

## Security Considerations

1. **Credential Isolation**: Credentials stored in relay, never exposed to AI agent
2. **Token Management**: Automatic token refresh, in-memory caching only
3. **Access Control**: Profile-based restrictions enforced at multiple points
4. **Audit Trail**: All operations logged with timestamps and user context
5. **Rate Limiting**: Prevents abuse and ensures fair resource usage

## Audit Logs

All operations are logged to `logs/audit.jsonl`:

```json
{
  "timestamp": "2026-04-02T08:00:00Z",
  "tool": "list_keys",
  "profile": "readonly",
  "status": "success",
  "duration_ms": 245,
  "user_context": "IBM Bob session"
}
```

View audit logs:
```bash
docker compose exec gcm-mcp-relay tail -f /logs/audit.jsonl
```

## File Structure

```
bob-commands/
├── gcm.md              # /gcm command (routing directive)
└── README.md           # This file (installation and usage)
```

## Support

For issues or questions:

1. **GCM MCP Relay**: Check the relay's configuration files (`relay.toml`, `policy.yaml`)
2. **IBM Bob**: Consult IBM Bob documentation
3. **GCM Server**: Refer to IBM Guardium Cryptography Manager documentation

---

**Note:** This slash command provides secure, policy-controlled access to GCM operations through the gcm-mcp-relay. All operations are authenticated, authorized, and audited for compliance.