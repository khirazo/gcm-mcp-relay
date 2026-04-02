# This file includes AI-generated code - Review and modify as needed
"""
Audit logger for recording tool invocations and security events.

Uses structured logging (JSONL format) for easy parsing and analysis.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog

from gcm_relay.config.models import AuditConfig
from gcm_relay.exceptions import AuditError

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for tool invocations and security events.

    Logs in JSONL format (newline-delimited JSON) for streaming and easy parsing.
    """

    def __init__(self, config: AuditConfig):
        """
        Initialize audit logger.

        Args:
            config: Audit configuration
        """
        self.config = config
        self._log_file: Optional[Path] = None
        self._file_handle: Optional[Any] = None

        if config.enabled:
            self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup audit log file."""
        try:
            self._log_file = Path(self.config.log_file)
            self._log_file.parent.mkdir(parents=True, exist_ok=True)

            # Open file in append mode
            self._file_handle = open(self._log_file, "a", encoding="utf-8")
            logger.info(f"Audit logging enabled: {self._log_file}")

        except Exception as e:
            raise AuditError(
                f"Failed to setup audit logging: {e}",
                details={"log_file": self.config.log_file, "error": str(e)},
            )

    def _write_log(self, event: dict[str, Any]) -> None:
        """
        Write log entry to file.

        Args:
            event: Log event dictionary
        """
        if not self.config.enabled or not self._file_handle:
            return

        try:
            # Add timestamp
            event["timestamp"] = datetime.utcnow().isoformat() + "Z"

            # Write as JSONL (newline-delimited JSON)
            json_line = json.dumps(event, ensure_ascii=False)
            self._file_handle.write(json_line + "\n")
            self._file_handle.flush()

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            # Don't raise - audit logging failure shouldn't break the relay

    def log_tool_invocation_start(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        user_id: str,
        request_id: str,
    ) -> None:
        """
        Log tool invocation start.

        Args:
            tool_name: Name of tool being called
            arguments: Tool arguments
            user_id: User ID making the call
            request_id: Unique request ID
        """
        event = {
            "event_type": "tool_invocation_start",
            "request_id": request_id,
            "tool_name": tool_name,
            "user_id": user_id,
        }

        # Include arguments if configured
        if self.config.include_arguments:
            event["arguments"] = arguments
        else:
            event["arguments_count"] = len(arguments)

        self._write_log(event)

    def log_tool_invocation_end(
        self,
        tool_name: str,
        request_id: str,
        success: bool,
        result: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> None:
        """
        Log tool invocation end.

        Args:
            tool_name: Name of tool
            request_id: Unique request ID
            success: Whether invocation succeeded
            result: Tool result (if successful)
            error: Error message (if failed)
            duration_ms: Execution duration in milliseconds
        """
        event = {
            "event_type": "tool_invocation_end",
            "request_id": request_id,
            "tool_name": tool_name,
            "success": success,
        }

        if duration_ms is not None:
            event["duration_ms"] = duration_ms

        if success and result:
            # Include full result if configured, otherwise just size
            if self.config.include_results:
                event["result"] = result
            else:
                result_str = json.dumps(result)
                event["result_size_bytes"] = len(result_str.encode("utf-8"))
        elif error:
            event["error"] = error

        self._write_log(event)

    def log_authentication_event(
        self,
        event_type: str,
        user_id: str,
        success: bool,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Log authentication event.

        Args:
            event_type: Type of auth event (login, token_refresh, etc.)
            user_id: User ID
            success: Whether authentication succeeded
            details: Additional event details
        """
        event = {
            "event_type": f"auth_{event_type}",
            "user_id": user_id,
            "success": success,
        }

        if details:
            event["details"] = details

        self._write_log(event)

    def log_policy_violation(
        self,
        tool_name: str,
        user_id: str,
        profile: str,
        reason: str,
    ) -> None:
        """
        Log policy violation.

        Args:
            tool_name: Name of tool that was denied
            user_id: User ID
            profile: Active policy profile
            reason: Reason for denial
        """
        event = {
            "event_type": "policy_violation",
            "tool_name": tool_name,
            "user_id": user_id,
            "profile": profile,
            "reason": reason,
        }

        self._write_log(event)

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Log security event.

        Args:
            event_type: Type of security event
            severity: Severity level (low, medium, high, critical)
            message: Event message
            details: Additional event details
        """
        event = {
            "event_type": f"security_{event_type}",
            "severity": severity,
            "message": message,
        }

        if details:
            event["details"] = details

        self._write_log(event)

    def close(self) -> None:
        """Close audit log file."""
        if self._file_handle:
            try:
                self._file_handle.close()
                logger.info("Audit log file closed")
            except Exception as e:
                logger.error(f"Error closing audit log file: {e}")
            finally:
                self._file_handle = None

    def __enter__(self) -> "AuditLogger":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

# Made with Bob
