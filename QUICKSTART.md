# Quick Start - Laptop Deployment with IBM Bob

This guide helps you set up GCM MCP Relay on your laptop for use with IBM Bob MCP client via stdio connection.

## 📋 Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose)
- **IBM Bob** MCP client installed
- **GCM credentials** (username, password, client secret)
- **Access to GCM server** with built-in MCP server enabled
- **Git** (for cloning the repository)
- **jq** (for testing - optional)

## 🚀 Setup (3 Steps)

### Step 1: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/khirazo/gcm-mcp-relay.git
cd gcm-mcp-relay

# Copy environment template
cp .env.example .env

# Edit .env with your GCM credentials
# Use your preferred text editor (nano, vim, notepad, etc.)
nano .env
```

**Required values in `.env`:**
```bash
# GCM Server
GCM_HOST=gcmapp.apps.example.com
GCM_API_PORT=443

# OIDC Provider (Keycloak)
GCM_OIDC_HOST=oidc.apps.example.com  # Can be same as GCM_HOST
GCM_OIDC_PORT=443
GCM_OIDC_REALM=gcmrealm

# Authentication (REQUIRED)
GCM_USERNAME=gcm-service-account
GCM_PASSWORD=your-password
GCM_CLIENT_SECRET=your-client-secret

# Optional
GCM_CLIENT_ID=gcmclient
GCM_VERIFY_SSL=false  # Set to true in production
```

**Important Notes:**
- `GCM_OIDC_HOST`: Can be same as `GCM_HOST` or different (e.g., separate Keycloak server)
- `GCM_OIDC_REALM`: Usually `gcmrealm` for GCM (not `master`)
- `GCM_CLIENT_SECRET`: See [docs/KEYCLOAK_CLIENT_SECRET.md](docs/KEYCLOAK_CLIENT_SECRET.md) for how to obtain this
- `GCM_USERNAME`: Use a dedicated service account with appropriate GCM roles

**Optional: Edit `config/relay.toml`** for non-sensitive settings:

```toml
[relay]
log_level = "WARNING"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
                       # WARNING recommended for production (reduces log noise)
```

**Log Level Guidelines:**
- `DEBUG`: Verbose logging for troubleshooting (includes all MCP protocol details)
- `INFO`: Normal operation logging (default for development)
- `WARNING`: Production recommended (errors and warnings only, minimal noise)
- `ERROR`: Only errors (not recommended - may miss important warnings)
- `CRITICAL`: Only critical failures

> **Tip**: Use `WARNING` level in production to reduce log volume. Optional MCP methods like `resources/list` are logged at DEBUG level and won't appear in WARNING mode.

### Step 2: Build Container

```bash
# Build the Docker image
docker compose build

# Verify the build
docker images | grep gcm-mcp-relay
```

Expected output:
```
gcm-mcp-relay:stdio    abc123def456        ~300MB
```

### Step 3: Test the Relay (Optional but Recommended)

Before configuring IBM Bob, test that the relay works correctly:

```bash
# Make the test script executable (Linux/macOS/WSL)
chmod +x scripts/test-mcp.sh

# Run the test
./scripts/test-mcp.sh
```

**Expected output:**
```
=== GCM MCP Relay Test Script ===

Testing MCP protocol with sequential requests in a single session

Sending requests:
1. initialize (MCP 2024-11-05)
2. tools/list

Starting GCM MCP Relay and sending requests...

=== Test Results ===

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
Found 32 tools

{
  "name": "search_policies",
  "description": "Retrieve policies filtered by policy_type, policy_group, active status..."
}
{
  "name": "fetch_policy_by_id",
  "description": "Retrieve one or more policies by their unique policy IDs..."
}
{
  "name": "get_violation_by_id",
  "description": "Fetch Violation By ID"
}
{
  "name": "fetch_policy_violations_ticket",
  "description": "Fetch Policy Violations Ticket"
}
{
  "name": "policy_violations_dashboard",
  "description": "Fetch Policy Violations Dashboard"
}
... (showing first 10 tools)

=== All tests completed ===

Summary:
- Initialize: ✓ Success
- Tools List: ✓ Success (32 tools)

Note: GCM MCP Relay exposes all tools from GCM built-in MCP server
      Access control is enforced by GCM's RBAC (user-based permissions)
```

**If the test fails:**
1. Check `.env` file has correct credentials
2. Verify GCM server is accessible
3. Check Docker logs: `docker compose logs gcm-mcp-relay`
4. See [Troubleshooting](#-troubleshooting) section below

### Step 4: Configure IBM Bob

Add the GCM MCP Relay to IBM Bob's configuration file.

**Location of Bob's config file:**

- **Windows**: `%USERPROFILE%\.bob\settings\mcp_settings.json`
- **macOS**: `~/.bob/settings/mcp_settings.json`
- **Linux**: `~/.bob/settings/mcp_settings.json`

**Configuration examples by platform:**

#### Option 1: Docker Desktop (Windows/macOS/Linux)

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
      "cwd": "/absolute/path/to/gcm-mcp-relay",
      "env": {}
    }
  }
}
```

**Example paths:**
- **Windows**: `C:\\Users\\YourName\\Projects\\gcm-mcp-relay`
- **macOS**: `/Users/yourname/projects/gcm-mcp-relay`
- **Linux**: `/home/yourname/projects/gcm-mcp-relay`

#### Option 2: WSL2 Docker (Windows with WSL2)

If you're using Docker installed in WSL2 (not Docker Desktop), use this configuration:

```json
{
  "mcpServers": {
    "gcm-mcp-relay": {
      "command": "wsl",
      "args": [
        "-d",
        "Ubuntu",
        "bash",
        "-c",
        "cd /path/to/gcm-mcp-relay && docker compose run --rm gcm-mcp-relay"
      ],
      "env": {}
    }
  }
}
```

**Important notes for WSL2:**
- Replace `Ubuntu` with your WSL distribution name (check with `wsl -l -v`)
- Use **Linux-style path** in WSL: `/home/yourname/projects/gcm-mcp-relay`
- If repository is on Windows filesystem, use: `/mnt/c/Users/YourName/Projects/gcm-mcp-relay`

**To find your WSL distribution name:**
```powershell
# Run in PowerShell or Command Prompt
wsl -l -v
```

Example output:
```
  NAME      STATE           VERSION
* Ubuntu    Running         2
```

## ✅ Verify Setup

After configuring IBM Bob, restart Bob and verify the connection:

1. **Restart IBM Bob** to load the new MCP server configuration
2. **Check Bob's MCP status** - you should see `gcm-mcp-relay` listed
3. **Try a simple query**: "List all GCM policies"

**Expected behavior:**
- Bob connects to GCM MCP Relay via stdio
- Relay authenticates with GCM (OAuth2 + authorization)
- Relay exposes all tools from GCM (pass-through)
- Access control enforced by GCM's RBAC (user roles)
- Bob can query GCM data through the relay

## 🔐 Access Control

**GCM MCP Relay uses GCM's native RBAC** for access control:

- All tools from GCM are exposed through the relay (pass-through)
- Tool availability depends on the GCM user's assigned roles
- Access control is enforced by GCM (not by the relay)

**Best Practices:**
1. **Use dedicated service accounts** for AI agents
2. **Assign minimal required roles** in GCM admin console
3. **Monitor audit logs** to track tool usage
4. **Rotate credentials regularly**

**Example GCM User Roles:**
- **Read-only user**: Can query data, cannot modify
- **Operator**: Can query + create tickets
- **Administrator**: Full access to all tools

> **Note**: Configure user roles in GCM admin console, not in the relay configuration.

## 🔍 Troubleshooting

### Authentication Fails (401 Unauthorized)

**Symptom:**
```
ERROR - OAuth2 authentication failed: Client error '401 Unauthorized'
```

**Solutions:**
1. **Check realm**: Ensure `GCM_OIDC_REALM=gcmrealm` (not `master`)
2. **Verify client secret**: See [docs/KEYCLOAK_CLIENT_SECRET.md](docs/KEYCLOAK_CLIENT_SECRET.md)
3. **Check credentials**: Verify `GCM_USERNAME` and `GCM_PASSWORD`

### GCM MCP Server Not Found (404)

**Symptom:**
```
ERROR - GCM API error: 404 - Not Found
```

**Solutions:**
1. **Verify GCM URL**: Should be `https://host:port/ibm/mcp/mcp`
2. **Check GCM version**: Built-in MCP server requires GCM 2.0.1+
3. **Verify MCP is enabled**: Contact GCM administrator

### OIDC Host Configuration

**Symptom:**
```
ERROR - Failed to connect to OIDC provider
```

**Solutions:**
1. **Same host scenario**: Set `GCM_OIDC_HOST` to same value as `GCM_HOST`
2. **Different host scenario**: Set `GCM_OIDC_HOST` to Keycloak server hostname
3. **Check ports**: `GCM_API_PORT` (usually 443) vs `GCM_OIDC_PORT` (may differ)

### SSL Certificate Errors

**Symptom:**
```
ERROR - SSL verification failed
```

**Solutions:**
1. **Development**: Set `GCM_VERIFY_SSL=false` in `.env`
2. **Production**: Install GCM's CA certificate in system trust store
3. **Self-signed certs**: Use `GCM_VERIFY_SSL=false` (not recommended for production)

### Tool Access Denied

**Symptom:**
```
ERROR - Tool execution failed: Access denied
```

**Solutions:**
1. **Check GCM user roles**: Verify user has required permissions in GCM
2. **Review GCM audit logs**: Check for permission denied events
3. **Contact GCM admin**: Request appropriate role assignment

### No Tools Listed

**Symptom:**
```
Tools List: ✓ Success (0 tools)
```

**Solutions:**
1. **Check GCM connection**: Verify relay can connect to GCM MCP server
2. **Check GCM permissions**: User must have access to at least some GCM tools
3. **Review logs**: Check `docker compose logs gcm-mcp-relay` for errors

## 🔧 Log Configuration

The relay's log output can be controlled via `config/relay.toml`:

### Log Levels

```toml
[relay]
log_level = "WARNING"  # Recommended for production
```

**Available levels:**
- `DEBUG`: All logs including MCP protocol details (verbose)
- `INFO`: Normal operation logs (default for development)
- `WARNING`: Errors and warnings only (recommended for production)
- `ERROR`: Only error messages
- `CRITICAL`: Only critical failures

### Log Behavior Changes (v0.1.0+)

**Reduced Log Noise:**
- Optional MCP methods (`resources/list`, `prompts/list`, etc.) are now logged at `DEBUG` level
- These are normal discovery attempts by MCP clients and not errors
- With `WARNING` level, these messages won't appear in logs

**Before (INFO level):**
```
ERROR - Unexpected error: Unknown method: resources/list
Traceback (most recent call last):
  ...
```

**After (WARNING level):**
```
(No output for optional methods - logged at DEBUG level only)
```

### Viewing Logs

```bash
# View Docker logs
docker compose logs gcm-mcp-relay

# Follow logs in real-time
docker compose logs -f gcm-mcp-relay

# View last 50 lines
docker compose logs --tail=50 gcm-mcp-relay

# View audit logs (tool invocations)
cat logs/audit.jsonl | jq
```

### Troubleshooting with Logs

If you need detailed logs for troubleshooting:

1. **Temporarily enable DEBUG logging:**
   ```toml
   [relay]
   log_level = "DEBUG"
   ```

2. **Restart the relay:**
   ```bash
   docker compose down
   docker compose up -d
   ```

3. **Reproduce the issue** and check logs

4. **Restore WARNING level** after troubleshooting

## 📚 Next Steps

- **Read the documentation**: See [README.md](README.md) for architecture details
- **Configure GCM roles**: Set up appropriate user roles in GCM admin console
- **View audit logs**: Check `logs/audit.jsonl` for tool invocation history
- **Explore tools**: Ask Bob "What GCM tools are available?"
- **Adjust log level**: Set to `WARNING` for production use

## 🔗 Related Documentation

- [README.md](README.md) - Project overview and architecture
- [docs/KEYCLOAK_CLIENT_SECRET.md](docs/KEYCLOAK_CLIENT_SECRET.md) - How to get client secret
- [docs/architecture.md](docs/architecture.md) - Detailed architecture design

## 💡 Tips

- **Use service accounts** - Create dedicated GCM accounts for AI agents
- **Monitor audit logs** - Track what tools are being called
- **Use test script** - Verify setup before connecting Bob
- **Keep credentials secure** - Never commit `.env` to version control
- **Configure GCM roles** - Access control is managed in GCM, not in the relay

---

**Made with Bob** 🤖