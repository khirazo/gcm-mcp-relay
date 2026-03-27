# GCM MCP Relay - Project Structure

## Directory Layout

```
gcm-mcp-relay/
├── README.md                      # Project overview and quick start
├── LICENSE                        # License file
├── requirements.txt               # Python dependencies
├── setup.py                       # Package installation script
├── pyproject.toml                 # Modern Python project configuration
├── .gitignore                     # Git ignore patterns
├── .env.example                   # Environment variable template
│
├── config/                        # Configuration files
│   ├── relay.example.toml         # Example relay configuration
│   ├── relay.toml                 # Active relay configuration (gitignored)
│   ├── tools.example.yaml         # Example tool policy configuration
│   └── tools.yaml                 # Active tool policy (gitignored)
│
├── docs/                          # Documentation
│   ├── architecture.md            # Architecture design (this document)
│   ├── project-structure.md       # Project structure overview
│   ├── configuration.md           # Configuration guide
│   ├── deployment.md              # Deployment guide
│   ├── security.md                # Security considerations
│   ├── api-reference.md           # API reference
│   └── development.md             # Development guide
│
├── src/                           # Source code
│   └── gcm_relay/                 # Main package
│       ├── __init__.py            # Package initialization
│       ├── __main__.py            # CLI entry point
│       ├── version.py             # Version information
│       │
│       ├── server/                # MCP server implementation
│       │   ├── __init__.py
│       │   ├── stdio.py           # stdio transport (Phase 1)
│       │   ├── http.py            # HTTP/SSE transport (Phase 2)
│       │   └── protocol.py        # MCP protocol handling
│       │
│       ├── tools/                 # Tool management
│       │   ├── __init__.py
│       │   ├── registry.py        # Tool registry and discovery
│       │   ├── executor.py        # Tool execution logic
│       │   ├── schema.py          # Tool schema definitions
│       │   └── validator.py       # Input validation
│       │
│       ├── policy/                # Policy engine
│       │   ├── __init__.py
│       │   ├── engine.py          # Policy enforcement logic
│       │   ├── loader.py          # Policy configuration loader
│       │   └── profiles.py        # Profile definitions
│       │
│       ├── auth/                  # Authentication management
│       │   ├── __init__.py
│       │   ├── manager.py         # Authentication manager
│       │   ├── token_cache.py     # Token caching logic
│       │   └── oidc.py            # OIDC/OAuth2 client (Phase 2)
│       │
│       ├── gcm/                   # GCM MCP client
│       │   ├── __init__.py
│       │   ├── client.py          # GCM MCP client implementation
│       │   ├── transport.py       # streamable-http transport
│       │   └── errors.py          # GCM-specific error handling
│       │
│       ├── audit/                 # Audit logging
│       │   ├── __init__.py
│       │   ├── logger.py          # Audit logger implementation
│       │   └── formatter.py       # Log formatting
│       │
│       ├── config/                # Configuration management
│       │   ├── __init__.py
│       │   ├── loader.py          # Configuration loader
│       │   ├── validator.py       # Configuration validation
│       │   └── models.py          # Configuration data models
│       │
│       └── utils/                 # Utility functions
│           ├── __init__.py
│           ├── logging.py         # Logging utilities
│           ├── errors.py          # Error definitions
│           └── helpers.py         # Helper functions
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration
│   │
│   ├── unit/                      # Unit tests
│   │   ├── test_policy_engine.py
│   │   ├── test_tool_registry.py
│   │   ├── test_auth_manager.py
│   │   ├── test_config_loader.py
│   │   └── test_validators.py
│   │
│   ├── integration/               # Integration tests
│   │   ├── test_gcm_client.py
│   │   ├── test_stdio_server.py
│   │   └── test_end_to_end.py
│   │
│   └── fixtures/                  # Test fixtures
│       ├── config/
│       │   ├── test_relay.toml
│       │   └── test_tools.yaml
│       └── mock_responses/
│           └── gcm_responses.json
│
├── scripts/                       # Utility scripts
│   ├── generate_api_key.py        # Generate API keys (Phase 2)
│   ├── validate_config.py         # Validate configuration files
│   └── test_gcm_connection.py     # Test GCM connectivity
│
├── logs/                          # Log files (gitignored)
│   ├── relay.log                  # Application logs
│   └── audit.jsonl                # Audit logs
│
└── work/                          # Working documents (reference only)
    ├── Building_agents_for_IBM_Guardium_Cryptography_Manager_using_inbuilt_MCP_server.md
    └── MCP_Relay_Design_Summary_for_GCM_MCP_Server.md
```

## Key Files and Their Purposes

### Root Level

#### [`README.md`](README.md)
- Project overview
- Quick start guide
- Installation instructions
- Basic usage examples

#### [`requirements.txt`](requirements.txt)
```txt
# MCP Protocol
mcp>=1.0.0

# HTTP Client (for GCM connection)
httpx>=0.27.0
httpx-sse>=0.4.0

# Configuration
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
tomli>=2.0.0; python_version < '3.11'
pyyaml>=6.0.0

# Logging
structlog>=24.0.0

# Testing (dev dependencies)
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# HTTP Server (Phase 2)
fastapi>=0.110.0
uvicorn>=0.27.0
```

#### [`setup.py`](setup.py) / [`pyproject.toml`](pyproject.toml)
- Package metadata
- Dependencies
- Entry points
- Build configuration

### Configuration Files

#### [`config/relay.example.toml`](config/relay.example.toml)
Template configuration file with all available options and documentation.

#### [`config/tools.example.yaml`](config/tools.example.yaml)
Template tool policy configuration with profile definitions.

### Source Code Structure

#### [`src/gcm_relay/__main__.py`](src/gcm_relay/__main__.py)
CLI entry point:
```python
"""
GCM MCP Relay - Command Line Interface

Usage:
    python -m gcm_relay --mode stdio
    python -m gcm_relay --mode http --host 0.0.0.0 --port 8002
"""
```

#### [`src/gcm_relay/server/stdio.py`](src/gcm_relay/server/stdio.py)
stdio transport implementation (Phase 1):
- JSON-RPC over stdin/stdout
- MCP protocol handling
- Tool invocation routing

#### [`src/gcm_relay/tools/registry.py`](src/gcm_relay/tools/registry.py)
Tool registry:
- Tool discovery from GCM
- Tool metadata management
- Tool filtering based on policy

#### [`src/gcm_relay/policy/engine.py`](src/gcm_relay/policy/engine.py)
Policy enforcement:
- Tool allowlist checking
- Profile-based access control
- Parameter validation

#### [`src/gcm_relay/auth/manager.py`](src/gcm_relay/auth/manager.py)
Authentication management:
- OAuth2/OIDC token acquisition
- Token caching and refresh
- Credential management

#### [`src/gcm_relay/gcm/client.py`](src/gcm_relay/gcm/client.py)
GCM MCP client:
- Connection to GCM built-in MCP server
- streamable-http transport
- Bearer JWT authentication

#### [`src/gcm_relay/audit/logger.py`](src/gcm_relay/audit/logger.py)
Audit logging:
- Structured logging
- Tool invocation tracking
- Security event logging

### Test Structure

#### [`tests/unit/`](tests/unit/)
Unit tests for individual components:
- Mock external dependencies
- Test business logic in isolation
- Fast execution

#### [`tests/integration/`](tests/integration/)
Integration tests:
- Test component interactions
- Test with real GCM connection (optional)
- End-to-end scenarios

#### [`tests/fixtures/`](tests/fixtures/)
Test data and configurations:
- Sample configuration files
- Mock GCM responses
- Test credentials

### Scripts

#### [`scripts/validate_config.py`](scripts/validate_config.py)
Configuration validation utility:
```bash
python scripts/validate_config.py config/relay.toml
```

#### [`scripts/test_gcm_connection.py`](scripts/test_gcm_connection.py)
GCM connectivity test:
```bash
python scripts/test_gcm_connection.py
```

## Module Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                         __main__.py                          │
│                      (CLI Entry Point)                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      server/stdio.py                         │
│                   (MCP Server Layer)                         │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    tools/executor.py                         │
│                   (Tool Execution)                           │
└──────┬──────────────────────┬──────────────────────┬────────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ policy/      │    │ auth/            │    │ audit/       │
│ engine.py    │    │ manager.py       │    │ logger.py    │
└──────┬───────┘    └────────┬─────────┘    └──────────────┘
       │                     │
       │                     ▼
       │            ┌──────────────────┐
       │            │ gcm/             │
       │            │ client.py        │
       │            └──────────────────┘
       │
       ▼
┌──────────────────┐
│ config/          │
│ loader.py        │
└──────────────────┘
```

## File Naming Conventions

### Python Files
- **Modules**: lowercase with underscores (`tool_registry.py`)
- **Classes**: PascalCase (`ToolRegistry`, `PolicyEngine`)
- **Functions**: lowercase with underscores (`load_config`, `validate_tool`)
- **Constants**: UPPERCASE with underscores (`DEFAULT_TIMEOUT`, `MAX_RETRIES`)

### Configuration Files
- **TOML**: lowercase with dots (`relay.toml`, `relay.example.toml`)
- **YAML**: lowercase with dots (`tools.yaml`, `tools.example.yaml`)
- **Environment**: uppercase with underscores (`.env`, `.env.example`)

### Documentation Files
- **Markdown**: lowercase with hyphens (`project-structure.md`, `api-reference.md`)

## Import Conventions

### Absolute Imports
Always use absolute imports from the package root:
```python
from gcm_relay.config import load_config
from gcm_relay.tools import ToolRegistry
from gcm_relay.policy import PolicyEngine
```

### Relative Imports
Avoid relative imports except within the same subpackage:
```python
# Within gcm_relay/tools/
from .registry import ToolRegistry  # OK
from .executor import ToolExecutor  # OK
```

## Code Organization Principles

### Single Responsibility
Each module should have a single, well-defined purpose:
- [`auth/manager.py`](auth/manager.py): Authentication only
- [`policy/engine.py`](policy/engine.py): Policy enforcement only
- [`audit/logger.py`](audit/logger.py): Audit logging only

### Dependency Injection
Use dependency injection for testability:
```python
class ToolExecutor:
    def __init__(
        self,
        gcm_client: GCMClient,
        policy_engine: PolicyEngine,
        audit_logger: AuditLogger
    ):
        self.gcm_client = gcm_client
        self.policy_engine = policy_engine
        self.audit_logger = audit_logger
```

### Configuration Over Code
Use configuration files for behavior changes:
- Tool allowlists in [`tools.yaml`](config/tools.yaml)
- Server settings in [`relay.toml`](config/relay.toml)
- No hardcoded policies in source code

## Development Workflow

### 1. Setup Development Environment
```bash
# Clone repository
git clone <repository-url>
cd gcm-mcp-relay

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .  # Install in editable mode
```

### 2. Configure for Development
```bash
# Copy example configurations
cp config/relay.example.toml config/relay.toml
cp config/tools.example.yaml config/tools.yaml
cp .env.example .env

# Edit configurations
# Set GCM connection details and credentials
```

### 3. Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gcm_relay --cov-report=html

# Run specific test file
pytest tests/unit/test_policy_engine.py

# Run with verbose output
pytest -v
```

### 4. Run Locally
```bash
# stdio mode
python -m gcm_relay --mode stdio

# With custom config
python -m gcm_relay --mode stdio --config config/relay.toml
```

### 5. Code Quality
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Phase 1 Implementation Priority

### Core Components (Must Have)
1. [`config/loader.py`](src/gcm_relay/config/loader.py) - Configuration loading
2. [`auth/manager.py`](src/gcm_relay/auth/manager.py) - Authentication
3. [`gcm/client.py`](src/gcm_relay/gcm/client.py) - GCM connection
4. [`policy/engine.py`](src/gcm_relay/policy/engine.py) - Policy enforcement
5. [`tools/registry.py`](src/gcm_relay/tools/registry.py) - Tool discovery
6. [`tools/executor.py`](src/gcm_relay/tools/executor.py) - Tool execution
7. [`server/stdio.py`](src/gcm_relay/server/stdio.py) - stdio server
8. [`__main__.py`](src/gcm_relay/__main__.py) - CLI entry point

### Supporting Components (Should Have)
9. [`audit/logger.py`](src/gcm_relay/audit/logger.py) - Audit logging
10. [`utils/logging.py`](src/gcm_relay/utils/logging.py) - Logging utilities
11. [`utils/errors.py`](src/gcm_relay/utils/errors.py) - Error definitions

### Documentation (Should Have)
12. [`README.md`](README.md) - Project overview
13. [`docs/configuration.md`](docs/configuration.md) - Configuration guide
14. [`docs/deployment.md`](docs/deployment.md) - Deployment guide

### Testing (Should Have)
15. Unit tests for core components
16. Integration test with GCM
17. End-to-end test

## Phase 2 Additions

### New Components
- [`server/http.py`](src/gcm_relay/server/http.py) - HTTP/SSE server
- [`auth/oidc.py`](src/gcm_relay/auth/oidc.py) - OIDC client
- [`scripts/generate_api_key.py`](scripts/generate_api_key.py) - API key management

### Enhanced Components
- [`policy/engine.py`](src/gcm_relay/policy/engine.py) - Rate limiting
- [`audit/logger.py`](src/gcm_relay/audit/logger.py) - Enhanced metrics
- [`config/models.py`](src/gcm_relay/config/models.py) - HTTP mode config

## References

- [Architecture Design](architecture.md)
- [Configuration Guide](configuration.md)
- [Development Guide](development.md)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)