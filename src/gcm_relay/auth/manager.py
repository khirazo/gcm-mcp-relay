# This file includes AI-generated code - Review and modify as needed
"""
Authentication manager for GCM MCP Relay.

Handles OAuth2/OIDC authentication flow with Keycloak and GCM authorization.
"""

import base64
import logging
from typing import Optional

import httpx

from gcm_relay.auth.token_cache import TokenCache
from gcm_relay.config.models import Config
from gcm_relay.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    TokenRefreshError,
)

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """
    Manages authentication with GCM via OAuth2/OIDC.

    Two-step authentication flow:
    1. Get OAuth2 access token from Keycloak
    2. Authorize with GCM user management endpoint
    """

    def __init__(self, config: Config):
        """
        Initialize authentication manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.token_cache = TokenCache()
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                verify=self.config.gcm.verify_ssl,
                timeout=self.config.gcm.request_timeout,
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _get_keycloak_url(self) -> str:
        """
        Get Keycloak token endpoint URL.
        
        Uses configured OIDC host if set, otherwise falls back to GCM host.
        This supports both scenarios:
        - OIDC on same host as GCM (different port)
        - OIDC on different host (e.g., dedicated Keycloak server)
        """
        oidc_host = self.config.gcm.oidc.get_host(self.config.gcm.host)
        oidc_port = self.config.gcm.oidc.port
        realm = self.config.gcm.oidc.realm

        return f"https://{oidc_host}:{oidc_port}/realms/{realm}/protocol/openid-connect/token"

    def _get_gcm_auth_url(self) -> str:
        """Get GCM authorization endpoint URL."""
        return f"https://{self.config.gcm.host}:{self.config.gcm.api_port}/ibm/usermanagement/api/v2/authorization"

    async def _get_oauth2_token(self) -> dict:
        """
        Get OAuth2 access token from Keycloak.

        Returns:
            Token response with access_token, expires_in, etc.

        Raises:
            AuthenticationError: If authentication fails
        """
        client = await self._get_http_client()
        token_url = self._get_keycloak_url()

        # Prepare Basic Auth header
        client_id = self.config.gcm.auth.client_id
        client_secret = self.config.gcm.auth.client_secret
        basic_auth = base64.b64encode(
            f"{client_id}:{client_secret}".encode()
        ).decode()

        # Prepare token request
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "password",
            "username": self.config.gcm.auth.username,
            "password": self.config.gcm.auth.password,
            "scope": "openid",
        }

        try:
            response = await client.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"OAuth2 authentication failed: {e}")
            raise AuthenticationError(
                f"Failed to get OAuth2 token: {e.response.status_code}",
                details={
                    "status_code": e.response.status_code,
                    "response": e.response.text,
                },
            )
        except Exception as e:
            logger.error(f"OAuth2 request failed: {e}")
            raise AuthenticationError(
                f"OAuth2 request failed: {e}",
                details={"error": str(e)},
            )

    async def _authorize_with_gcm(self, access_token: str) -> None:
        """
        Authorize with GCM user management endpoint.

        Args:
            access_token: OAuth2 access token

        Raises:
            AuthenticationError: If authorization fails
        """
        client = await self._get_http_client()
        auth_url = self._get_gcm_auth_url()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        data = {"tenantId": ""}

        try:
            response = await client.post(auth_url, headers=headers, json=data)
            response.raise_for_status()
            logger.debug("GCM authorization successful")
        except httpx.HTTPStatusError as e:
            logger.error(f"GCM authorization failed: {e}")
            raise AuthenticationError(
                f"Failed to authorize with GCM: {e.response.status_code}",
                details={
                    "status_code": e.response.status_code,
                    "response": e.response.text,
                },
            )
        except Exception as e:
            logger.error(f"GCM authorization request failed: {e}")
            raise AuthenticationError(
                f"GCM authorization request failed: {e}",
                details={"error": str(e)},
            )

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get valid access token, using cache if available.

        Args:
            force_refresh: Force token refresh even if cached

        Returns:
            Valid access token

        Raises:
            AuthenticationError: If authentication fails
        """
        # Use username as cache key for stdio mode
        cache_key = self.config.gcm.auth.username

        # Check cache first
        if not force_refresh:
            cached_token = self.token_cache.get(cache_key)
            if cached_token:
                logger.debug("Using cached access token")
                return cached_token

        # Get new token
        logger.info("Authenticating with GCM...")

        # Step 1: Get OAuth2 token from Keycloak
        token_response = await self._get_oauth2_token()
        access_token = token_response.get("access_token")
        expires_in = token_response.get("expires_in", 300)  # Default 5 minutes

        if not access_token:
            raise AuthenticationError("No access token in OAuth2 response")

        # Step 2: Authorize with GCM
        await self._authorize_with_gcm(access_token)

        # Cache the token
        self.token_cache.set(
            key=cache_key,
            access_token=access_token,
            expires_in=expires_in,
            user_id=self.config.gcm.auth.username,
        )

        logger.info("Authentication successful")
        return access_token

    async def refresh_token_if_needed(self) -> Optional[str]:
        """
        Refresh token if it's close to expiry.

        Returns:
            New access token if refreshed, None if not needed
        """
        cache_key = self.config.gcm.auth.username
        cached_token = self.token_cache.get(cache_key)

        if cached_token is None:
            # Token needs refresh
            return await self.get_access_token(force_refresh=True)

        return None

    def invalidate_token(self) -> None:
        """Invalidate cached token."""
        cache_key = self.config.gcm.auth.username
        self.token_cache.invalidate(cache_key)
        logger.debug("Token invalidated")

    async def __aenter__(self) -> "AuthenticationManager":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

# Made with Bob
