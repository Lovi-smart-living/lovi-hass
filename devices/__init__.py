"""Lovi device implementations.

This package provides the device abstraction layer for Lovi IoT devices.

Key Components:
- LoviDevice: Abstract base class for all devices
- LoviDeviceInfo: Dataclass for device metadata
- DeviceRegistry: Central registry for device types
- DeviceFactory: Factory pattern for creating devices
- DeviceCapabilities: Describes device features

Adding New Device Types:
1. Create device class inheriting from LoviDevice
2. Create factory inheriting from DeviceFactory
3. Register factory with registry

Example:
    from devices.base import LoviDevice, LoviDeviceInfo
    from devices.factory import DeviceFactory, DeviceCapabilities
    from devices.registry import registry

    class MyDevice(LoviDevice):
        DEVICE_TYPE = "my_device"

        def __init__(self, device_info: dict):
            self._info = LoviDeviceInfo(...)

        # ... implement abstract methods

    class MyDeviceFactory(DeviceFactory):
        DEVICE_TYPE = "my_device"

        @property
        def capabilities(self) -> DeviceCapabilities:
            return DeviceCapabilities(
                supported_entities=["sensor"],
                has_led_control=True,
            )

        def create(self, device_info: dict) -> MyDevice:
            return MyDevice(device_info)

    # Register the factory
    registry.register(MyDeviceFactory())
"""

from .base import LoviDevice, LoviDeviceInfo, LoviWifiDevice
from .factory import DeviceCapabilities, DeviceFactory
from .registry import DeviceRegistry, registry

__all__ = [
    # Base classes
    "LoviDevice",
    "LoviDeviceInfo",
    "LoviWifiDevice",
    # Factory
    "DeviceFactory",
    "DeviceCapabilities",
    # Registry
    "DeviceRegistry",
    "registry",
]
