# GCM MCP Relay - Tool Abstraction Layer Design

## 1. Overview

The Tool Abstraction Layer manages the exposure of GCM's 26 built-in MCP tools to AI agents. It implements a selective exposure strategy where safe read-only tools are directly exposed, while dangerous state-changing tools are restricted or hidden.

## 2. Design Principles

### 2.1 Selective Exposure
- **Read-only tools**: Directly exposed with minimal transformation
- **State-changing tools**: Restricted by default, require explicit configuration
- **Tool metadata**: Enhanced with safety information

### 2.2 Configuration-Driven
- Tool allowlists defined in YAML configuration
- Profile-based access control (readonly/ops/admin)
- No code changes required to modify tool exposure

### 2.3 Transparency
- Tool names preserved (no renaming in Phase 1)
- Original schemas maintained
- Clear documentation of restrictions

## 3. GCM Tool Classification

### 3.1 Read-Only Tools (22 tools)

These tools only query data and cannot modify GCM state:

| Tool Name | Category | Description |
|-----------|----------|-------------|
| [`search_policies`](gcm://tools/search_policies) | Policy | Search for policies |
| [`fetch_policy_by_id`](gcm://tools/fetch_policy_by_id) | Policy | Get policy details |
| [`get_violation_by_id`](gcm://tools/get_violation_by_id) | Violation | Get violation details |
| [`fetch_policy_violations_ticket`](gcm://tools/fetch_policy_violations_ticket) | Violation | List violation tickets |
| [`policy_violations_dashboard`](gcm://tools/policy_violations_dashboard) | Violation | Get violations dashboard |
| [`get_filters_by_it_assets`](gcm://tools/get_filters_by_it_assets) | Asset | Get IT asset filters |
| [`fetch_detailed_asset_list_by_it_assets`](gcm://tools/fetch_detailed_asset_list_by_it_assets) | Asset | List IT assets |
| [`fetch_individual_asset_detail_by_it_assets`](gcm://tools/fetch_individual_asset_detail_by_it_assets) | Asset | Get IT asset details |
| [`get_category_metadata_by_it_assets`](gcm://tools/get_category_metadata_by_it_assets) | Asset | Get IT asset metadata |
| [`get_filters_by_crypto_objects`](gcm://tools/get_filters_by_crypto_objects) | Crypto | Get crypto object filters |
| [`fetch_detailed_asset_list_by_crypto_objects`](gcm://tools/fetch_detailed_asset_list_by_crypto_objects) | Crypto | List crypto objects |
| [`fetch_individual_asset_detail_by_crypto_objects`](gcm://tools/fetch_individual_asset_detail_by_crypto_objects) | Crypto | Get crypto object details |
| [`get_category_metadata_by_crypto_objects`](gcm://tools/get_category_metadata_by_crypto_objects) | Crypto | Get crypto object metadata |
| [`get_asset_groups`](gcm://tools/get_asset_groups) | Asset | List asset groups |
| [`fetch_asset_metadata`](gcm://tools/fetch_asset_metadata) | Asset | Get asset metadata |
| [`fetch_bulk_vulnerable_crypto_objects`](gcm://tools/fetch_bulk_vulnerable_crypto_objects) | Crypto | List vulnerable crypto objects |
| [`get_vulnerable_crypto_objects_count`](gcm://tools/get_vulnerable_crypto_objects_count) | Crypto | Count vulnerable crypto objects |
| [`get_all_intergration`](gcm://tools/get_all_intergration) | Integration | List integrations |
| [`get_certificate_permissions`](gcm://tools/get_certificate_permissions) | Certificate | Get certificate permissions |
| [`get_vault_details`](gcm://tools/get_vault_details) | Certificate | Get vault details |
| [`get_certificate_details`](gcm://tools/get_certificate_details) | Certificate | Get certificate details |
| [`get_user_details_by_username`](gcm://tools/get_user_details_by_username) | User | Get user details |

### 3.2 State-Changing Tools (4 tools)

These tools modify GCM state and require careful access control:

| Tool Name | Risk Level | Default Profile | Description |
|-----------|------------|-----------------|-------------|
| [`create_policy`](gcm://tools/create_policy) | HIGH | admin only | Create new policy |
| [`create_violation_ticket`](gcm://tools/create_violation_ticket) | MODERATE | ops, admin | Create violation ticket |
| [`renew_ca_signed_certificate`](gcm://tools/renew_ca_signed_certificate) | HIGH | admin only | Renew CA-signed certificate |
| [`renew_self_signed_certificate`](gcm://tools/renew_self_signed_certificate) | HIGH | admin only | Renew self-signed certificate |

## 4. Tool Registry Design

### 4.1 Tool Metadata Structure

```python
@dataclass
class ToolMetadata:
    """Metadata for a GCM MCP tool."""
    
    name: str                    # Tool name (e.g., "search_policies")
    description: str             # Tool description
    category: str                # Category (policy, asset, crypto, etc.)
    risk_level: str              # safe, moderate, high
    is_read_only: bool           # True if read-only
    input_schema: Dict[str, Any] # JSON schema for inputs
    output_schema: Dict[str, Any] # JSON schema for outputs (optional)
    
    # Access control
    default_profiles: List[str]  # Profiles that include this tool by default
    requires_approval: bool      # Whether tool requires manual approval
    
    # Documentation
    examples: List[Dict[str, Any]]  # Usage examples
    notes: Optional[str]            # Additional notes
```

### 4.2 Tool Registry Implementation

```python
class ToolRegistry:
    """
    Registry of available GCM MCP tools.
    
    Manages tool discovery, metadata, and filtering based on policy.
    """
    
    def __init__(self, gcm_client: GCMClient, policy_engine: PolicyEngine):
        self.gcm_client = gcm_client
        self.policy_engine = policy_engine
        self._tools: Dict[str, ToolMetadata] = {}
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize tool registry by discovering tools from GCM.
        
        1. Call GCM MCP server's list_tools
        2. Enhance with local metadata
        3. Filter based on policy
        """
        if self._initialized:
            return
        
        # Discover tools from GCM
        gcm_tools = await self.gcm_client.list_tools()
        
        # Enhance with metadata
        for tool in gcm_tools:
            metadata = self._create_metadata(tool)
            self._tools[tool.name] = metadata
        
        self._initialized = True
    
    def _create_metadata(self, gcm_tool: MCPTool) -> ToolMetadata:
        """Create enhanced metadata for a GCM tool."""
        # Classify tool
        is_read_only = gcm_tool.name in READ_ONLY_TOOLS
        risk_level = self._assess_risk_level(gcm_tool.name)
        category = self._categorize_tool(gcm_tool.name)
        
        return ToolMetadata(
            name=gcm_tool.name,
            description=gcm_tool.description,
            category=category,
            risk_level=risk_level,
            is_read_only=is_read_only,
            input_schema=gcm_tool.inputSchema,
            output_schema={},
            default_profiles=self._get_default_profiles(gcm_tool.name),
            requires_approval=risk_level == "high",
            examples=[],
            notes=None
        )
    
    def get_allowed_tools(self, profile: str) -> List[ToolMetadata]:
        """Get list of tools allowed for the given profile."""
        allowed_names = self.policy_engine.get_allowed_tools(profile)
        return [
            self._tools[name]
            for name in allowed_names
            if name in self._tools
        ]
    
    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """Get metadata for a specific tool."""
        return self._tools.get(name)
    
    def is_tool_allowed(self, name: str, profile: str) -> bool:
        """Check if a tool is allowed for the given profile."""
        return self.policy_engine.is_tool_allowed(name, profile)
```

### 4.3 Tool Classification Logic

```python
# Tool classification constants
READ_ONLY_TOOLS = {
    "search_policies",
    "fetch_policy_by_id",
    "get_violation_by_id",
    "fetch_policy_violations_ticket",
    "policy_violations_dashboard",
    "get_filters_by_it_assets",
    "fetch_detailed_asset_list_by_it_assets",
    "fetch_individual_asset_detail_by_it_assets",
    "get_category_metadata_by_it_assets",
    "get_filters_by_crypto_objects",
    "fetch_detailed_asset_list_by_crypto_objects",
    "fetch_individual_asset_detail_by_crypto_objects",
    "get_category_metadata_by_crypto_objects",
    "get_asset_groups",
    "fetch_asset_metadata",
    "fetch_bulk_vulnerable_crypto_objects",
    "get_vulnerable_crypto_objects_count",
    "get_all_intergration",
    "get_certificate_permissions",
    "get_vault_details",
    "get_certificate_details",
    "get_user_details_by_username",
}

STATE_CHANGING_TOOLS = {
    "create_policy": "high",
    "create_violation_ticket": "moderate",
    "renew_ca_signed_certificate": "high",
    "renew_self_signed_certificate": "high",
}

TOOL_CATEGORIES = {
    "policy": ["search_policies", "fetch_policy_by_id", "create_policy"],
    "violation": ["get_violation_by_id", "fetch_policy_violations_ticket", 
                  "policy_violations_dashboard", "create_violation_ticket"],
    "asset": ["get_filters_by_it_assets", "fetch_detailed_asset_list_by_it_assets",
              "fetch_individual_asset_detail_by_it_assets", 
              "get_category_metadata_by_it_assets", "get_asset_groups",
              "fetch_asset_metadata"],
    "crypto": ["get_filters_by_crypto_objects", 
               "fetch_detailed_asset_list_by_crypto_objects",
               "fetch_individual_asset_detail_by_crypto_objects",
               "get_category_metadata_by_crypto_objects",
               "fetch_bulk_vulnerable_crypto_objects",
               "get_vulnerable_crypto_objects_count"],
    "certificate": ["get_certificate_permissions", "get_vault_details",
                    "get_certificate_details", "renew_ca_signed_certificate",
                    "renew_self_signed_certificate"],
    "integration": ["get_all_intergration"],
    "user": ["get_user_details_by_username"],
}

def _assess_risk_level(tool_name: str) -> str:
    """Assess risk level of a tool."""
    if tool_name in STATE_CHANGING_TOOLS:
        return STATE_CHANGING_TOOLS[tool_name]
    return "safe"

def _categorize_tool(tool_name: str) -> str:
    """Categorize a tool."""
    for category, tools in TOOL_CATEGORIES.items():
        if tool_name in tools:
            return category
    return "other"

def _get_default_profiles(tool_name: str) -> List[str]:
    """Get default profiles that include this tool."""
    if tool_name in READ_ONLY_TOOLS:
        return ["readonly", "ops", "admin"]
    elif tool_name == "create_violation_ticket":
        return ["ops", "admin"]
    else:
        return ["admin"]
```

## 5. Tool Execution Flow

### 5.1 Execution Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ 1. MCP Server receives call_tool request                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Tool Executor: Validate tool exists                       │
│    - Check tool is in registry                               │
│    - Return error if not found                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Policy Engine: Check tool is allowed                      │
│    - Check against profile allowlist                         │
│    - Return error if not allowed                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Tool Validator: Validate arguments                        │
│    - Check against input schema                              │
│    - Sanitize inputs                                         │
│    - Return error if invalid                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Audit Logger: Log invocation (pre-execution)              │
│    - Tool name, arguments, timestamp                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. GCM Client: Call GCM MCP server                           │
│    - Forward tool call with Bearer token                     │
│    - Handle errors and timeouts                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Audit Logger: Log result (post-execution)                 │
│    - Success/failure, duration, response size                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Return result to MCP client                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Tool Executor Implementation

```python
class ToolExecutor:
    """
    Executes tool calls with policy enforcement and audit logging.
    """
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        policy_engine: PolicyEngine,
        gcm_client: GCMClient,
        audit_logger: AuditLogger,
        profile: str
    ):
        self.tool_registry = tool_registry
        self.policy_engine = policy_engine
        self.gcm_client = gcm_client
        self.audit_logger = audit_logger
        self.profile = profile
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool call with full validation and logging.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            ToolNotFoundError: Tool does not exist
            ToolNotAllowedError: Tool not allowed for current profile
            ValidationError: Invalid arguments
            GCMError: Error from GCM MCP server
        """
        start_time = time.time()
        
        try:
            # 1. Validate tool exists
            tool_metadata = self.tool_registry.get_tool(tool_name)
            if not tool_metadata:
                raise ToolNotFoundError(f"Tool '{tool_name}' not found")
            
            # 2. Check tool is allowed
            if not self.policy_engine.is_tool_allowed(tool_name, self.profile):
                raise ToolNotAllowedError(
                    f"Tool '{tool_name}' not allowed for profile '{self.profile}'"
                )
            
            # 3. Validate arguments
            validated_args = self._validate_arguments(
                tool_metadata.input_schema,
                arguments
            )
            
            # 4. Log pre-execution
            await self.audit_logger.log_tool_invocation(
                tool_name=tool_name,
                arguments=validated_args,
                profile=self.profile,
                status="started"
            )
            
            # 5. Execute tool via GCM client
            result = await self.gcm_client.call_tool(tool_name, validated_args)
            
            # 6. Log post-execution
            duration_ms = (time.time() - start_time) * 1000
            await self.audit_logger.log_tool_invocation(
                tool_name=tool_name,
                arguments=validated_args,
                profile=self.profile,
                status="success",
                duration_ms=duration_ms,
                result_size=len(json.dumps(result))
            )
            
            return result
            
        except Exception as e:
            # Log failure
            duration_ms = (time.time() - start_time) * 1000
            await self.audit_logger.log_tool_invocation(
                tool_name=tool_name,
                arguments=arguments,
                profile=self.profile,
                status="failed",
                duration_ms=duration_ms,
                error=str(e)
            )
            raise
    
    def _validate_arguments(
        self,
        schema: Dict[str, Any],
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and sanitize tool arguments."""
        # Use jsonschema or pydantic for validation
        # Sanitize string inputs
        # Check for injection attempts
        return arguments
```

## 6. Tool Schema Enhancement

### 6.1 Enhanced Tool Description

Original GCM tool description:
```json
{
  "name": "search_policies",
  "description": "Search for policies",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"}
    }
  }
}
```

Enhanced relay tool description:
```json
{
  "name": "search_policies",
  "description": "Search for policies. This is a read-only operation that queries the GCM policy database.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query string"
      }
    },
    "required": ["query"]
  },
  "metadata": {
    "category": "policy",
    "risk_level": "safe",
    "is_read_only": true,
    "examples": [
      {
        "description": "Search for policies containing 'TLS'",
        "arguments": {"query": "TLS"}
      }
    ]
  }
}
```

### 6.2 Schema Transformation

```python
class SchemaEnhancer:
    """Enhance GCM tool schemas with additional metadata."""
    
    def enhance_tool_schema(
        self,
        gcm_tool: MCPTool,
        metadata: ToolMetadata
    ) -> MCPTool:
        """
        Enhance a GCM tool schema with relay metadata.
        
        Args:
            gcm_tool: Original GCM tool
            metadata: Enhanced metadata
            
        Returns:
            Enhanced tool schema
        """
        enhanced = copy.deepcopy(gcm_tool)
        
        # Enhance description
        enhanced.description = self._enhance_description(
            gcm_tool.description,
            metadata
        )
        
        # Add metadata section
        enhanced.inputSchema["metadata"] = {
            "category": metadata.category,
            "risk_level": metadata.risk_level,
            "is_read_only": metadata.is_read_only,
        }
        
        # Add examples if available
        if metadata.examples:
            enhanced.inputSchema["examples"] = metadata.examples
        
        return enhanced
    
    def _enhance_description(
        self,
        original: str,
        metadata: ToolMetadata
    ) -> str:
        """Enhance tool description with safety information."""
        enhanced = original
        
        if metadata.is_read_only:
            enhanced += " This is a read-only operation."
        else:
            enhanced += f" ⚠️ This operation modifies GCM state (risk: {metadata.risk_level})."
        
        if metadata.requires_approval:
            enhanced += " Manual approval may be required."
        
        return enhanced
```

## 7. Error Handling

### 7.1 Tool-Specific Errors

```python
class ToolNotFoundError(Exception):
    """Tool does not exist in registry."""
    pass

class ToolNotAllowedError(Exception):
    """Tool not allowed for current profile."""
    pass

class ValidationError(Exception):
    """Tool arguments failed validation."""
    pass

class GCMToolError(Exception):
    """Error from GCM MCP server."""
    pass
```

### 7.2 Error Response Format

```json
{
  "error": {
    "code": "TOOL_NOT_ALLOWED",
    "message": "Tool 'create_policy' is not allowed for profile 'readonly'",
    "details": {
      "tool": "create_policy",
      "profile": "readonly",
      "allowed_tools": ["search_policies", "fetch_policy_by_id", ...],
      "required_profile": "admin"
    }
  }
}
```

## 8. Testing Strategy

### 8.1 Unit Tests

```python
class TestToolRegistry:
    """Test tool registry functionality."""
    
    def test_classify_read_only_tools(self):
        """Test read-only tool classification."""
        assert _assess_risk_level("search_policies") == "safe"
        assert _assess_risk_level("fetch_policy_by_id") == "safe"
    
    def test_classify_state_changing_tools(self):
        """Test state-changing tool classification."""
        assert _assess_risk_level("create_policy") == "high"
        assert _assess_risk_level("create_violation_ticket") == "moderate"
    
    def test_tool_categorization(self):
        """Test tool categorization."""
        assert _categorize_tool("search_policies") == "policy"
        assert _categorize_tool("get_certificate_details") == "certificate"
```

### 8.2 Integration Tests

```python
class TestToolExecution:
    """Test tool execution with real GCM connection."""
    
    async def test_execute_allowed_tool(self):
        """Test executing an allowed tool."""
        executor = ToolExecutor(...)
        result = await executor.execute_tool(
            "search_policies",
            {"query": "TLS"}
        )
        assert result is not None
    
    async def test_execute_disallowed_tool(self):
        """Test executing a disallowed tool raises error."""
        executor = ToolExecutor(profile="readonly")
        with pytest.raises(ToolNotAllowedError):
            await executor.execute_tool("create_policy", {})
```

## 9. Phase 2 Enhancements

### 9.1 Tool Abstraction

Future enhancement: Create logical tools that combine multiple GCM tools:

```python
# Logical tool: crypto.list_expiring_certificates
# Maps to: fetch_detailed_asset_list_by_crypto_objects + filtering

class LogicalTool:
    """A logical tool that combines multiple GCM tools."""
    
    name: str
    description: str
    gcm_tools: List[str]  # GCM tools used
    
    async def execute(self, arguments: Dict) -> Dict:
        """Execute logical tool by calling multiple GCM tools."""
        pass
```

### 9.2 Tool Composition

```python
# Example: Get certificates expiring within N days
async def list_expiring_certificates(days: int) -> List[Dict]:
    """
    Logical tool that combines:
    1. fetch_detailed_asset_list_by_crypto_objects (certificates)
    2. Filter by expiry date
    3. Sort by expiry date
    """
    # Call GCM tool
    all_certs = await gcm_client.call_tool(
        "fetch_detailed_asset_list_by_crypto_objects",
        {"asset_type": "certificates"}
    )
    
    # Filter and sort
    expiring = [
        cert for cert in all_certs
        if cert["days_until_expiry"] <= days
    ]
    expiring.sort(key=lambda c: c["days_until_expiry"])
    
    return expiring
```

## 10. References

- [Architecture Design](architecture.md)
- [Policy Engine Design](policy-engine-design.md)
- [GCM MCP Server Manual](../work/Building_agents_for_IBM_Guardium_Cryptography_Manager_using_inbuilt_MCP_server.md)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)