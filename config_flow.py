"""Config flow for Lovi integration."""
from ipaddress import ip_address
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client

from .api import ApiCredentials, SecureApiClient
from .api.exceptions import LoviConnectionError, LoviApiError
from .const import DEFAULT_PORT, DOMAIN

try:
    from homeassistant.components.zeroconf import ZeroconfServiceInfo
except ImportError:
    from typing import Any as ZeroconfServiceInfo

_LOGGER = logging.getLogger(__name__)

ZEROCONF_SERVICE_TYPE = "_lovi._tcp.local."

DEVICE_INFO_PROPERTIES = [
    "mac",
    "model",
    "device_type",
    "firmware_version",
    "capabilities",
]


class LoviConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lovi."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - auto-discover devices."""
        # Automatically trigger discovery first
        return await self.async_step_discovery()

    async def async_step_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle discovery step - scan network for Lovi devices."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get("action") == "manual":
                return await self.async_step_manual()
            elif user_input.get("action") == "setup_new":
                return await self.async_step_setup_new()
            elif user_input.get("action") == "scan":
                # User clicked scan - try to find devices
                return await self._async_scan_for_devices()

        # Auto-scan on first entry
        return await self._async_scan_for_devices()

    async def _async_scan_for_devices(self) -> FlowResult:
        """Scan network for Lovi devices."""
        # Get the network prefix from the host
        hostname = self.hass.helpers.instance_name()
        local_ip = ""
        try:
            s = self.hass.helpers.aiohttp_client._async_create_clientsession()
        except Exception:
            pass

        # Use aiohttp from HA
        session = aiohttp_client.async_get_clientsession(self.hass)
        
        # Get local IP
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        if local_ip:
            # Scan local network for Lovi devices
            prefix = ".".join(local_ip.split(".")[:3])
            discovered_devices = []

            # Try common IPs or scan range
            for last_octet in [1, 14, 50, 100, 150, 200, 250]:
                ip = f"{prefix}.{last_octet}"
                try:
                    async with session.get(f"http://{ip}/status", timeout=1) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "device_type" in data or "model" in data:
                                discovered_devices.append({
                                    "host": ip,
                                    "port": 80,
                                    "model": data.get("model", "Lovi Device"),
                                    "device_type": data.get("device_type", "unknown"),
                                })
                except Exception:
                    pass

            if discovered_devices:
                # Found devices - create entry for first one
                device = discovered_devices[0]
                return await self._async_validate_and_create_entry(
                    device["host"],
                    device["port"],
                    discovery_data=device,
                )

        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): vol.In(
                        {
                            "scan": "Scan Network",
                            "manual": "Enter IP Manually",
                            "setup_new": "Set up new device (AP mode)",
                        }
                    )
                }
            ),
            errors={},
            description_placeholders={
                "message": "Searching for Lovi devices on your network...\n\n"
                          "If a device is found, it will appear automatically.\n\n"
                          "Make sure your device is powered on and connected to the same network.",
            },
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual IP entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                ip_address(user_input[CONF_HOST])
            except ValueError:
                errors["base"] = "invalid_ip_address"

            if not errors:
                return await self._async_validate_and_create_entry(
                    user_input[CONF_HOST],
                    user_input.get(CONF_PORT, DEFAULT_PORT),
                )

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )

    async def async_step_setup_new(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle setup of new device (AP mode instructions)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get("action") == "continue":
                return await self.async_step_manual()
            elif user_input.get("action") == "done":
                return self.async_abort(reason="setup_complete")

        return self.async_show_form(
            step_id="setup_new",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): vol.In(
                        {
                            "continue": "I've Connected My Device",
                        }
                    )
                }
            ),
            errors=errors,
        )

    async def _async_validate_and_create_entry(
        self, host: str, port: int, discovery_data: dict | None = None
    ) -> FlowResult:
        """Validate device and create entry."""
        entry_data = {
            CONF_HOST: host,
            CONF_PORT: port,
        }

        if discovery_data:
            entry_data.update(discovery_data)

        try:
            client = SecureApiClient(
                host=host,
                port=port,
                credentials=ApiCredentials(),
                use_https=False,
                timeout=5,
            )
            try:
                device_info = await client.get("/api/device")
                entry_data["device_id"] = device_info.get("id", "")
                entry_data["device_name"] = device_info.get("name", "")
                entry_data["device_type"] = device_info.get("type", "")
                entry_data["firmware_version"] = device_info.get("firmware_version", "")
            finally:
                await client.close()
        except LoviConnectionError:
            _LOGGER.warning("Could not connect to device at %s:%d", host, port)
        except LoviApiError as err:
            _LOGGER.warning("API error for %s:%d: %s", host, port, err)

        device_name = entry_data.get("device_name") or entry_data.get("model", "Lovi Device")
        title = f"Lovi - {device_name}"

        return self.async_create_entry(
            title=title,
            data=entry_data,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.debug("Discovered Lovi device via zeroconf: %s", discovery_info)

        # Get service type
        service_type = discovery_info.type
        
        # If discovered via HTTP service, check if it's a Lovi device
        if "_http._tcp" in service_type:
            # Check if the name contains "lovi" or if we have lovi-specific properties
            name = discovery_info.name.lower() if discovery_info.name else ""
            if "lovi" not in name:
                _LOGGER.debug("Discovered HTTP service is not a Lovi device: %s", name)
                return self.async_abort(reason="not_lovi_device")

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
        """Validate discovered device by calling the API."""
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
        """Handle zeroconf discovery - auto-create without confirmation."""
        discovery_info = self.context.get("discovery_info", {})
        validated_data = self.context.get("validated_data", {})

        host = discovery_info.get("host", "")
        port = discovery_info.get("port", DEFAULT_PORT)
        device_name = validated_data.get(
            "device_name", discovery_info.get("model", "Lovi Device")
        )

        entry_data = {
            CONF_HOST: host,
            CONF_PORT: port,
        }

        if validated_data.get("api_validated"):
            entry_data["device_id"] = validated_data.get("device_id")
            entry_data["device_type"] = validated_data.get("device_type")
            entry_data["firmware_version"] = validated_data.get("firmware_version")
            entry_data["capabilities"] = validated_data.get("capabilities")
            entry_data["device_name"] = device_name

        # Auto-create entry without user confirmation
        return self.async_create_entry(
            title=f"Lovi - {device_name}",
            data=entry_data,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "LoviOptionsFlowHandler":
        """Get options flow."""
        return LoviOptionsFlowHandler(config_entry)


class LoviOptionsFlowHandler(OptionsFlow):
    """Handle options flow for Lovi integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
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

