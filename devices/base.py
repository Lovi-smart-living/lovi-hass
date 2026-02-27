"""Base device class for Lovi devices.

This module provides the abstract base class for all Lovi devices.
All device implementations must inherit from LoviDevice and implement
the required properties and methods.

Example:
    from abc import ABC, abstractmethod
    from dataclasses import dataclass

    @dataclass
    class LoviDeviceInfo:
        device_id: str
        name: str
        model: str
        manufacturer: str = "Lovi"
        sw_version: str | None = None
        hw_version: str | None = None

    class LoviDevice(ABC):
        @property
        @abstractmethod
        def device_type(self) -> str:
            pass

        @property
        @abstractmethod
        def device_info(self) -> LoviDeviceInfo:
            pass

        @abstractmethod
        def update(self, data: dict) -> None:
            pass
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeviceCapabilities:
    """Describes what a device type can do.

    Attributes:
        has_presence: Whether device reports presence detection
        has_motion: Whether device reports motion detection
        has_temperature: Whether device reports temperature
        has_humidity: Whether device reports humidity
        has_led: Whether device has LED indicator control
        has_led_brightness: Whether device supports LED brightness control
        has_sensitivity: Whether device supports sensitivity control
        max_distance: Maximum detection distance in meters (0 if not applicable)
        supported_entities: List of HA entity types (e.g., ["sensor", "switch"])
    """

    has_presence: bool = False
    has_motion: bool = False
    has_temperature: bool = False
    has_humidity: bool = False
    has_led: bool = False
    has_led_brightness: bool = False
    has_sensitivity: bool = False
    max_distance: float = 0.0
    supported_entities: list[str] = field(default_factory=list)


@dataclass
class LoviDeviceInfo:
    """Dataclass for device information.

    Attributes:
        device_id: Unique identifier for the device
        name: Human-readable device name
        model: Device model name
        manufacturer: Device manufacturer (default: "Lovi")
        sw_version: Software/firmware version
        hw_version: Hardware version
    """

    device_id: str
    name: str
    model: str
    manufacturer: str = "Lovi"
    sw_version: str | None = None
    hw_version: str | None = None


class LoviDevice(ABC):
    """Abstract base class for all Lovi devices.

    All device implementations must inherit from this class and implement
    the required properties and methods.

    Properties:
        device_type: Unique identifier (e.g., "presence_gen_one")
        device_info: Device metadata

    Methods:
        update(): Update state from API data
        async_set_sensitivity(): Set sensitivity (if supported)
        async_set_led(): Control LED (if supported)
        async_reboot(): Reboot device (if supported)
        async_factory_reset(): Factory reset (if supported)

    Example:
        class MyDevice(LoviDevice):
            DEVICE_TYPE = "my_device"

            def __init__(self, device_info: dict):
                self._info = LoviDeviceInfo(
                    device_id=device_info["id"],
                    name=device_info["name"],
                    model="My Device",
                )

            @property
            def device_type(self) -> str:
                return self.DEVICE_TYPE

            @property
            def device_info(self) -> LoviDeviceInfo:
                return self._info

            def update(self, data: dict) -> None:
                # Update state from API data
                pass
    """

    @property
    @abstractmethod
    def device_type(self) -> str:
        """Return the device type identifier.

        This should match the device type reported by the device's API
        and registered in the device registry.

        Returns:
            Device type string (e.g., "presence_gen_one")
        """
        pass

    @property
    @abstractmethod
    def device_info(self) -> LoviDeviceInfo:
        """Return device information.

        Returns:
            LoviDeviceInfo with device metadata
        """
        pass

    @property
    def device_id(self) -> str:
        """Return the device ID.

        Convenience property that delegates to device_info.

        Returns:
            Device unique identifier
        """
        return self.device_info.device_id

    @property
    def name(self) -> str:
        """Return the device name.

        Convenience property that delegates to device_info.

        Returns:
            Human-readable device name
        """
        return self.device_info.name

    @property
    def model(self) -> str:
        """Return the device model.

        Convenience property that delegates to device_info.

        Returns:
            Device model name
        """
        return self.device_info.model

    @property
    def manufacturer(self) -> str:
        """Return the device manufacturer.

        Convenience property that delegates to device_info.

        Returns:
            Manufacturer name
        """
        return self.device_info.manufacturer

    @property
    def sw_version(self) -> str | None:
        """Return the software version.

        Convenience property that delegates to device_info.

        Returns:
            Software version or None
        """
        return self.device_info.sw_version

    @property
    def state(self) -> dict[str, Any]:
        """Return current device state as dictionary.

        Returns:
            Dictionary containing current device state
        """
        return {}

    @property
    def capabilities(self) -> DeviceCapabilities:
        """Return device capabilities.

        Returns:
            DeviceCapabilities describing what this device supports
        """
        return DeviceCapabilities()

    async def async_capabilities(self) -> DeviceCapabilities:
        """Asynchronously detect and return device capabilities.

        Override in device classes to detect capabilities from the device.
        Default implementation returns the static capabilities property.

        Returns:
            DeviceCapabilities describing what this device supports
        """
        return self.capabilities

    @abstractmethod
    def update(self, data: dict[str, Any]) -> None:
        """Update device state from API data.

        This method is called when new data is received from the device.
        Implementations should parse the data and update internal state.

        Args:
            data: Raw data from device API
        """
        pass

    async def async_set_sensitivity(self, value: int) -> bool:
        """Set detection sensitivity.

        Override in device classes that support sensitivity control.

        Args:
            value: Sensitivity value (0-100)

        Returns:
            True if successful

        Raises:
            NotImplementedError: If device doesn't support sensitivity
        """
        raise NotImplementedError(
            f"{self.device_type} does not support sensitivity control"
        )

    async def async_set_led(self, enabled: bool) -> bool:
        """Enable or disable LED.

        Override in device classes that support LED control.

        Args:
            enabled: LED state

        Returns:
            True if successful

        Raises:
            NotImplementedError: If device doesn't support LED control
        """
        raise NotImplementedError(
            f"{self.device_type} does not support LED control"
        )

    async def async_set_led_brightness(self, brightness: int) -> bool:
        """Set LED brightness.

        Override in device classes that support LED brightness control.

        Args:
            brightness: Brightness value 0-255

        Returns:
            True if successful

        Raises:
            NotImplementedError: If device doesn't support LED brightness
        """
        raise NotImplementedError(
            f"{self.device_type} does not support LED brightness control"
        )

    async def async_reboot(self) -> bool:
        """Reboot the device.

        Override in device classes that support remote reboot.

        Returns:
            True if successful

        Raises:
            NotImplementedError: If device doesn't support reboot
        """
        raise NotImplementedError(
            f"{self.device_type} does not support reboot"
        )

    async def async_factory_reset(self) -> bool:
        """Factory reset the device.

        Override in device classes that support factory reset.

        Returns:
            True if successful

        Raises:
            NotImplementedError: If device doesn't support factory reset
        """
        raise NotImplementedError(
            f"{self.device_type} does not support factory reset"
        )


# Backwards compatibility - keep old class name available
class LoviWifiDevice(LoviDevice):
    """Legacy base class for WiFi-connected Lovi devices.

    This class is kept for backwards compatibility.
    New code should use LoviDevice directly.
    """

    def __init__(self, device_info: dict[str, Any]) -> None:
        """Initialize the device.

        Args:
            device_info: Device configuration dictionary
        """
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
