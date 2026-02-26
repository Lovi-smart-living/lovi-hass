"""Device registry for Lovi IoT devices.

This module provides the central registry that manages all device types.
New device types are registered with factories, and the registry creates
instances as needed.

Example:
    from devices.registry import registry
    from devices.presence_gen_one import PresenceGenOneFactory

    # Register a device factory
    registry.register(PresenceGenOneFactory())

    # Create a device instance
    device = registry.create("presence_gen_one", {"id": "lovi_001", "name": "Living Room"})
"""

from __future__ import annotations

from typing import Any

from .factory import DeviceFactory


class DeviceRegistry:
    """Central registry for all device types.

    This is the foundation for scalability. Each device type registers
    itself with a factory, and the registry creates instances as needed.

    Adding a new device type requires:
    1. Create device class inheriting from LoviDevice
    2. Create device factory inheriting from DeviceFactory
    3. Register factory with registry

    Example:
        registry = DeviceRegistry()
        registry.register(PresenceGenOneFactory())
        registry.register(TemperatureSensorFactory())
    """

    _instance: DeviceRegistry | None = None

    def __init__(self) -> None:
        """Initialize the registry."""
        self._factories: dict[str, DeviceFactory] = {}

    @classmethod
    def get_instance(cls) -> DeviceRegistry:
        """Get the singleton instance of the registry.

        Returns:
            The global DeviceRegistry instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, factory: DeviceFactory) -> None:
        """Register a device factory.

        Args:
            factory: Device factory for a specific device type

        Raises:
            ValueError: If a factory for this device type is already registered
        """
        device_type = factory.device_type
        if device_type in self._factories:
            raise ValueError(
                f"Device type '{device_type}' is already registered. "
                f"Use replace() to override."
            )
        self._factories[device_type] = factory

    def replace(self, factory: DeviceFactory) -> None:
        """Replace an existing device factory.

        Use this to override a previously registered device type.

        Args:
            factory: Device factory for a specific device type
        """
        self._factories[factory.device_type] = factory

    def unregister(self, device_type: str) -> None:
        """Unregister a device type.

        Args:
            device_type: The device type to remove

        Raises:
            KeyError: If the device type is not registered
        """
        del self._factories[device_type]

    def create(self, device_type: str, device_info: dict[str, Any]) -> Any:
        """Create device instance from device type and info.

        Args:
            device_type: Type identifier (e.g., "presence_gen_one")
            device_info: Device configuration and metadata

        Returns:
            Device instance for the given type

        Raises:
            ValueError: If device_type is not registered
        """
        if device_type not in self._factories:
            available = ", ".join(sorted(self._factories.keys()))
            raise ValueError(
                f"Unknown device type: '{device_type}'. "
                f"Available types: {available or 'none'}"
            )
        return self._factories[device_type].create(device_info)

    def get_supported_types(self) -> list[str]:
        """Get list of all supported device types.

        Returns:
            List of device type identifiers
        """
        return list(self._factories.keys())

    def get_capabilities(self, device_type: str) -> Any:
        """Get capabilities for a device type.

        Args:
            device_type: The device type to query

        Returns:
            DeviceCapabilities for the requested type

        Raises:
            ValueError: If device_type is not registered
        """
        if device_type not in self._factories:
            raise ValueError(f"Unknown device type: '{device_type}'")
        return self._factories[device_type].capabilities

    def get_entity_descriptions(
        self, device_type: str
    ) -> list[Any]:
        """Get Home Assistant entity descriptions for a device type.

        Args:
            device_type: The device type to query

        Returns:
            List of EntityDescription objects for this device

        Raises:
            ValueError: If device_type is not registered
        """
        if device_type not in self._factories:
            raise ValueError(f"Unknown device type: '{device_type}'")
        return self._factories[device_type].get_entity_descriptions()

    def is_supported(self, device_type: str) -> bool:
        """Check if a device type is supported.

        Args:
            device_type: The device type to check

        Returns:
            True if the device type is registered
        """
        return device_type in self._factories

    def clear(self) -> None:
        """Clear all registered device types.

        Useful for testing.
        """
        self._factories.clear()


# Global registry instance
registry = DeviceRegistry.get_instance()
