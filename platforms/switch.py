"""Lovi switch platform for Home Assistant."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import LoviDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lovi switches from a config entry."""
    coordinator: LoviDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    await coordinator.async_config_entry_first_refresh()

    if coordinator.device is None:
        return

    if coordinator.device.capabilities.has_led:
        async_add_entities([LoviLedSwitch(coordinator)])


class LoviLedSwitch(CoordinatorEntity, SwitchEntity):
    """Switch entity for Lovi LED control."""

    def __init__(self, coordinator: LoviDataUpdateCoordinator) -> None:
        """Initialize the LED switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.host}_led"
        self._attr_has_entity_name = True
        self.entity_description = SwitchEntityDescription(
            key="led",
            name="LED",
            translation_key="led",
        )

        if coordinator.device:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.device.device_id)},
                name=coordinator.device.name,
                manufacturer=MANUFACTURER,
                model=coordinator.device.model,
                sw_version=coordinator.device.device_info.sw_version,
            )

    @property
    def is_on(self) -> bool | None:
        """Return the LED state."""
        if self.coordinator.device is None:
            return None

        return self.coordinator.device.led_enabled

    @property
    def icon(self) -> str | None:
        """Return the icon based on LED state."""
        if self.is_on is None:
            return "mdi:led-off"
        return "mdi:led-on" if self.is_on else "mdi:led-off"

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the LED on."""
        await self.coordinator.async_set_led(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the LED off."""
        await self.coordinator.async_set_led(False)

    async def async_toggle(self, **kwargs) -> None:
        """Toggle the LED."""
        if self.is_on is not None:
            await self.coordinator.async_set_led(not self.is_on)
