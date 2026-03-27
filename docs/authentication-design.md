# GCM MCP Relay - Authentication & Authorization Design

## 1. Overview

The authentication system manages credentials and tokens for connecting to the GCM built-in MCP server. It supports two operational modes with different authentication strategies.

## 2. Authentication Modes

### 2.1 stdio Mode (Phase 1)

**Use Case**: Local development, AI coding agents on the same machine

**Trust Model**: 
- Relay and AI agent run on the same host
- Same user context
- No network boundary

**Authentication Flow**:
```
┌─────────────────────────────────────────────────────────────┐
│ 1. Relay Startup                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Load Credentials                                          │
│    Priority:                                                 │
│    1. Environment variables (GCM_USERNAME, GCM_PASSWORD)     │
│    2. Config file (config/relay.toml)                        │
│    3. .env file                                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Validate Credentials                                      │
│    - Check all required fields present                       │
│    - Fail fast if missing                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Authenticate to Keycloak                                  │
│    POST /realms/gcmrealm/protocol/openid-connect/token      │
│    - grant_type: password                                    │
│    - username: <from config>                                 │
│    - password: <from config>                                 │
│    - client_id: <from config>                                │
│    - client_secret: <from config>                            │
│    - scope: openid                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Receive Tokens                                            │
│    - access_token (JWT, 5-15 min TTL)                        │
│    - refresh_token (long-lived)                              │
│    - expires_in (seconds)                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Authorize with GCM                                        │
│    POST /ibm/usermanagement/api/v2/authorization             │
│    Headers: Authorization: Bearer <access_token>             │
│    Body: {"tenantId": ""}                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Cache Token                                               │
│    - Store access_token in memory                            │
│    - Store refresh_token in memory                           │
│    - Calculate expiry time (now + expires_in - 60s buffer)   │
│    - Store user_id from authorization response               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Ready to Serve                                            │
│    - Accept MCP requests from AI agent                       │
│    - Automatically refresh token before expiry               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 HTTP Mode (Phase 2)

**Use Case**: Remote agents, CI/CD, long-running automation

**Trust Model**:
- Relay and AI agent on different hosts
- Network boundary
- Refresh token as credential

**Authentication Flow**:
```
┌─────────────────────────────────────────────────────────────┐
│ AI Agent                                                     │
│ - Holds OIDC Refresh Token                                   │
│ - Sends with each MCP request                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Authorization: Bearer <refresh_token>
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Relay Receives Request                                    │
│    - Extract refresh_token from Authorization header         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Validate Refresh Token                                    │
│    - Check token format (JWT)                                │
│    - Verify signature (optional)                             │
│    - Check expiry (optional)                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Check Token Cache                                         │
│    - Key: hash(refresh_token)                                │
│    - If cached and not expired: use cached access_token      │
│    - If not cached or expired: proceed to exchange           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Exchange for Access Token                                 │
│    POST /realms/gcmrealm/protocol/openid-connect/token      │
│    - grant_type: refresh_token                               │
│    - refresh_token: <from request>                           │
│    - client_id: <from config>                                │
│    - client_secret: <from config>                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Receive New Access Token                                  │
│    - access_token (JWT, 5-15 min TTL)                        │
│    - refresh_token (may be rotated)                          │
│    - expires_in (seconds)                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Cache Access Token                                        │
│    - Key: hash(refresh_token)                                │
│    - Value: access_token                                     │
│    - TTL: expires_in - 60s buffer                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Call GCM MCP Server                                       │
│    - Use access_token (not refresh_token)                    │
│    - Authorization: Bearer <access_token>                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Return Result to AI Agent                                 │
└─────────────────────────────────────────────────────────────┘
```

## 3. Token Management

### 3.1 Token Types

#### Access Token
- **Purpose**: Authenticate to GCM MCP server
- **Lifetime**: 5-15 minutes (configurable in Keycloak)
- **Format**: JWT (JSON Web Token)
- **Storage**: In-memory cache only
- **Transmission**: Sent to GCM MCP server only

#### Refresh Token
- **Purpose**: Obtain new access tokens
- **Lifetime**: Hours to days (configurable in Keycloak)
- **Format**: Opaque string or JWT
- **Storage**: 
  - stdio mode: In-memory (obtained at startup)
  - HTTP mode: Provided by client with each request
- **Transmission**: Sent to Keycloak only (never to GCM)

### 3.2 Token Cache Design

```python
class TokenCache:
    """
    In-memory token cache with TTL.
    
    Key: hash(refresh_token) or "default" for stdio mode
    Value: {
        "access_token": str,
        "expires_at": datetime,
        "user_id": str
    }
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[str]:
        """Get cached access token if not expired."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry and datetime.now() < entry["expires_at"]:
                return entry["access_token"]
            return None
    
    async def set(
        self, 
        key: str, 
        access_token: str, 
        expires_in: int,
        user_id: str
    ):
        """Cache access token with expiry."""
        async with self._lock:
            self._cache[key] = {
                "access_token": access_token,
                "expires_at": datetime.now() + timedelta(seconds=expires_in - 60),
                "user_id": user_id
            }
    
    async def clear(self, key: str):
        """Clear cached token."""
        async with self._lock:
            self._cache.pop(key, None)
```

### 3.3 Token Refresh Strategy

#### Proactive Refresh (stdio mode)
```python
async def ensure_valid_token(self):
    """Ensure we have a valid access token, refreshing if needed."""
    if not self._access_token:
        raise AuthenticationError("Not authenticated")
    
    # Check if token is about to expire (within 60 seconds)
    if datetime.now() >= self._token_expiry:
        logger.info("Access token expiring soon, refreshing...")
        await self._refresh_access_token()
```

#### On-Demand Refresh (HTTP mode)
```python
async def get_access_token(self, refresh_token: str) -> str:
    """Get access token, using cache or refreshing as needed."""
    cache_key = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    # Try cache first
    cached_token = await self._token_cache.get(cache_key)
    if cached_token:
        return cached_token
    
    # Cache miss - exchange refresh token
    access_token = await self._exchange_refresh_token(refresh_token)
    return access_token
```

## 4. Credential Management

### 4.1 Credential Sources (Priority Order)

1. **Environment Variables** (Highest Priority)
   ```bash
   export GCM_USERNAME="admin"
   export GCM_PASSWORD="secret"
   export GCM_CLIENT_ID="gcmclient"
   export GCM_CLIENT_SECRET="client-secret"
   ```

2. **Configuration File**
   ```toml
   [gcm.auth]
   username = "admin"
   password = "secret"
   client_id = "gcmclient"
   client_secret = "client-secret"
   ```

3. **.env File**
   ```
   GCM_USERNAME=admin
   GCM_PASSWORD=secret
   GCM_CLIENT_ID=gcmclient
   GCM_CLIENT_SECRET=client-secret
   ```

### 4.2 Credential Validation

```python
class CredentialValidator:
    """Validate authentication credentials at startup."""
    
    REQUIRED_FIELDS = [
        "username",
        "password",
        "client_id",
        "client_secret"
    ]
    
    def validate(self, credentials: Dict[str, str]) -> List[str]:
        """
        Validate credentials and return list of missing fields.
        
        Returns:
            Empty list if valid, list of missing field names otherwise.
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            if not credentials.get(field):
                missing.append(field)
        return missing
```

### 4.3 Credential Security

#### stdio Mode
- Credentials stored in process memory only
- Never written to disk (except config file)
- Config file permissions: 600 (owner read/write only)
- Config file in `.gitignore`
- Environment variables preferred over config file

#### HTTP Mode
- Relay never stores client refresh tokens
- Refresh tokens provided with each request
- Access tokens cached in memory only
- No persistent storage of any tokens

## 5. Error Handling

### 5.1 Authentication Errors

#### Invalid Credentials
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Authentication failed: invalid username or password",
    "details": {
      "username": "admin",
      "keycloak_url": "https://gcm.example.com:30443"
    }
  }
}
```

#### Missing Credentials
```json
{
  "error": {
    "code": "MISSING_CREDENTIALS",
    "message": "Required credentials not provided",
    "details": {
      "missing_fields": ["password", "client_secret"],
      "help": "Set GCM_PASSWORD and GCM_CLIENT_SECRET environment variables"
    }
  }
}
```

#### Token Expired
```json
{
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Access token has expired",
    "details": {
      "expired_at": "2026-03-27T08:00:00Z",
      "action": "Token will be automatically refreshed"
    }
  }
}
```

#### Refresh Failed
```json
{
  "error": {
    "code": "REFRESH_FAILED",
    "message": "Failed to refresh access token",
    "details": {
      "reason": "Refresh token has been revoked",
      "action": "Re-authenticate with username and password"
    }
  }
}
```

### 5.2 Authorization Errors

#### GCM Authorization Failed
```json
{
  "error": {
    "code": "GCM_AUTHORIZATION_FAILED",
    "message": "GCM authorization endpoint returned error",
    "details": {
      "status_code": 403,
      "gcm_message": "User does not have required permissions"
    }
  }
}
```

### 5.3 Retry Strategy

```python
class AuthenticationManager:
    """Authentication manager with retry logic."""
    
    MAX_RETRIES = 1
    RETRY_DELAY = 1.0  # seconds
    
    async def authenticate(self) -> bool:
        """Authenticate with retry on transient failures."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return await self._do_authenticate()
            except TransientError as e:
                if attempt < self.MAX_RETRIES:
                    logger.warning(f"Authentication failed (attempt {attempt + 1}), retrying...")
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    raise
```

## 6. Security Considerations

### 6.1 Credential Storage

**DO**:
- Use environment variables for credentials
- Set restrictive file permissions (600) on config files
- Add config files to `.gitignore`
- Use separate credentials for each environment

**DON'T**:
- Commit credentials to version control
- Log credentials (even in debug mode)
- Store credentials in plaintext in shared locations
- Reuse credentials across environments

### 6.2 Token Handling

**DO**:
- Cache tokens in memory only
- Clear tokens on shutdown
- Use short-lived access tokens
- Rotate refresh tokens regularly

**DON'T**:
- Store tokens on disk
- Log token values
- Send refresh tokens to GCM
- Share tokens between users

### 6.3 Network Security

**DO**:
- Use TLS for all connections
- Verify server certificates (production)
- Set appropriate timeouts
- Use secure cipher suites

**DON'T**:
- Disable TLS verification (except dev)
- Use HTTP (unencrypted)
- Trust self-signed certs in production
- Allow unlimited connection time

## 7. Implementation Classes

### 7.1 AuthenticationManager

```python
class AuthenticationManager:
    """
    Manages authentication to GCM via Keycloak.
    
    Supports both stdio mode (credentials from config) and
    HTTP mode (refresh token from client).
    """
    
    def __init__(
        self,
        keycloak_url: str,
        client_id: str,
        client_secret: str,
        gcm_base_url: str,
        token_cache: TokenCache
    ):
        self.keycloak_url = keycloak_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.gcm_base_url = gcm_base_url
        self.token_cache = token_cache
    
    async def authenticate_with_password(
        self,
        username: str,
        password: str
    ) -> str:
        """Authenticate using username/password (stdio mode)."""
        # 1. Get access token from Keycloak
        # 2. Authorize with GCM
        # 3. Cache token
        # 4. Return access token
        pass
    
    async def authenticate_with_refresh_token(
        self,
        refresh_token: str
    ) -> str:
        """Authenticate using refresh token (HTTP mode)."""
        # 1. Check cache
        # 2. Exchange refresh token for access token
        # 3. Cache token
        # 4. Return access token
        pass
    
    async def ensure_valid_token(self, key: str = "default") -> str:
        """Ensure we have a valid access token."""
        # 1. Check cache
        # 2. Refresh if needed
        # 3. Return access token
        pass
```

### 7.2 TokenCache

```python
class TokenCache:
    """In-memory token cache with TTL."""
    
    async def get(self, key: str) -> Optional[str]:
        """Get cached access token if not expired."""
        pass
    
    async def set(
        self,
        key: str,
        access_token: str,
        expires_in: int,
        user_id: str
    ):
        """Cache access token with expiry."""
        pass
    
    async def clear(self, key: str):
        """Clear cached token."""
        pass
```

### 7.3 CredentialLoader

```python
class CredentialLoader:
    """Load credentials from environment, config, or .env file."""
    
    def load(self) -> Dict[str, str]:
        """
        Load credentials with priority:
        1. Environment variables
        2. Config file
        3. .env file
        """
        pass
    
    def validate(self, credentials: Dict[str, str]) -> List[str]:
        """Validate credentials and return missing fields."""
        pass
```

## 8. Testing Strategy

### 8.1 Unit Tests

- Token cache operations
- Credential loading priority
- Token expiry calculation
- Error handling

### 8.2 Integration Tests

- Keycloak authentication flow
- GCM authorization flow
- Token refresh flow
- Error scenarios (invalid credentials, expired tokens)

### 8.3 Mock Keycloak

For testing without real Keycloak:
```python
class MockKeycloakServer:
    """Mock Keycloak server for testing."""
    
    def __init__(self):
        self.valid_credentials = {
            "admin": "password123"
        }
        self.issued_tokens = {}
    
    async def token_endpoint(self, request):
        """Mock token endpoint."""
        # Validate credentials
        # Issue mock tokens
        # Return response
        pass
```

## 9. Configuration Examples

### 9.1 stdio Mode Configuration

```toml
[gcm]
url = "https://gcm.example.com:31443/ibm/mcp/mcp"

[gcm.auth]
# Credentials (prefer environment variables)
username = ""  # Set via GCM_USERNAME
password = ""  # Set via GCM_PASSWORD
client_id = "gcmclient"
client_secret = ""  # Set via GCM_CLIENT_SECRET

[gcm.oidc]
host = "gcm.example.com"
port = 30443
realm = "gcmrealm"
```

### 9.2 HTTP Mode Configuration (Phase 2)

```toml
[relay]
mode = "http"

[relay.http]
host = "0.0.0.0"
port = 8002

[gcm]
url = "https://gcm.example.com:31443/ibm/mcp/mcp"

[gcm.auth]
# Only client credentials needed (refresh tokens from clients)
client_id = "gcmclient"
client_secret = ""  # Set via GCM_CLIENT_SECRET

[gcm.oidc]
host = "gcm.example.com"
port = 30443
realm = "gcmrealm"
```

## 10. References

- [GCM Authentication Documentation](../work/Building_agents_for_IBM_Guardium_Cryptography_Manager_using_inbuilt_MCP_server.md#add-authentication)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)