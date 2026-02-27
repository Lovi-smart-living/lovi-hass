"""Lovi Home Assistant integration."""

# Lazy imports to avoid hard dependency on homeassistant at import time
async def async_setup_entry(hass, entry):
    """Set up Lovi integration from a config entry."""
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import CONF_HOST, CONF_PORT, Platform
    from homeassistant.core import HomeAssistant

    from .const import DOMAIN
    from .coordinator import LoviDataUpdateCoordinator
    from .api import SecureApiClient

    PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    # Create API client (use_https=False for local devices)
    client = SecureApiClient(host, port, use_https=False)
    client.set_hass(hass)

    # Create coordinator
    coordinator = LoviDataUpdateCoordinator(hass, client)

    # Store coordinator in hass data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    from homeassistant.const import Platform
    from homeassistant.config_entries import ConfigEntry

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]
    )

    if unload_ok:
        # Remove coordinator from hass data
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
