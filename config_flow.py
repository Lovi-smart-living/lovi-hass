"""Config flow for Lovi integration."""
from ipaddress import ip_address
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class LoviConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lovi."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate IP address
            try:
                ip_address(user_input[CONF_HOST])
            except ValueError:
                errors["base"] = "invalid_ip_address"

            if not errors:
                # Create entry
                return self.async_create_entry(
                    title=f"Lovi - {user_input[CONF_HOST]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.debug("Discovered Lovi device via zeroconf: %s", discovery_info)

        host = discovery_info.host
        mac_address = discovery_info.properties.get("mac", "")
        model = discovery_info.properties.get("model", "Lovi Device")

        unique_id = f"lovi-{mac_address.replace(':', '').lower()}"

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {
            "name": model,
            "host": host,
        }
        self.context["discovery_info"] = discovery_info

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user confirmation of discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            discovery_info = self.context.get("discovery_info")
            if discovery_info:
                host = discovery_info.host
                mac_address = discovery_info.properties.get("mac", "")
                unique_id = f"lovi-{mac_address.replace(':', '').lower()}"

                return self.async_create_entry(
                    title=f"Lovi - {host}",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: DEFAULT_PORT,
                    },
                )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema({}),
            description_placeholders=self.context.get("title_placeholders"),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "LoviOptionsFlowHandler":
        """Get options flow."""
        return LoviOptionsFlowHandler(config_entry)


class LoviOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Lovi integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = {
            vol.Optional(
                CONF_PORT,
                default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT),
            ): int,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))

