"""Data update coordinator for Lovi devices."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import LoviApiClient
from .api import LoviConnectionError
from .const import DOMAIN
from .devices.wifi import LoviWifiDevice


class LoviDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for Lovi devices."""

    def __init__(self, hass: HomeAssistant, client: LoviApiClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self._device: LoviWifiDevice | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        try:
            data = await self.client.async_get_data()
            # Create device instance if not exists
            if self._device is None:
                device_info = await self.client.async_get_device_info()
                self._device = LoviWifiDevice(device_info)
            return data
        except LoviConnectionError as err:
            raise UpdateFailed(f"Connection failed: {err}") from err

    @property
    def device(self) -> LoviWifiDevice | None:
        """Return the device."""
        return self._device


import logging

_LOGGER = logging.getLogger(__name__)

