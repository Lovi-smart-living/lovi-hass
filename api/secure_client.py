"""Secure API client for Lovi devices.

This module provides a secure API client with:
- Token-based authentication
- HTTPS support
- Retry with exponential backoff
- Request timeout handling
- Input validation

Example:
    from api.secure_client import SecureApiClient, ApiCredentials

    credentials = ApiCredentials(api_key="my-api-key")
    client = SecureApiClient("192.168.1.100", 80, credentials)

    # Make authenticated requests
    data = await client.get("/api/status")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .exceptions import (
    LoviApiError,
    LoviAuthenticationError,
    LoviConnectionError,
    LoviTimeoutError,
    LoviValidationError,
)

_LOGGER = logging.getLogger(__name__)

# Default configuration
DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 2  # seconds


@dataclass
class ApiCredentials:
    """API credentials for device authentication.

    Attributes:
        api_key: API key for authentication
        token: Optional JWT token (if using token auth)
    """

    api_key: str | None = None
    token: str | None = None


class SecureApiClient:
    """Secure API client for Lovi devices.

    Features:
    - HTTPS by default (can be disabled for local development)
    - Token/API key authentication
    - Retry with exponential backoff
    - Request timeout handling
    - Input validation

    Example:
        credentials = ApiCredentials(api_key="device-api-key")
        client = SecureApiClient("192.168.1.100", 80, credentials)

        # Get device status
        status = await client.get("/api/status")

        # Update settings
        await client.post("/api/settings", {"sensitivity": 75})
    """

    def __init__(
        self,
        host: str,
        port: int,
        credentials: ApiCredentials | None = None,
        use_https: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        hass: Any = None,
    ) -> None:
        """Initialize the secure API client.

        Args:
            host: Device IP address or hostname
            port: Device port
            credentials: API credentials
            use_https: Use HTTPS (default: True)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            hass: Home Assistant instance (optional)
        """
        self.host = host
        self.port = port
        self.credentials = credentials or ApiCredentials()
        self.use_https = use_https
        self.timeout = timeout
        self.max_retries = max_retries
        self._hass = hass
        self._session: aiohttp.ClientSession | None = None

        # Build base URL
        scheme = "https" if use_https else "http"
        self.base_url = f"{scheme}://{host}:{port}"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session.

        Returns:
            aiohttp ClientSession
        """
        if self._session is None or self._session.closed:
            if self._hass:
                self._session = async_get_clientsession(self._hass)
            else:
                self._session = aiohttp.ClientSession()
        return self._session

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Add authentication
        if self.credentials.token:
            headers["Authorization"] = f"Bearer {self.credentials.token}"
        elif self.credentials.api_key:
            headers["X-API-Key"] = self.credentials.api_key

        return headers

    async def request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated, secure request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body (optional)

        Returns:
            Response data as dictionary

        Raises:
            LoviConnectionError: If connection fails
            LoviTimeoutError: If request times out
            LoviAuthenticationError: If authentication fails
            LoviApiError: If API returns an error
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                timeout = aiohttp.ClientTimeout(total=self.timeout)

                async with session.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=headers,
                    timeout=timeout,
                ) as response:
                    await self._handle_response_errors(response, endpoint)
                    return await response.json()

            except LoviApiError:
                # Don't retry on API errors
                raise

            except aiohttp.ServerTimeoutError:
                if attempt == self.max_retries - 1:
                    raise LoviTimeoutError(
                        f"Request to {endpoint} timed out after "
                        f"{self.max_retries} attempts"
                    ) from None
                await self._backoff(attempt)

            except aiohttp.ClientConnectorError as err:
                if attempt == self.max_retries - 1:
                    raise LoviConnectionError(
                        f"Failed to connect to {self.host}:{self.port} - {err}"
                    ) from None
                await self._backoff(attempt)

            except aiohttp.ClientError as err:
                raise LoviConnectionError(
                    f"Request failed: {err}"
                ) from err

        raise LoviConnectionError("Max retries exceeded")

    async def _backoff(self, attempt: int) -> None:
        """Wait before retry with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)
        """
        import asyncio

        wait_time = DEFAULT_BACKOFF_FACTOR ** attempt
        _LOGGER.debug(
            "Retry attempt %d for %s, waiting %ds",
            attempt + 1,
            self.host,
            wait_time,
        )
        await asyncio.sleep(wait_time)

    def _handle_response_errors(
        self,
        response: aiohttp.ClientResponse,
        endpoint: str,
    ) -> None:
        """Handle HTTP response errors.

        Args:
            response: aiohttp response object
            endpoint: API endpoint that was called

        Raises:
            LoviAuthenticationError: For 401/403 responses
            LoviApiError: For other error responses
        """
        if response.status == 401 or response.status == 403:
            raise LoviAuthenticationError(
                f"Authentication failed for {endpoint}",
                status_code=response.status,
                endpoint=endpoint,
            )

        if response.status >= 400:
            raise LoviApiError(
                f"API error: {response.status}",
                status_code=response.status,
                endpoint=endpoint,
            )

    async def get(self, endpoint: str) -> dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint: API endpoint path

        Returns:
            Response data
        """
        return await self.request("GET", endpoint)

    async def post(
        self,
        endpoint: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint: API endpoint path
            data: Request body

        Returns:
            Response data
        """
        return await self.request("POST", endpoint, data)

    async def put(
        self,
        endpoint: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Make a PUT request.

        Args:
            endpoint: API endpoint path
            data: Request body

        Returns:
            Response data
        """
        return await self.request("PUT", endpoint, data)

    async def delete(self, endpoint: str) -> dict[str, Any]:
        """Make a DELETE request.

        Args:
            endpoint: API endpoint path

        Returns:
            Response data
        """
        return await self.request("DELETE", endpoint)

    async def async_get_data(self) -> dict[str, Any]:
        """Get device status data.

        Returns:
            Dictionary with device status (presence, motion, distance, etc.)
        """
        return await self.get("/api/status")

    async def async_get_device_info(self) -> dict[str, Any]:
        """Get device information.

        Returns:
            Dictionary with device info (id, type, name, model, etc.)
        """
        return await self.get("/api/device")

    async def async_set_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Update device settings.

        Args:
            settings: Settings to update (e.g., {"sensitivity": 75, "led": true})

        Returns:
            Dictionary with updated settings
        """
        return await self.post("/api/settings", settings)

    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def set_hass(self, hass: Any) -> None:
        """Set the Home Assistant instance.

        Args:
            hass: Home Assistant instance
        """
        self._hass = hass


# Backwards compatibility - keep old name available
LoviApiClient = SecureApiClient
