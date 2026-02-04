"""Presence Gen One - ESP8266 Human Presence Sensor."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import LoviDeviceInfo, LoviWifiDevice


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


class PresenceGenOne(LoviWifiDevice):
    """Presence Gen One - ESP8266 Human Presence Sensor.

    This device uses radar-based human presence detection.
    It communicates over WiFi and provides presence, motion,
    and distance information.
    """

    PRESENCE_DEVICE_TYPE = "presence_gen_one"
    MODEL_NAME = "Presence Gen One"

    def __init__(self, device_info: dict[str, Any]) -> None:
        """Initialize the Presence Gen One sensor."""
        # Ensure model is set correctly
        device_info["model"] = self.MODEL_NAME
        super().__init__(device_info)
        self._state = PresenceGenOneState()

    @property
    def device_type(self) -> str:
        """Return the device type."""
        return self.PRESENCE_DEVICE_TYPE

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

    @property
    def state(self) -> PresenceGenOneState:
        """Return the current device state."""
        return self._state

    def update(self, data: dict[str, Any]) -> None:
        """Update device state from API data."""
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

    def set_sensitivity(self, value: int) -> None:
        """Set the detection sensitivity."""
        self._state.sensitivity = max(0, min(100, value))

    def set_led(self, enabled: bool) -> None:
        """Enable or disable the LED indicator."""
        self._state.led_enabled = enabled

    def clear_motion(self) -> None:
        """Clear the motion detection state."""
        self._state.motion = False

