"""Device factory pattern for Lovi IoT devices.

This module provides the factory pattern for creating device instances.
Each device type implements a factory that handles instantiation and
describes its capabilities.

Example:
    from abc import ABC, abstractmethod
    from dataclasses import dataclass

    @dataclass
    class DeviceCapabilities:
        supported_entities: list[str]
        has_sensitivity: bool = False
        has_led_control: bool = False

    class DeviceFactory(ABC):
        @property
        def device_type(self) -> str:
            pass

        @property
        def capabilities(self) -> DeviceCapabilities:
            pass

        def create(self, device_info: dict) -> LoviDevice:
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
        supported_entities: List of HA entity types (e.g., ["sensor", "switch"])
        has_sensitivity: Whether device supports sensitivity control
        has_led_control: Whether device supports LED on/off control
        supports_motion: Whether device reports motion detection
        supports_presence: Whether device reports presence detection
        has_temperature: Whether device reports temperature
        has_humidity: Whether device reports humidity
    """

    supported_entities: list[str] = field(default_factory=list)
    has_sensitivity: bool = False
    has_led_control: bool = False
    supports_motion: bool = False
    supports_presence: bool = False
    has_temperature: bool = False
    has_humidity: bool = False
    has_power_monitoring: bool = False


class DeviceFactory(ABC):
    """Abstract factory for creating device instances.

    Each device type implements this interface to provide:
    - Device creation
    - Capability description
    - Entity definitions for Home Assistant

    Example:
        class PresenceGenOneFactory(DeviceFactory):
            DEVICE_TYPE = "presence_gen_one"

            @property
            def capabilities(self) -> DeviceCapabilities:
                return DeviceCapabilities(
                    supported_entities=["binary_sensor", "sensor"],
                    has_sensitivity=True,
                    has_led_control=True,
                    supports_presence=True,
                    supports_motion=True,
                )

            def create(self, device_info: dict) -> PresenceGenOne:
                return PresenceGenOne(device_info)
    """

    @property
    @abstractmethod
    def device_type(self) -> str:
        """Unique identifier for this device type.

        This should match the device type reported by the device's API.

        Returns:
            Device type string (e.g., "presence_gen_one")
        """
        pass

    @property
    @abstractmethod
    def capabilities(self) -> DeviceCapabilities:
        """What this device type supports.

        Returns:
            DeviceCapabilities describing supported features
        """
        pass

    @abstractmethod
    def create(self, device_info: dict[str, Any]) -> Any:
        """Create a device instance.

        Args:
            device_info: Device configuration from discovery/config

        Returns:
            Initialized device instance
        """
        pass

    def get_entity_descriptions(self) -> list[Any]:
        """Get Home Assistant entity descriptions for this device.

        Returns a list of entity descriptions that this device type
        will create in Home Assistant. Each platform (sensor, switch, etc.)
        has its own set of entity descriptions.

        Returns:
            List of EntityDescription objects
        """
        return []


class BinarySensorFactoryMixin:
    """Mixin for devices that have binary sensor entities.

    Provides common entity descriptions for presence/motion sensors.
    """

    def get_binary_sensor_descriptions(self) -> list[Any]:
        """Get binary sensor entity descriptions.

        Returns entity descriptions for:
        - Presence (binary_sensor)
        - Motion (binary_sensor)
        """
        # Import here to avoid circular imports
        from homeassistant.components.binary_sensor import (
            BinarySensorEntityDescription,
        )

        descriptions = []

        capabilities = self.capabilities
        if capabilities.supports_presence:
            descriptions.append(
                BinarySensorEntityDescription(
                    key="presence",
                    name="Presence",
                    icon="mdi:account-question",
                    translation_key="presence_status",
                )
            )

        if capabilities.supports_motion:
            descriptions.append(
                BinarySensorEntityDescription(
                    key="motion",
                    name="Motion",
                    icon="mdi:motion-sensor",
                    translation_key="motion_status",
                )
            )

        return descriptions


class SensorFactoryMixin:
    """Mixin for devices that have sensor entities.

    Provides common entity descriptions for various sensor types.
    """

    def get_sensor_descriptions(self) -> list[Any]:
        """Get sensor entity descriptions.

        Returns entity descriptions for various sensor types.
        """
        from homeassistant.components.sensor import (
            SensorEntityDescription,
            SensorDeviceClass,
            SensorStateClass,
        )
        from homeassistant.const import UnitOfTemperature

        descriptions = []

        capabilities = self.capabilities

        if capabilities.has_temperature:
            descriptions.append(
                SensorEntityDescription(
                    key="temperature",
                    name="Temperature",
                    icon="mdi:thermometer",
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    translation_key="device_temperature",
                )
            )

        if capabilities.has_humidity:
            descriptions.append(
                SensorEntityDescription(
                    key="humidity",
                    name="Humidity",
                    icon="mdi:water-percent",
                    native_unit_of_measurement="%",
                    device_class=SensorDeviceClass.HUMIDITY,
                    state_class=SensorStateClass.MEASUREMENT,
                    translation_key="device_humidity",
                )
            )

        if capabilities.has_sensitivity:
            descriptions.append(
                SensorEntityDescription(
                    key="sensitivity",
                    name="Sensitivity",
                    icon="mdi:tune",
                    native_unit_of_measurement="%",
                    state_class=SensorStateClass.MEASUREMENT,
                    translation_key="detection_sensitivity",
                )
            )

        if capabilities.has_power_monitoring:
            descriptions.append(
                SensorEntityDescription(
                    key="power",
                    name="Power",
                    icon="mdi:flash",
                    native_unit_of_measurement="W",
                    device_class=SensorDeviceClass.POWER,
                    state_class=SensorStateClass.MEASUREMENT,
                    translation_key="power_consumption",
                )
            )

        # Always include uptime
        descriptions.append(
            SensorEntityDescription(
                key="uptime",
                name="Uptime",
                icon="mdi:clock-outline",
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.TOTAL_INCREASING,
                translation_key="device_uptime",
            )
        )

        return descriptions
