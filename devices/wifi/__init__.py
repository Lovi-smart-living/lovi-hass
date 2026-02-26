"""Lovi WiFi devices.

This package contains WiFi-connected device implementations.
Each device type has a factory that registers with the global registry.
"""

from ..base import LoviDeviceInfo
from ..registry import registry

# Import device classes to register them
from .presence_gen_one import PresenceGenOne, PresenceGenOneFactory

# Register factories (auto-registration)
registry.register(PresenceGenOneFactory())

__all__ = [
    "LoviDeviceInfo",
    "PresenceGenOne",
    "PresenceGenOneFactory",
]
