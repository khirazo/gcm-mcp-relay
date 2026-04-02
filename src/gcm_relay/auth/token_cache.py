# This file includes AI-generated code - Review and modify as needed
"""
In-memory token cache with TTL support.

Tokens are cached in memory only and never persisted to disk for security.
"""

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class CachedToken:
    """Cached access token with metadata."""

    access_token: str
    expires_at: float  # Unix timestamp
    user_id: str
    refresh_token_hash: Optional[str] = None  # For HTTP mode


class TokenCache:
    """
    In-memory token cache with TTL support.

    Tokens are stored in memory only and automatically expire based on TTL.
    Proactive refresh happens 60 seconds before expiry.
    """

    def __init__(self, refresh_buffer_seconds: int = 60):
        """
        Initialize token cache.

        Args:
            refresh_buffer_seconds: Refresh tokens this many seconds before expiry
        """
        self._cache: dict[str, CachedToken] = {}
        self._refresh_buffer = refresh_buffer_seconds

    def get(self, key: str) -> Optional[str]:
        """
        Get cached access token if valid.

        Args:
            key: Cache key (user_id for stdio, refresh_token_hash for HTTP)

        Returns:
            Access token if cached and valid, None otherwise
        """
        cached = self._cache.get(key)
        if not cached:
            return None

        # Check if token is expired or needs refresh
        now = time.time()
        if now >= cached.expires_at - self._refresh_buffer:
            # Token expired or needs refresh
            del self._cache[key]
            return None

        return cached.access_token

    def set(
        self,
        key: str,
        access_token: str,
        expires_in: int,
        user_id: str,
        refresh_token_hash: Optional[str] = None,
    ) -> None:
        """
        Cache access token with TTL.

        Args:
            key: Cache key (user_id for stdio, refresh_token_hash for HTTP)
            access_token: Access token to cache
            expires_in: Token lifetime in seconds
            user_id: User ID associated with token
            refresh_token_hash: Hash of refresh token (HTTP mode only)
        """
        expires_at = time.time() + expires_in
        self._cache[key] = CachedToken(
            access_token=access_token,
            expires_at=expires_at,
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
        )

    def invalidate(self, key: str) -> None:
        """
        Invalidate cached token.

        Args:
            key: Cache key to invalidate
        """
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached tokens."""
        self._cache.clear()

    def get_stats(self) -> dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        now = time.time()
        valid_count = sum(
            1 for token in self._cache.values() if now < token.expires_at
        )
        return {
            "total_cached": len(self._cache),
            "valid_tokens": valid_count,
            "expired_tokens": len(self._cache) - valid_count,
        }

# Made with Bob
