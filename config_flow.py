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

from .api import ApiCredentials, SecureApiClient
from .api.exceptions import LoviConnectionError, LoviApiError
from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

ZEROCONF_SERVICE_TYPE = "_lovi._tcp.local."

DEVICE_INFO_PROPERTIES = [
    "mac",
    "model",
    "device_type",
    "firmware_version",
    "capabilities",
]


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
        port = discovery_info.port
        properties = discovery_info.properties

        mac_address = properties.get("mac", "")
        device_type = properties.get("device_type", "unknown")
        model = properties.get("model", "Lovi Device")
        firmware_version = properties.get("firmware_version", "unknown")
        capabilities = properties.get("capabilities", "")

        if not mac_address:
            _LOGGER.warning("No MAC address in discovery info, aborting")
            return self.async_abort(reason="invalid_discovery_info")

        unique_id = f"lovi-{mac_address.replace(':', '').lower()}"

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        discovery_data = {
            "host": host,
            "port": port,
            "mac": mac_address,
            "device_type": device_type,
            "model": model,
            "firmware_version": firmware_version,
            "capabilities": capabilities,
        }

        self.context["title_placeholders"] = {
            "name": model,
            "host": host,
        }
        self.context["discovery_info"] = discovery_data

        try:
            validated_data = await self._validate_discovered_device(
                host, port, discovery_data
            )
            discovery_data.update(validated_data)
            self.context["validated_data"] = validated_data
        except LoviConnectionError:
            _LOGGER.warning(
                "Could not validate device at %s:%d, proceeding with discovery data",
                host,
                port,
            )
        except LoviApiError as err:
            _LOGGER.warning(
                "Device validation failed for %s:%d: %s", host, port, err
            )

        return await self.async_step_zeroconf_confirm()

    async def _validate_discovered_device(
        self,
        host: str,
        port: int,
        discovery_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate discovered device by calling the API.

        Args:
            host: Device IP address
            port: Device port
            discovery_data: Discovery properties

        Returns:
            Validated device data

        Raises:
            LoviConnectionError: If device cannot be reached
            LoviApiError: If API returns an error
        """
        _LOGGER.debug("Validating discovered device at %s:%d", host, port)

        client = SecureApiClient(
            host=host,
            port=port,
            credentials=ApiCredentials(),
            use_https=False,
            timeout=5,
        )

        try:
            device_info = await client.get("/api/device")

            validated_data = {
                "device_id": device_info.get("id", ""),
                "device_name": device_info.get("name", discovery_data.get("model")),
                "device_type": device_info.get("type", discovery_data.get("device_type")),
                "firmware_version": device_info.get(
                    "firmware_version", discovery_data.get("firmware_version")
                ),
                "capabilities": device_info.get(
                    "capabilities", discovery_data.get("capabilities")
                ),
                "api_validated": True,
            }

            _LOGGER.debug("Device validated successfully: %s", validated_data)
            return validated_data

        finally:
            await client.close()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user confirmation of discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            discovery_info = self.context.get("discovery_info")
            validated_data = self.context.get("validated_data", {})

            if discovery_info:
                host = discovery_info.get("host", "")
                port = discovery_info.get("port", DEFAULT_PORT)
                mac_address = discovery_info.get("mac", "")
                device_name = validated_data.get(
                    "device_name", discovery_info.get("model", "Lovi Device")
                )

                unique_id = f"lovi-{mac_address.replace(':', '').lower()}"

                entry_data = {
                    CONF_HOST: host,
                    CONF_PORT: port,
                }

                if validated_data.get("api_validated"):
                    entry_data["device_id"] = validated_data.get("device_id")
                    entry_data["device_type"] = validated_data.get("device_type")
                    entry_data["firmware_version"] = validated_data.get("firmware_version")
                    entry_data["capabilities"] = validated_data.get("capabilities")

                return self.async_create_entry(
                    title=f"Lovi - {device_name}",
                    data=entry_data,
                )

        discovery_info = self.context.get("discovery_info", {})
        device_name = discovery_info.get(
            "model",
            discovery_info.get("device_name", "Lovi Device"),
        )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "name": device_name,
                "host": discovery_info.get("host", ""),
                "device_type": discovery_info.get("device_type", "unknown"),
                "firmware_version": discovery_info.get("firmware_version", "unknown"),
            },
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

