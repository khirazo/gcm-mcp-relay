# This file includes AI-generated code - Review and modify as needed
"""
Configuration loader with support for TOML files, environment variables, and CLI args.

Priority order (highest to lowest):
1. CLI arguments
2. Environment variables
3. TOML configuration file
4. Default values
"""

import os
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore

from pydantic_settings import BaseSettings, SettingsConfigDict

from gcm_relay.config.models import Config
from gcm_relay.exceptions import ConfigurationError, MissingCredentialsError


class EnvSettings(BaseSettings):
    """Environment variable settings with prefix."""

    model_config = SettingsConfigDict(
        env_prefix="GCM_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    # GCM connection
    host: Optional[str] = None
    api_port: Optional[int] = None
    oidc_port: Optional[int] = None
    oidc_host: Optional[str] = None
    oidc_realm: Optional[str] = None
    verify_ssl: Optional[bool] = None
    request_timeout: Optional[int] = None

    # Authentication
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    auth_mode: Optional[str] = None

    # Relay
    relay_profile: Optional[str] = None
    log_level: Optional[str] = None


def load_toml_config(config_path: Path) -> dict[str, Any]:
    """
    Load configuration from TOML file.

    Args:
        config_path: Path to TOML configuration file

    Returns:
        Configuration dictionary

    Raises:
        ConfigurationError: If file not found or invalid TOML
    """
    if not config_path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {config_path}",
            details={"path": str(config_path)},
        )

    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigurationError(
            f"Invalid TOML syntax in {config_path}: {e}",
            details={"path": str(config_path), "error": str(e)},
        )
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load configuration from {config_path}: {e}",
            details={"path": str(config_path), "error": str(e)},
        )


def merge_env_vars(config_dict: dict[str, Any], env_settings: EnvSettings) -> None:
    """
    Merge environment variables into configuration dictionary.

    Args:
        config_dict: Configuration dictionary to update
        env_settings: Environment variable settings
    """
    # GCM connection settings
    if env_settings.host:
        config_dict.setdefault("gcm", {})["host"] = env_settings.host
    if env_settings.api_port:
        config_dict.setdefault("gcm", {})["api_port"] = env_settings.api_port
    if env_settings.verify_ssl is not None:
        config_dict.setdefault("gcm", {})["verify_ssl"] = env_settings.verify_ssl
    if env_settings.request_timeout:
        config_dict.setdefault("gcm", {})["request_timeout"] = env_settings.request_timeout

    # OIDC settings
    if env_settings.oidc_host:
        config_dict.setdefault("gcm", {}).setdefault("oidc", {})["host"] = env_settings.oidc_host
    if env_settings.oidc_port:
        config_dict.setdefault("gcm", {}).setdefault("oidc", {})["port"] = env_settings.oidc_port
    if env_settings.oidc_realm:
        config_dict.setdefault("gcm", {}).setdefault("oidc", {})["realm"] = env_settings.oidc_realm

    # Authentication settings
    if env_settings.username:
        config_dict.setdefault("gcm", {}).setdefault("auth", {})["username"] = env_settings.username
    if env_settings.password:
        config_dict.setdefault("gcm", {}).setdefault("auth", {})["password"] = env_settings.password
    if env_settings.client_id:
        config_dict.setdefault("gcm", {}).setdefault("auth", {})["client_id"] = env_settings.client_id
    if env_settings.client_secret:
        config_dict.setdefault("gcm", {}).setdefault("auth", {})["client_secret"] = env_settings.client_secret
    if env_settings.auth_mode:
        config_dict.setdefault("gcm", {}).setdefault("auth", {})["auth_mode"] = env_settings.auth_mode

    # Relay settings
    if env_settings.relay_profile:
        config_dict.setdefault("relay", {})["profile"] = env_settings.relay_profile
    if env_settings.log_level:
        config_dict.setdefault("relay", {})["log_level"] = env_settings.log_level
        config_dict.setdefault("logging", {})["level"] = env_settings.log_level


def validate_credentials(config: Config) -> None:
    """
    Validate that required credentials are present.

    Args:
        config: Configuration object

    Raises:
        MissingCredentialsError: If required credentials are missing
    """
    missing = []

    if not config.gcm.auth.username:
        missing.append("GCM_USERNAME")
    if not config.gcm.auth.password:
        missing.append("GCM_PASSWORD")
    if not config.gcm.auth.client_secret:
        missing.append("GCM_CLIENT_SECRET")

    if missing:
        raise MissingCredentialsError(missing)


def load_config(
    config_path: Optional[Path] = None,
    validate: bool = True,
) -> Config:
    """
    Load configuration from all sources with proper priority.

    Priority order:
    1. CLI arguments (not implemented yet)
    2. Environment variables
    3. TOML configuration file
    4. Default values

    Args:
        config_path: Path to TOML configuration file (optional)
        validate: Whether to validate credentials

    Returns:
        Loaded and validated configuration

    Raises:
        ConfigurationError: If configuration is invalid
        MissingCredentialsError: If required credentials are missing
    """
    # Start with empty dict
    config_dict: dict[str, Any] = {}

    # Load from TOML file if provided
    if config_path:
        config_dict = load_toml_config(config_path)

    # Load environment variables
    env_settings = EnvSettings()

    # Merge environment variables (higher priority)
    merge_env_vars(config_dict, env_settings)

    # Create Config object (applies defaults)
    try:
        config = Config(**config_dict)
    except Exception as e:
        raise ConfigurationError(
            f"Invalid configuration: {e}",
            details={"error": str(e)},
        )

    # Validate credentials if requested
    if validate:
        validate_credentials(config)

    return config


def load_config_from_file(file_path: str) -> Config:
    """
    Convenience function to load config from a file path string.

    Args:
        file_path: Path to configuration file

    Returns:
        Loaded configuration
    """
    return load_config(config_path=Path(file_path))


def get_default_config_path() -> Optional[Path]:
    """
    Get default configuration file path.

    Searches in order:
    1. ./config/relay.toml
    2. /config/relay.toml (Docker)
    3. ~/.config/gcm-relay/relay.toml

    Returns:
        Path to config file if found, None otherwise
    """
    candidates = [
        Path("config/relay.toml"),
        Path("/config/relay.toml"),
        Path.home() / ".config" / "gcm-relay" / "relay.toml",
    ]

    for path in candidates:
        if path.exists():
            return path

    return None

# Made with Bob
