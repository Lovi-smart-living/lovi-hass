"""Input validation utilities for Lovi API.

This module provides input validation functions to ensure
data integrity and prevent invalid data from reaching devices.

Example:
    from utils.validators import validate_host, validate_port, validate_sensitivity

    # Validate device configuration
    validate_host("192.168.1.100")  # OK
    validate_host("invalid")  # Raises ValidationError

    # Validate settings
    validate_sensitivity(75)  # OK
    validate_sensitivity(150)  # Raises ValidationError
"""

from __future__ import annotations

import ipaddress
import re
from typing import Any

from ..api.exceptions import LoviValidationError


def validate_host(host: str) -> str:
    """Validate a hostname or IP address.

    Args:
        host: Hostname or IP address string

    Returns:
        Validated host string

    Raises:
        LoviValidationError: If host is invalid
    """
    if not host:
        raise LoviValidationError("Host cannot be empty", field="host")

    # Try to validate as IP address
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    # Validate as hostname
    # Hostname regex: alphanumeric, dots, hyphens, max 253 chars
    hostname_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    if not re.match(hostname_pattern, host):
        raise LoviValidationError(
            f"Invalid hostname or IP address: {host}", field="host"
        )

    return host


def validate_port(port: int) -> int:
    """Validate a port number.

    Args:
        port: Port number

    Returns:
        Validated port number

    Raises:
        LoviValidationError: If port is invalid
    """
    if not isinstance(port, int):
        raise LoviValidationError(f"Port must be an integer, got {type(port)}", field="port")

    if port < 1 or port > 65535:
        raise LoviValidationError(
            f"Port must be between 1 and 65535, got {port}", field="port"
        )

    return port


def validate_sensitivity(value: int | float) -> int:
    """Validate sensitivity value (0-100).

    Args:
        value: Sensitivity value

    Returns:
        Validated sensitivity as integer

    Raises:
        LoviValidationError: If sensitivity is invalid
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise LoviValidationError(
            f"Sensitivity must be a number, got {type(value)}", field="sensitivity"
        )

    if value < 0 or value > 100:
        raise LoviValidationError(
            f"Sensitivity must be between 0 and 100, got {value}", field="sensitivity"
        )

    return value


def validate_distance(value: float | int) -> float:
    """Validate distance value in meters.

    Args:
        value: Distance value

    Returns:
        Validated distance as float

    Raises:
        LoviValidationError: If distance is invalid
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise LoviValidationError(
            f"Distance must be a number, got {type(value)}", field="distance"
        )

    if value < 0:
        raise LoviValidationError(
            f"Distance must be positive, got {value}", field="distance"
        )

    return value


def validate_temperature(value: float | int) -> float:
    """Validate temperature value in Celsius.

    Args:
        value: Temperature value

    Returns:
        Validated temperature as float

    Raises:
        LoviValidationError: If temperature is invalid
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise LoviValidationError(
            f"Temperature must be a number, got {type(value)}", field="temperature"
        )

    # Sanity check: -100°C to 100°C
    if value < -100 or value > 100:
        raise LoviValidationError(
            f"Temperature out of reasonable range: {value}", field="temperature"
        )

    return value


def validate_device_id(device_id: str) -> str:
    """Validate device ID.

    Args:
        device_id: Device ID string

    Returns:
        Validated device ID

    Raises:
        LoviValidationError: If device ID is invalid
    """
    if not device_id:
        raise LoviValidationError("Device ID cannot be empty", field="device_id")

    if not isinstance(device_id, str):
        raise LoviValidationError(
            f"Device ID must be a string, got {type(device_id)}", field="device_id"
        )

    # Device ID should be alphanumeric with allowed separators
    if not re.match(r"^[a-zA-Z0-9_\-]+$", device_id):
        raise LoviValidationError(
            f"Device ID contains invalid characters: {device_id}", field="device_id"
        )

    return device_id


def validate_device_name(name: str) -> str:
    """Validate device name.

    Args:
        name: Device name string

    Returns:
        Validated device name

    Raises:
        LoviValidationError: If name is invalid
    """
    if not name:
        raise LoviValidationError("Device name cannot be empty", field="name")

    if not isinstance(name, str):
        raise LoviValidationError(
            f"Device name must be a string, got {type(name)}", field="name"
        )

    if len(name) > 100:
        raise LoviValidationError(
            f"Device name too long (max 100 chars): {len(name)}", field="name"
        )

    return name.strip()


def validate_api_key(api_key: str | None) -> str | None:
    """Validate API key.

    Args:
        api_key: API key string or None

    Returns:
        Validated API key or None

    Raises:
        LoviValidationError: If API key is invalid
    """
    if api_key is None:
        return None

    if not isinstance(api_key, str):
        raise LoviValidationError(
            f"API key must be a string, got {type(api_key)}", field="api_key"
        )

    if len(api_key) < 8:
        raise LoviValidationError(
            "API key too short (min 8 characters)", field="api_key"
        )

    return api_key


def validate_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate device settings dictionary.

    Args:
        settings: Settings dictionary

    Returns:
        Validated settings

    Raises:
        LoviValidationError: If any setting is invalid
    """
    if not isinstance(settings, dict):
        raise LoviValidationError(
            f"Settings must be a dictionary, got {type(settings)}", field="settings"
        )

    validated = {}

    # Validate known settings
    if "sensitivity" in settings:
        validated["sensitivity"] = validate_sensitivity(settings["sensitivity"])

    if "led" in settings:
        led = settings["led"]
        if not isinstance(led, bool):
            raise LoviValidationError(
                f"LED must be a boolean, got {type(led)}", field="led"
            )
        validated["led"] = led

    if "name" in settings:
        validated["name"] = validate_device_name(settings["name"])

    return validated


def sanitize_dict(data: dict[str, Any], allowed_keys: list[str]) -> dict[str, Any]:
    """Sanitize a dictionary to only include allowed keys.

    Args:
        data: Input dictionary
        allowed_keys: List of allowed key names

    Returns:
        Sanitized dictionary
    """
    return {k: v for k, v in data.items() if k in allowed_keys}
