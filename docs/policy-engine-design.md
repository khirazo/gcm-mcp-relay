# GCM MCP Relay - Policy Engine Design

## 1. Overview

The Policy Engine enforces access control policies for GCM MCP tools. It implements profile-based access control, tool allowlisting, and argument validation to ensure AI agents can only perform authorized operations.

## 2. Design Principles

### 2.1 Defense in Depth
- **Startup validation**: Load and validate policy configuration
- **Registration-time filtering**: Only register allowed tools
- **Execution-time enforcement**: Validate every tool call
- **Argument validation**: Check parameters against schema

### 2.2 Configuration-Driven
- Policies defined in YAML files
- Profile-based access control
- No code changes for policy updates
- Hot-reload support (Phase 2)

### 2.3 Fail-Safe Defaults
- Default profile: `readonly` (most restrictive)
- Unknown tools: denied by default
- Invalid configuration: fail to start
- Missing policy file: use built-in defaults

## 3. Policy Configuration Structure

### 3.1 Policy File Format

```yaml
# config/tools.yaml

# Active profile (can be overridden by environment variable)
profile: readonly

# Profile definitions
profiles:
  # Read-only profile (default, most restrictive)
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

  # Operations profile (read + ticket creation)
  ops:
    description: "Operations team access with ticket creation"
    allow:
      - "*readonly"  # Include all readonly tools
      - create_violation_ticket

  # Admin profile (full access)
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
    allowed_certificate_types:
      - production
      - staging

# Global settings
settings:
  # Deny unknown tools by default
  deny_unknown_tools: true
  
  # Log all policy violations
  log_violations: true
  
  # Fail on policy load errors
  fail_on_policy_error: true
```

### 3.2 Profile Inheritance

```yaml
profiles:
  # Base profile
  base:
    allow:
      - search_policies
      - fetch_policy_by_id
  
  # Extended profile (inherits from base)
  extended:
    extends: base
    allow:
      - get_violation_by_id
      - create_violation_ticket
  
  # Multiple inheritance
  admin:
    extends:
      - extended
      - certificate_manager
    allow:
      - create_policy
```

## 4. Policy Engine Implementation

### 4.1 Core Classes

```python
@dataclass
class Profile:
    """Access control profile."""
    name: str
    description: str
    allowed_tools: Set[str]
    extends: Optional[List[str]] = None
    restrictions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolRestriction:
    """Restrictions for a specific tool."""
    tool_name: str
    max_calls_per_hour: Optional[int] = None
    require_confirmation: bool = False
    allowed_values: Dict[str, List[Any]] = field(default_factory=dict)

@dataclass
class PolicyConfig:
    """Complete policy configuration."""
    active_profile: str
    profiles: Dict[str, Profile]
    tool_restrictions: Dict[str, ToolRestriction]
    settings: Dict[str, Any]
```

### 4.2 PolicyEngine Class

```python
class PolicyEngine:
    """
    Enforces access control policies for GCM MCP tools.
    
    Responsibilities:
    - Load and validate policy configuration
    - Resolve profile inheritance
    - Check tool access permissions
    - Enforce tool-specific restrictions
    - Track usage for rate limiting
    """
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: Optional[PolicyConfig] = None
        self.usage_tracker = UsageTracker()
        self._initialized = False
    
    async def initialize(self):
        """Load and validate policy configuration."""
        if self._initialized:
            return
        
        # Load configuration
        self.config = await self._load_config()
        
        # Validate configuration
        self._validate_config()
        
        # Resolve profile inheritance
        self._resolve_inheritance()
        
        self._initialized = True
        logger.info(
            f"Policy engine initialized with profile: {self.config.active_profile}"
        )
    
    def is_tool_allowed(self, tool_name: str, profile: Optional[str] = None) -> bool:
        """
        Check if a tool is allowed for the given profile.
        
        Args:
            tool_name: Name of the tool
            profile: Profile name (uses active profile if None)
            
        Returns:
            True if tool is allowed, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Policy engine not initialized")
        
        profile_name = profile or self.config.active_profile
        profile_obj = self.config.profiles.get(profile_name)
        
        if not profile_obj:
            logger.warning(f"Unknown profile: {profile_name}")
            return False
        
        # Check if tool is in allowlist
        if "*" in profile_obj.allowed_tools:
            return True  # Admin profile allows all
        
        return tool_name in profile_obj.allowed_tools
    
    def get_allowed_tools(self, profile: Optional[str] = None) -> List[str]:
        """
        Get list of allowed tools for the given profile.
        
        Args:
            profile: Profile name (uses active profile if None)
            
        Returns:
            List of allowed tool names
        """
        if not self._initialized:
            raise RuntimeError("Policy engine not initialized")
        
        profile_name = profile or self.config.active_profile
        profile_obj = self.config.profiles.get(profile_name)
        
        if not profile_obj:
            return []
        
        # If wildcard, return all known tools
        if "*" in profile_obj.allowed_tools:
            return list(ALL_KNOWN_TOOLS)
        
        return list(profile_obj.allowed_tools)
    
    async def check_restrictions(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Optional[str]:
        """
        Check tool-specific restrictions.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            None if allowed, error message if restricted
        """
        restriction = self.config.tool_restrictions.get(tool_name)
        if not restriction:
            return None  # No restrictions
        
        # Check rate limiting
        if restriction.max_calls_per_hour:
            if not await self.usage_tracker.check_rate_limit(
                tool_name,
                restriction.max_calls_per_hour
            ):
                return f"Rate limit exceeded for {tool_name}"
        
        # Check allowed values
        for param, allowed_values in restriction.allowed_values.items():
            if param in arguments:
                if arguments[param] not in allowed_values:
                    return (
                        f"Invalid value for {param}: {arguments[param]}. "
                        f"Allowed: {allowed_values}"
                    )
        
        return None
    
    async def _load_config(self) -> PolicyConfig:
        """Load policy configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            return self._parse_config(data)
        except FileNotFoundError:
            logger.warning(f"Policy file not found: {self.config_path}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load policy: {e}")
            if self.config.settings.get("fail_on_policy_error", True):
                raise
            return self._get_default_config()
    
    def _parse_config(self, data: Dict) -> PolicyConfig:
        """Parse YAML data into PolicyConfig."""
        profiles = {}
        for name, profile_data in data.get("profiles", {}).items():
            profiles[name] = Profile(
                name=name,
                description=profile_data.get("description", ""),
                allowed_tools=set(profile_data.get("allow", [])),
                extends=profile_data.get("extends"),
                restrictions=profile_data.get("restrictions", {})
            )
        
        tool_restrictions = {}
        for tool_name, restriction_data in data.get("tool_restrictions", {}).items():
            tool_restrictions[tool_name] = ToolRestriction(
                tool_name=tool_name,
                max_calls_per_hour=restriction_data.get("max_calls_per_hour"),
                require_confirmation=restriction_data.get("require_confirmation", False),
                allowed_values=restriction_data.get("allowed_values", {})
            )
        
        return PolicyConfig(
            active_profile=data.get("profile", "readonly"),
            profiles=profiles,
            tool_restrictions=tool_restrictions,
            settings=data.get("settings", {})
        )
    
    def _validate_config(self):
        """Validate policy configuration."""
        # Check active profile exists
        if self.config.active_profile not in self.config.profiles:
            raise ValueError(
                f"Active profile '{self.config.active_profile}' not defined"
            )
        
        # Check profile inheritance is valid
        for profile in self.config.profiles.values():
            if profile.extends:
                extends_list = (
                    profile.extends if isinstance(profile.extends, list)
                    else [profile.extends]
                )
                for parent in extends_list:
                    if parent not in self.config.profiles:
                        raise ValueError(
                            f"Profile '{profile.name}' extends unknown profile '{parent}'"
                        )
    
    def _resolve_inheritance(self):
        """Resolve profile inheritance."""
        for profile in self.config.profiles.values():
            if profile.extends:
                self._resolve_profile_inheritance(profile)
    
    def _resolve_profile_inheritance(self, profile: Profile):
        """Recursively resolve inheritance for a profile."""
        if not profile.extends:
            return
        
        extends_list = (
            profile.extends if isinstance(profile.extends, list)
            else [profile.extends]
        )
        
        for parent_name in extends_list:
            parent = self.config.profiles[parent_name]
            
            # Recursively resolve parent
            self._resolve_profile_inheritance(parent)
            
            # Inherit allowed tools
            if "*readonly" in profile.allowed_tools:
                # Special case: inherit all readonly tools
                profile.allowed_tools.remove("*readonly")
                readonly_profile = self.config.profiles.get("readonly")
                if readonly_profile:
                    profile.allowed_tools.update(readonly_profile.allowed_tools)
            else:
                profile.allowed_tools.update(parent.allowed_tools)
    
    def _get_default_config(self) -> PolicyConfig:
        """Get default policy configuration (readonly profile only)."""
        return PolicyConfig(
            active_profile="readonly",
            profiles={
                "readonly": Profile(
                    name="readonly",
                    description="Default read-only profile",
                    allowed_tools=set(READ_ONLY_TOOLS)
                )
            },
            tool_restrictions={},
            settings={"deny_unknown_tools": True}
        )
```

### 4.3 Usage Tracker (Rate Limiting)

```python
class UsageTracker:
    """
    Track tool usage for rate limiting.
    
    Uses sliding window algorithm for rate limiting.
    """
    
    def __init__(self):
        self._usage: Dict[str, List[datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(
        self,
        tool_name: str,
        max_calls_per_hour: int
    ) -> bool:
        """
        Check if tool call is within rate limit.
        
        Args:
            tool_name: Name of the tool
            max_calls_per_hour: Maximum calls allowed per hour
            
        Returns:
            True if within limit, False if exceeded
        """
        async with self._lock:
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            
            # Get recent calls
            if tool_name not in self._usage:
                self._usage[tool_name] = []
            
            # Remove old entries
            self._usage[tool_name] = [
                ts for ts in self._usage[tool_name]
                if ts > one_hour_ago
            ]
            
            # Check limit
            if len(self._usage[tool_name]) >= max_calls_per_hour:
                return False
            
            # Record this call
            self._usage[tool_name].append(now)
            return True
    
    async def get_usage_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get usage statistics for a tool."""
        async with self._lock:
            if tool_name not in self._usage:
                return {"calls_last_hour": 0}
            
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            
            recent_calls = [
                ts for ts in self._usage[tool_name]
                if ts > one_hour_ago
            ]
            
            return {
                "calls_last_hour": len(recent_calls),
                "last_call": max(recent_calls) if recent_calls else None
            }
```

## 5. Policy Enforcement Points

### 5.1 Startup Enforcement

```python
async def startup_validation():
    """Validate policy at startup."""
    policy_engine = PolicyEngine("config/tools.yaml")
    
    try:
        await policy_engine.initialize()
        logger.info("✓ Policy configuration valid")
    except Exception as e:
        logger.error(f"✗ Policy configuration invalid: {e}")
        sys.exit(1)
```

### 5.2 Tool Registration Enforcement

```python
async def register_tools(
    tool_registry: ToolRegistry,
    policy_engine: PolicyEngine
):
    """Register only allowed tools."""
    all_tools = await gcm_client.list_tools()
    active_profile = policy_engine.config.active_profile
    
    for tool in all_tools:
        if policy_engine.is_tool_allowed(tool.name, active_profile):
            tool_registry.register(tool)
            logger.debug(f"✓ Registered tool: {tool.name}")
        else:
            logger.debug(f"✗ Skipped tool: {tool.name} (not in profile)")
```

### 5.3 Execution Enforcement

```python
async def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    policy_engine: PolicyEngine
):
    """Execute tool with policy enforcement."""
    # Check tool is allowed
    if not policy_engine.is_tool_allowed(tool_name):
        raise ToolNotAllowedError(
            f"Tool '{tool_name}' not allowed for profile "
            f"'{policy_engine.config.active_profile}'"
        )
    
    # Check tool-specific restrictions
    restriction_error = await policy_engine.check_restrictions(
        tool_name,
        arguments
    )
    if restriction_error:
        raise RestrictionViolationError(restriction_error)
    
    # Execute tool
    result = await gcm_client.call_tool(tool_name, arguments)
    return result
```

## 6. Error Handling

### 6.1 Policy Errors

```python
class PolicyError(Exception):
    """Base class for policy-related errors."""
    pass

class PolicyLoadError(PolicyError):
    """Failed to load policy configuration."""
    pass

class PolicyValidationError(PolicyError):
    """Policy configuration is invalid."""
    pass

class ToolNotAllowedError(PolicyError):
    """Tool not allowed for current profile."""
    pass

class RestrictionViolationError(PolicyError):
    """Tool-specific restriction violated."""
    pass

class RateLimitExceededError(PolicyError):
    """Rate limit exceeded for tool."""
    pass
```

### 6.2 Error Responses

```json
{
  "error": {
    "code": "TOOL_NOT_ALLOWED",
    "message": "Tool 'create_policy' is not allowed for profile 'readonly'",
    "details": {
      "tool": "create_policy",
      "profile": "readonly",
      "allowed_tools": ["search_policies", "fetch_policy_by_id", ...],
      "required_profiles": ["admin"]
    }
  }
}
```

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded for tool 'create_policy'",
    "details": {
      "tool": "create_policy",
      "limit": 10,
      "period": "1 hour",
      "calls_made": 10,
      "retry_after": "2026-03-27T09:00:00Z"
    }
  }
}
```

## 7. Configuration Management

### 7.1 Environment Variable Override

```bash
# Override active profile
export GCM_RELAY_PROFILE=ops

# Override policy file location
export GCM_RELAY_POLICY_FILE=/etc/gcm-relay/custom-policy.yaml
```

### 7.2 Runtime Profile Switching (Phase 2)

```python
class PolicyEngine:
    async def switch_profile(self, new_profile: str):
        """Switch to a different profile at runtime."""
        if new_profile not in self.config.profiles:
            raise ValueError(f"Unknown profile: {new_profile}")
        
        old_profile = self.config.active_profile
        self.config.active_profile = new_profile
        
        logger.info(f"Switched profile: {old_profile} → {new_profile}")
        
        # Emit event for tool registry to update
        await self._emit_profile_changed_event(new_profile)
```

### 7.3 Hot Reload (Phase 2)

```python
class PolicyEngine:
    async def reload_config(self):
        """Reload policy configuration from file."""
        logger.info("Reloading policy configuration...")
        
        try:
            new_config = await self._load_config()
            self._validate_config()
            self._resolve_inheritance()
            
            self.config = new_config
            logger.info("✓ Policy configuration reloaded")
            
            # Emit event for tool registry to update
            await self._emit_config_reloaded_event()
        except Exception as e:
            logger.error(f"✗ Failed to reload policy: {e}")
            # Keep existing configuration
```

## 8. Testing Strategy

### 8.1 Unit Tests

```python
class TestPolicyEngine:
    def test_load_valid_config(self):
        """Test loading valid policy configuration."""
        engine = PolicyEngine("tests/fixtures/valid-policy.yaml")
        await engine.initialize()
        assert engine.config.active_profile == "readonly"
    
    def test_profile_inheritance(self):
        """Test profile inheritance resolution."""
        engine = PolicyEngine("tests/fixtures/inheritance-policy.yaml")
        await engine.initialize()
        
        ops_profile = engine.config.profiles["ops"]
        assert "search_policies" in ops_profile.allowed_tools  # From readonly
        assert "create_violation_ticket" in ops_profile.allowed_tools  # Own
    
    def test_tool_allowed_check(self):
        """Test tool allowlist checking."""
        engine = PolicyEngine("tests/fixtures/policy.yaml")
        await engine.initialize()
        
        assert engine.is_tool_allowed("search_policies", "readonly")
        assert not engine.is_tool_allowed("create_policy", "readonly")
        assert engine.is_tool_allowed("create_policy", "admin")
    
    def test_rate_limiting(self):
        """Test rate limiting enforcement."""
        tracker = UsageTracker()
        
        # Should allow first 10 calls
        for i in range(10):
            assert await tracker.check_rate_limit("test_tool", 10)
        
        # Should deny 11th call
        assert not await tracker.check_rate_limit("test_tool", 10)
```

### 8.2 Integration Tests

```python
class TestPolicyEnforcement:
    async def test_execute_allowed_tool(self):
        """Test executing allowed tool succeeds."""
        result = await execute_tool(
            "search_policies",
            {"query": "TLS"},
            policy_engine
        )
        assert result is not None
    
    async def test_execute_disallowed_tool(self):
        """Test executing disallowed tool fails."""
        with pytest.raises(ToolNotAllowedError):
            await execute_tool(
                "create_policy",
                {},
                policy_engine
            )
    
    async def test_rate_limit_enforcement(self):
        """Test rate limiting is enforced."""
        # Configure tool with rate limit
        policy_engine.config.tool_restrictions["test_tool"] = ToolRestriction(
            tool_name="test_tool",
            max_calls_per_hour=5
        )
        
        # Should allow first 5 calls
        for i in range(5):
            await execute_tool("test_tool", {}, policy_engine)
        
        # Should deny 6th call
        with pytest.raises(RateLimitExceededError):
            await execute_tool("test_tool", {}, policy_engine)
```

## 9. Security Considerations

### 9.1 Policy File Security

**DO**:
- Store policy files in secure location
- Set restrictive file permissions (644 or 600)
- Version control policy files
- Review policy changes carefully
- Use separate policies per environment

**DON'T**:
- Allow world-writable policy files
- Store policies in web-accessible directories
- Use overly permissive default profiles
- Skip policy validation

### 9.2 Profile Security

**DO**:
- Use least-privilege principle
- Default to most restrictive profile (readonly)
- Require explicit configuration for admin access
- Audit profile usage
- Rotate admin credentials regularly

**DON'T**:
- Use admin profile by default
- Share admin profiles across users
- Allow profile switching without authentication
- Skip audit logging for admin actions

## 10. Monitoring and Auditing

### 10.1 Policy Metrics

```python
class PolicyMetrics:
    """Track policy enforcement metrics."""
    
    def __init__(self):
        self.allowed_calls = 0
        self.denied_calls = 0
        self.rate_limited_calls = 0
        self.by_tool: Dict[str, int] = {}
        self.by_profile: Dict[str, int] = {}
    
    def record_allowed(self, tool: str, profile: str):
        """Record allowed tool call."""
        self.allowed_calls += 1
        self.by_tool[tool] = self.by_tool.get(tool, 0) + 1
        self.by_profile[profile] = self.by_profile.get(profile, 0) + 1
    
    def record_denied(self, tool: str, profile: str, reason: str):
        """Record denied tool call."""
        self.denied_calls += 1
        # Log for security audit
        logger.warning(
            f"Tool call denied: tool={tool}, profile={profile}, reason={reason}"
        )
```

### 10.2 Audit Events

```json
{
  "timestamp": "2026-03-27T08:00:00Z",
  "event": "policy_violation",
  "tool": "create_policy",
  "profile": "readonly",
  "user": "ai-agent-001",
  "reason": "tool_not_allowed",
  "details": {
    "required_profile": "admin",
    "attempted_arguments": {"name": "new-policy"}
  }
}
```

## 11. References

- [Architecture Design](architecture.md)
- [Tool Abstraction Design](tool-abstraction-design.md)
- [Configuration Guide](configuration.md)
- [Security Considerations](security.md)