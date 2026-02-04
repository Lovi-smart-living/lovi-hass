"""API client for Lovi devices."""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_TIMEOUT


class LoviApiClient:
    """API client for communicating with Lovi devices."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the API client."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = async_get_clientsession(self._hass)
        return self._session

    async def async_get_data(self) -> dict[str, Any]:
        """Get data from the device."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/api/status",
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError:
            raise LoviConnectionError("Connection timed out")
        except aiohttp.ClientError as err:
            raise LoviConnectionError(f"Connection error: {err}")

    async def async_set_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Set state on the device."""
        try:
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/api/state",
                json=state,
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError:
            raise LoviConnectionError("Connection timed out")
        except aiohttp.ClientError as err:
            raise LoviConnectionError(f"Connection error: {err}")

    async def async_get_device_info(self) -> dict[str, Any]:
        """Get device information."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/api/device",
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError:
            raise LoviConnectionError("Connection timed out")
        except aiohttp.ClientError as err:
            raise LoviConnectionError(f"Connection error: {err}")

    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def set_hass(self, hass: Any) -> None:
        """Set the hass instance for the session."""
        self._hass = hass


class LoviConnectionError(Exception):
    """Exception for connection errors."""

