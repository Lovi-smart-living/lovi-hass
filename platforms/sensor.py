"""Lovi sensor platform for Home Assistant."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import LoviDataUpdateCoordinator
from .devices.wifi.presence_gen_one import PresenceGenOne


SENSOR_TYPES: list[SensorEntityDescription] = [
    SensorEntityDescription(
        key="presence",
        name="Presence",
        icon="mdi:account-question",
        device_class=SensorDeviceClass.ENUM,
        options=["detected", "not_detected"],
        translation_key="presence_status",
    ),
    SensorEntityDescription(
        key="motion",
        name="Motion",
        icon="mdi:run",
        translation_key="motion_status",
    ),
    SensorEntityDescription(
        key="distance",
        name="Distance",
        icon="mdi:arrow-left-right",
        native_unit_of_measurement="m",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="detection_distance",
    ),
    SensorEntityDescription(
        key="sensitivity",
        name="Sensitivity",
        icon="mdi:-tune",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="detection_sensitivity",
    ),
    SensorEntityDescription(
        key="temperature",
        name="Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="device_temperature",
    ),
    SensorEntityDescription(
        key="uptime",
        name="Uptime",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="device_uptime",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lovi sensors from a config entry."""
    coordinator: LoviDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Wait for device to be available
    await coordinator.async_config_entry_first_refresh()

    entities: list[LoviSensor] = []

    # Create sensors for each description
    for description in SENSOR_TYPES:
        entity = LoviSensor(coordinator, description)
        entities.append(entity)

    async_add_entities(entities)


class LoviSensor(CoordinatorEntity, SensorEntity):
    """Sensor entity for Lovi Presence Gen One device."""

    def __init__(
        self,
        coordinator: LoviDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.host}_{description.key}"
        self._attr_has_entity_name = True

        # Set device info
        if coordinator.device:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.device.device_id)},
                name=coordinator.device.name,
                manufacturer=MANUFACTURER,
                model=coordinator.device.model,
                sw_version=coordinator.device.device_info.sw_version,
            )

    @property
    def native_value(self) -> str | int | float | None:
        """Return the sensor value."""
        if self.coordinator.device is None:
            return None

        device = self.coordinator.device

        if not isinstance(device, PresenceGenOne):
            return None

        key = self.entity_description.key

        if key == "presence":
            return "detected" if device.is_present else "not_detected"
        elif key == "motion":
            return "detected" if device.has_motion else "clear"
        elif key == "distance":
            return device.distance
        elif key == "sensitivity":
            return device.sensitivity
        elif key == "temperature":
            return device.temperature
        elif key == "uptime":
            return device.uptime

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.coordinator.device is None:
            return None

        device = self.coordinator.device

        if not isinstance(device, PresenceGenOne):
            return None

        if self.entity_description.key == "presence":
            return {
                "device_type": device.device_type,
            }

        return None

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()

