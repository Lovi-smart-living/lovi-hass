"""Presence Gen One - ESP8266 Human Presence Sensor.

This module provides the Presence Gen One device implementation and factory.
The device uses radar-based human presence detection with LD2410C sensor.

Device Type: presence_gen_one

Features:
- Presence detection (static and moving people)
- Motion detection
- Distance measurement (0-6m)
- Configurable sensitivity (0-100%)
- LED indicator control
- Temperature reporting
- Uptime tracking
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.sensor import SensorEntityDescription

from ...devices.base import LoviDevice, LoviDeviceInfo
from ...devices.factory import DeviceCapabilities, DeviceFactory
from ...devices.registry import registry


# ============================================================================
# Device State
# ============================================================================


@dataclass
class PresenceGenOneState:
    """State dataclass for Presence Gen One sensor."""

    presence: bool = False
    motion: bool = False
    distance: float = 0.0
    sensitivity: int = 50
    led_enabled: bool = True
    temperature: float | None = None
    uptime: int = 0


# ============================================================================
# Device Implementation
# ============================================================================


class PresenceGenOne(LoviDevice):
    """Presence Gen One - ESP8266 Human Presence Sensor.

    This device uses LD2410C radar-based human presence detection.
    It communicates over WiFi and provides presence, motion,
    and distance information.

    API Endpoints:
    - GET /api/status - Device status
    - GET /api/presence - Presence detection data
    - POST /api/settings - Update settings (sensitivity, LED)
    """

    DEVICE_TYPE = "presence_gen_one"
    MODEL_NAME = "Presence Gen One"

    def __init__(self, device_info: dict[str, Any]) -> None:
        """Initialize the Presence Gen One sensor.

        Args:
            device_info: Device configuration from discovery/config
        """
        self._info = LoviDeviceInfo(
            device_id=device_info.get("id", ""),
            name=device_info.get("name", "Lovi Presence"),
            model=self.MODEL_NAME,
            manufacturer="Lovi",
            sw_version=device_info.get("sw_version"),
            hw_version=device_info.get("hw_version"),
        )
        self._state = PresenceGenOneState()

    @property
    def device_type(self) -> str:
        """Return the device type identifier."""
        return self.DEVICE_TYPE

    @property
    def device_info(self) -> LoviDeviceInfo:
        """Return device information."""
        return self._info

    @property
    def state(self) -> dict[str, Any]:
        """Return current device state as dictionary."""
        return {
            "presence": self._state.presence,
            "motion": self._state.motion,
            "distance": self._state.distance,
            "sensitivity": self._state.sensitivity,
            "led": self._state.led_enabled,
            "temperature": self._state.temperature,
            "uptime": self._state.uptime,
        }

    @property
    def raw_state(self) -> PresenceGenOneState:
        """Return the raw state object."""
        return self._state

    # Convenience properties
    @property
    def is_present(self) -> bool:
        """Return whether presence is detected."""
        return self._state.presence

    @property
    def has_motion(self) -> bool:
        """Return whether motion is detected."""
        return self._state.motion

    @property
    def distance(self) -> float:
        """Return the distance to detected object in meters."""
        return self._state.distance

    @property
    def sensitivity(self) -> int:
        """Return the detection sensitivity (0-100)."""
        return self._state.sensitivity

    @property
    def led_enabled(self) -> bool:
        """Return whether the LED indicator is enabled."""
        return self._state.led_enabled

    @property
    def temperature(self) -> float | None:
        """Return the device temperature in Celsius."""
        return self._state.temperature

    @property
    def uptime(self) -> int:
        """Return the device uptime in seconds."""
        return self._state.uptime

    def update(self, data: dict[str, Any]) -> None:
        """Update device state from API data.

        Args:
            data: Raw data from device API
        """
        if "presence" in data:
            self._state.presence = bool(data["presence"])
        if "motion" in data:
            self._state.motion = bool(data["motion"])
        if "distance" in data:
            self._state.distance = float(data["distance"])
        if "sensitivity" in data:
            self._state.sensitivity = int(data["sensitivity"])
        if "led" in data:
            self._state.led_enabled = bool(data["led"])
        if "temperature" in data:
            temp = data["temperature"]
            self._state.temperature = float(temp) if temp is not None else None
        if "uptime" in data:
            self._state.uptime = int(data["uptime"])

    async def async_set_sensitivity(self, value: int) -> bool:
        """Set detection sensitivity.

        Args:
            value: Sensitivity value (0-100)

        Returns:
            True if successful
        """
        self._state.sensitivity = max(0, min(100, value))
        return True

    async def async_set_led(self, enabled: bool) -> bool:
        """Enable or disable the LED indicator.

        Args:
            enabled: LED state

        Returns:
            True if successful
        """
        self._state.led_enabled = enabled
        return True


# ============================================================================
# Device Factory
# ============================================================================


class PresenceGenOneFactory(DeviceFactory):
    """Factory for Presence Gen One devices."""

    DEVICE_TYPE = "presence_gen_one"

    @property
    def device_type(self) -> str:
        """Return the device type identifier."""
        return self.DEVICE_TYPE

    @property
    def capabilities(self) -> DeviceCapabilities:
        """Return device capabilities."""
        return DeviceCapabilities(
            supported_entities=["binary_sensor", "sensor", "switch", "number"],
            has_sensitivity=True,
            has_led_control=True,
            supports_motion=True,
            supports_presence=True,
            has_temperature=True,
        )

    def create(self, device_info: dict[str, Any]) -> PresenceGenOne:
        """Create a Presence Gen One device instance.

        Args:
            device_info: Device configuration

        Returns:
            Initialized PresenceGenOne device
        """
        return PresenceGenOne(device_info)

    def get_entity_descriptions(self) -> list:
        """Get Home Assistant entity descriptions.

        Returns:
            List of entity descriptions for this device
        """
        entities = []

        # Binary sensors
        entities.append(
            BinarySensorEntityDescription(
                key="presence",
                name="Presence",
                icon="mdi:account-question",
                translation_key="presence_status",
            )
        )
        entities.append(
            BinarySensorEntityDescription(
                key="motion",
                name="Motion",
                icon="mdi:motion-sensor",
                translation_key="motion_status",
            )
        )

        # Sensors
        entities.append(
            SensorEntityDescription(
                key="distance",
                name="Distance",
                icon="mdi:arrow-left-right",
                native_unit_of_measurement="m",
                translation_key="detection_distance",
            )
        )
        entities.append(
            SensorEntityDescription(
                key="sensitivity",
                name="Sensitivity",
                icon="mdi:tune",
                native_unit_of_measurement="%",
                translation_key="detection_sensitivity",
            )
        )
        entities.append(
            SensorEntityDescription(
                key="temperature",
                name="Temperature",
                icon="mdi:thermometer",
                native_unit_of_measurement="°C",
                translation_key="device_temperature",
            )
        )
        entities.append(
            SensorEntityDescription(
                key="uptime",
                name="Uptime",
                icon="mdi:clock-outline",
                translation_key="device_uptime",
            )
        )

        return entities


# Auto-register the factory
# Note: This is done in wifi/__init__.py for explicit control
# registry.register(PresenceGenOneFactory())
