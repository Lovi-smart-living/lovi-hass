"""Data update coordinator for Lovi devices."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import SecureApiClient
from .api import LoviConnectionError
from .const import DOMAIN
from .devices import LoviDevice
from .devices.registry import registry

_LOGGER = logging.getLogger(__name__)


class LoviDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for Lovi devices.

    This coordinator manages data fetching from Lovi devices and
    automatically creates the appropriate device instance based on
    the device type reported by the device.
    """

    def __init__(self, hass: HomeAssistant, client: SecureApiClient) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            client: API client for device communication
        """
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self._device: LoviDevice | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device.

        Returns:
            Dictionary containing device data

        Raises:
            UpdateFailed: If connection fails
        """
        try:
            data = await self.client.async_get_data()

            # Create device instance if not exists
            if self._device is None:
                device_info = await self.client.async_get_device_info()
                device_type = device_info.get("type", "presence_gen_one")

                # Use registry to create device instance
                self._device = registry.create(device_type, device_info)
                _LOGGER.info(
                    "Created device instance: %s (%s)",
                    self._device.name,
                    self._device.device_type,
                )

            # Update device state with new data
            self._device.update(data)

            return data

        except LoviConnectionError as err:
            raise UpdateFailed(f"Connection failed: {err}") from err
        except ValueError as err:
            raise UpdateFailed(f"Device error: {err}") from err

    @property
    def device(self) -> LoviDevice | None:
        """Return the device instance.

        Returns:
            The device instance or None if not yet initialized
        """
        return self._device

    @property
    def device_type(self) -> str | None:
        """Return the device type.

        Returns:
            Device type string or None
        """
        return self._device.device_type if self._device else None

    @property
    def device_id(self) -> str | None:
        """Return the device ID.

        Returns:
            Device ID string or None
        """
        return self._device.device_id if self._device else None

    async def async_set_sensitivity(self, value: int) -> bool:
        """Set device sensitivity.

        Args:
            value: Sensitivity value (0-100)

        Returns:
            True if successful

        Raises:
            NotImplementedError: If device doesn't support sensitivity
        """
        if self._device is None:
            raise ValueError("Device not initialized")
        return await self._device.async_set_sensitivity(value)

    async def async_set_led(self, enabled: bool) -> bool:
        """Set device LED state.

        Args:
            enabled: LED state

        Returns:
            True if successful

        Raises:
            NotImplementedError: If device doesn't support LED control
        """
        if self._device is None:
            raise ValueError("Device not initialized")
        return await self._device.async_set_led(enabled)
