# This file includes AI-generated code - Review and modify as needed
"""
Policy configuration models.

Defines the structure for tool access control policies.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ToolPolicy(BaseModel):
    """Policy for a single tool."""

    enabled: bool = Field(
        default=True,
        description="Whether tool is enabled",
    )
    risk_level: Literal["safe", "moderate", "high"] = Field(
        default="safe",
        description="Risk level of tool",
    )
    category: Literal["readonly", "state-changing"] = Field(
        default="readonly",
        description="Tool category",
    )
    rate_limit: Optional[int] = Field(
        default=None,
        description="Max calls per minute (Phase 2)",
    )
    description: Optional[str] = Field(
        default=None,
        description="Tool description override",
    )


class ProfilePolicy(BaseModel):
    """Access control profile."""

    description: str = Field(
        description="Profile description",
    )
    allow: list[str] = Field(
        default_factory=list,
        description="Allowed tool names (supports wildcards)",
    )
    deny: list[str] = Field(
        default_factory=list,
        description="Denied tool names (takes precedence over allow)",
    )


class PolicyConfig(BaseModel):
    """Root policy configuration."""

    profile: str = Field(
        default="readonly",
        description="Active profile name",
    )
    profiles: dict[str, ProfilePolicy] = Field(
        default_factory=dict,
        description="Available profiles",
    )
    tools: dict[str, ToolPolicy] = Field(
        default_factory=dict,
        description="Per-tool policies",
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"

# Made with Bob
