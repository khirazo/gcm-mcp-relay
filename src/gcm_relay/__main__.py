# This file includes AI-generated code - Review and modify as needed
"""
Main entry point for GCM MCP Relay.

Usage:
    python -m gcm_relay [--config CONFIG_FILE]
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from gcm_relay.audit.logger import AuditLogger
from gcm_relay.auth.manager import AuthenticationManager
from gcm_relay.client.gcm_client import GCMClient
from gcm_relay.config import get_default_config_path, load_config
from gcm_relay.exceptions import RelayError
from gcm_relay.policy.engine import PolicyEngine
from gcm_relay.server.stdio_server import StdioMCPServer
from gcm_relay.tools.registry import ToolRegistry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main_async(config_path: Optional[Path] = None) -> int:
    """
    Main async entry point.

    Args:
        config_path: Path to configuration file

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Load configuration
        if config_path is None:
            config_path = get_default_config_path()

        if config_path:
            logger.info(f"Loading configuration from: {config_path}")
            config = load_config(config_path=config_path)
        else:
            logger.info("No configuration file found, using defaults")
            config = load_config()

        logger.info(f"Active profile: {config.relay.profile}")
        logger.info(f"Log level: {config.relay.log_level}")

        # Update log level
        logging.getLogger().setLevel(config.relay.log_level)

        # Load policy
        policy_path = Path(config.policy.config_file)
        if not policy_path.exists():
            logger.warning(f"Policy file not found: {policy_path}, using default policy")
            # Create minimal default policy
            from gcm_relay.policy.models import PolicyConfig, ProfilePolicy

            policy_config = PolicyConfig(
                profile="readonly",
                profiles={
                    "readonly": ProfilePolicy(
                        description="Read-only access",
                        allow=["*readonly"],
                        deny=[],
                    )
                },
            )
            policy_engine = PolicyEngine(policy_config)
        else:
            logger.info(f"Loading policy from: {policy_path}")
            policy_engine = PolicyEngine.from_file(policy_path)

        # Initialize components
        logger.info("Initializing components...")

        auth_manager = AuthenticationManager(config)
        gcm_client = GCMClient(config, auth_manager)
        tool_registry = ToolRegistry(gcm_client, policy_engine)
        audit_logger = AuditLogger(config.audit)

        # Create stdio server
        server = StdioMCPServer(
            config=config,
            auth_manager=auth_manager,
            gcm_client=gcm_client,
            policy_engine=policy_engine,
            tool_registry=tool_registry,
            audit_logger=audit_logger,
        )

        # Initialize server
        await server.initialize()

        # Log authentication event
        audit_logger.log_authentication_event(
            event_type="relay_start",
            user_id=config.gcm.auth.username,
            success=True,
            details={"profile": config.relay.profile},
        )

        logger.info("GCM MCP Relay started successfully")
        logger.info("Waiting for MCP requests on stdin...")

        # Run server
        await server.run()

        # Cleanup
        await auth_manager.close()
        await gcm_client.close()
        audit_logger.close()

        logger.info("GCM MCP Relay stopped")
        return 0

    except RelayError as e:
        logger.error(f"Relay error: {e.message}")
        logger.error(f"Details: {e.details}")
        return 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    # Parse command line arguments
    config_path: Optional[Path] = None

    if len(sys.argv) > 1:
        if sys.argv[1] in ("-h", "--help"):
            print("Usage: python -m gcm_relay [--config CONFIG_FILE]")
            print()
            print("Options:")
            print("  --config CONFIG_FILE  Path to configuration file")
            print("  -h, --help           Show this help message")
            return 0

        if sys.argv[1] == "--config" and len(sys.argv) > 2:
            config_path = Path(sys.argv[2])

    # Run async main
    return asyncio.run(main_async(config_path))


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
