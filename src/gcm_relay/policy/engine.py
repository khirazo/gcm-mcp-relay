# This file includes AI-generated code - Review and modify as needed
"""
Policy engine for enforcing tool access control.

Implements defense-in-depth with three enforcement points:
1. Startup validation
2. Tool registration filtering
3. Execution-time validation
"""

import logging
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from gcm_relay.exceptions import PolicyError, ToolNotAllowedError
from gcm_relay.policy.models import PolicyConfig, ProfilePolicy, ToolPolicy

logger = logging.getLogger(__name__)


# Hardcoded tool classification (from design)
READONLY_TOOLS = {
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
    "create_policy",
    "create_violation_ticket",
    "renew_ca_signed_certificate",
    "renew_self_signed_certificate",
}


class PolicyEngine:
    """
    Policy engine for tool access control.

    Enforces profile-based access control with wildcard support.
    """

    def __init__(self, policy_config: PolicyConfig):
        """
        Initialize policy engine.

        Args:
            policy_config: Policy configuration
        """
        self.config = policy_config
        self._validate_config()

    def _validate_config(self) -> None:
        """
        Validate policy configuration at startup.

        Raises:
            PolicyError: If configuration is invalid
        """
        # Check active profile exists
        if self.config.profile not in self.config.profiles:
            raise PolicyError(
                f"Active profile '{self.config.profile}' not found in configuration",
                details={"profile": self.config.profile},
            )

        logger.info(f"Policy engine initialized with profile: {self.config.profile}")

    @classmethod
    def from_file(cls, policy_file: Path) -> "PolicyEngine":
        """
        Load policy from YAML file.

        Args:
            policy_file: Path to policy YAML file

        Returns:
            Initialized policy engine

        Raises:
            PolicyError: If file not found or invalid
        """
        if not policy_file.exists():
            raise PolicyError(
                f"Policy file not found: {policy_file}",
                details={"path": str(policy_file)},
            )

        try:
            with open(policy_file, "r") as f:
                data = yaml.safe_load(f)

            config = PolicyConfig(**data)
            return cls(config)

        except yaml.YAMLError as e:
            raise PolicyError(
                f"Invalid YAML in policy file: {e}",
                details={"path": str(policy_file), "error": str(e)},
            )
        except Exception as e:
            raise PolicyError(
                f"Failed to load policy file: {e}",
                details={"path": str(policy_file), "error": str(e)},
            )

    def _expand_wildcards(self, patterns: list[str]) -> set[str]:
        """
        Expand wildcard patterns to tool names.

        Supports:
        - "*" - all tools
        - "*readonly" - all readonly tools
        - "*state-changing" - all state-changing tools

        Args:
            patterns: List of patterns (may include wildcards)

        Returns:
            Set of expanded tool names
        """
        expanded = set()

        for pattern in patterns:
            if pattern == "*":
                # All tools
                expanded.update(READONLY_TOOLS)
                expanded.update(STATE_CHANGING_TOOLS)
            elif pattern == "*readonly":
                # All readonly tools
                expanded.update(READONLY_TOOLS)
            elif pattern == "*state-changing":
                # All state-changing tools
                expanded.update(STATE_CHANGING_TOOLS)
            elif "*" in pattern:
                # Regex wildcard
                regex = re.compile(pattern.replace("*", ".*"))
                all_tools = READONLY_TOOLS | STATE_CHANGING_TOOLS
                expanded.update(tool for tool in all_tools if regex.match(tool))
            else:
                # Literal tool name
                expanded.add(pattern)

        return expanded

    def get_active_profile(self) -> ProfilePolicy:
        """
        Get active profile configuration.

        Returns:
            Active profile policy
        """
        return self.config.profiles[self.config.profile]

    def get_allowed_tools(self) -> set[str]:
        """
        Get set of allowed tool names for active profile.

        Returns:
            Set of allowed tool names
        """
        profile = self.get_active_profile()

        # Expand allow patterns
        allowed = self._expand_wildcards(profile.allow)

        # Remove denied tools
        denied = self._expand_wildcards(profile.deny)
        allowed -= denied

        return allowed

    def is_tool_allowed(self, tool_name: str) -> bool:
        """
        Check if tool is allowed by current policy.

        Args:
            tool_name: Name of tool to check

        Returns:
            True if tool is allowed, False otherwise
        """
        allowed_tools = self.get_allowed_tools()
        return tool_name in allowed_tools

    def validate_tool_call(self, tool_name: str) -> None:
        """
        Validate tool call against policy (execution-time enforcement).

        Args:
            tool_name: Name of tool being called

        Raises:
            ToolNotAllowedError: If tool is not allowed
        """
        if not self.is_tool_allowed(tool_name):
            raise ToolNotAllowedError(tool_name, self.config.profile)

    def get_tool_policy(self, tool_name: str) -> Optional[ToolPolicy]:
        """
        Get policy for specific tool.

        Args:
            tool_name: Name of tool

        Returns:
            Tool policy if configured, None otherwise
        """
        return self.config.tools.get(tool_name)

    def get_tool_metadata(self, tool_name: str) -> dict[str, Any]:
        """
        Get metadata for tool (category, risk level, etc.).

        Args:
            tool_name: Name of tool

        Returns:
            Tool metadata dictionary
        """
        # Determine category and risk level
        if tool_name in READONLY_TOOLS:
            category = "readonly"
            risk_level = "safe"
        elif tool_name in STATE_CHANGING_TOOLS:
            category = "state-changing"
            risk_level = "high"
        else:
            category = "unknown"
            risk_level = "moderate"

        # Check for policy overrides
        tool_policy = self.get_tool_policy(tool_name)
        if tool_policy:
            category = tool_policy.category
            risk_level = tool_policy.risk_level

        return {
            "category": category,
            "risk_level": risk_level,
            "is_read_only": category == "readonly",
        }

    def filter_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Filter tool list based on policy (registration-time enforcement).

        Args:
            tools: List of tool definitions from GCM

        Returns:
            Filtered list of allowed tools
        """
        allowed_tools = self.get_allowed_tools()
        filtered = []

        for tool in tools:
            # Handle both dict and object (e.g., LangChain StructuredTool)
            if isinstance(tool, dict):
                tool_name = tool.get("name")
            else:
                # Assume it's an object with .name attribute (e.g., StructuredTool)
                tool_name = getattr(tool, "name", None)
            
            if tool_name and tool_name in allowed_tools:
                # Keep the tool as-is (dict or object)
                # Note: We don't add metadata to objects to avoid modifying them
                filtered.append(tool)

        logger.info(
            f"Filtered {len(tools)} tools to {len(filtered)} allowed tools "
            f"(profile: {self.config.profile})"
        )
        return filtered

# Made with Bob
