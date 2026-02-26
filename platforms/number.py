"""Lovi number platform for Home Assistant."""
from __future__ import annotations

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import LoviDataUpdateCoordinator


SENSITIVITY_DESCRIPTION = NumberEntityDescription(
    key="sensitivity",
    name="Sensitivity",
    icon="mdi:tune",
    translation_key="sensitivity",
    native_min_value=0,
    native_max_value=100,
    native_unit_of_measurement="%",
    mode=NumberMode.SLIDER,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lovi number entities from a config entry."""
    coordinator: LoviDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    await coordinator.async_config_entry_first_refresh()

    if coordinator.device is None:
        return

    if not coordinator.device.capabilities.has_sensitivity:
        return

    async_add_entities([LoviNumber(coordinator)])


class LoviNumber(CoordinatorEntity, NumberEntity):
    """Number entity for Lovi device sensitivity control."""

    def __init__(
        self,
        coordinator: LoviDataUpdateCoordinator,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = SENSITIVITY_DESCRIPTION
        self._attr_unique_id = f"{coordinator.client.host}_sensitivity"
        self._attr_has_entity_name = True

        if coordinator.device:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.device.device_id)},
                name=coordinator.device.name,
                manufacturer=MANUFACTURER,
                model=coordinator.device.model,
                sw_version=coordinator.device.device_info.sw_version,
            )

    @property
    def native_value(self) -> float | None:
        """Return the current sensitivity value."""
        if self.coordinator.device is None:
            return None

        # Get sensitivity from device state
        return float(self.coordinator.device.state.get("sensitivity", 0))

    async def async_set_native_value(self, value: float) -> None:
        """Set the sensitivity value."""
        await self.coordinator.async_set_sensitivity(int(value))
        await self.coordinator.async_request_refresh()
