"""Base device class for Lovi devices."""
from __future__ import annotations

from typing import Any
from dataclasses import dataclass


@dataclass
class LoviDeviceInfo:
    """Dataclass for device information."""

    device_id: str
    name: str
    model: str
    manufacturer: str = "Lovi"
    sw_version: str | None = None
    hw_version: str | None = None


class LoviWifiDevice:
    """Base class for WiFi-connected Lovi devices."""

    def __init__(self, device_info: dict[str, Any]) -> None:
        """Initialize the device."""
        self._device_info = LoviDeviceInfo(
            device_id=device_info.get("id", ""),
            name=device_info.get("name", "Lovi Device"),
            model=device_info.get("model", ""),
            manufacturer=device_info.get("manufacturer", "Lovi"),
            sw_version=device_info.get("sw_version"),
            hw_version=device_info.get("hw_version"),
        )

    @property
    def device_info(self) -> LoviDeviceInfo:
        """Return device information."""
        return self._device_info

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self._device_info.device_id

    @property
    def name(self) -> str:
        """Return the device name."""
        return self._device_info.name

    @property
    def model(self) -> str:
        """Return the device model."""
        return self._device_info.model

    def update(self, data: dict[str, Any]) -> None:
        """Update device state from API data."""
        pass

