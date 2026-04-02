#!/usr/bin/env python3
# This file includes AI-generated code - Review and modify as needed
"""
Configuration loader script for GCM MCP Relay.
Validates TOML configuration and exports to environment variables.
"""

import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore


def load_config(config_path: str) -> dict:
    """Load and validate TOML configuration."""
    try:
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        print(f"✓ Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        print(f"✗ Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Invalid TOML syntax: {e}", file=sys.stderr)
        sys.exit(1)


def validate_config(config: dict) -> None:
    """Validate required configuration sections."""
    required_sections = ['relay', 'gcm', 'policy', 'audit']
    for section in required_sections:
        if section not in config:
            print(f"✗ Missing required section: [{section}]", file=sys.stderr)
            sys.exit(1)
    print("✓ Configuration structure validated")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: config-loader.py <config.toml>", file=sys.stderr)
        sys.exit(1)
    
    config_path = sys.argv[1]
    config = load_config(config_path)
    validate_config(config)

# Made with Bob
