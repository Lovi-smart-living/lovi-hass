"""Lovi API client.

This package provides the API client for communicating with Lovi devices.

Components:
- SecureApiClient: Main API client with security features
- ApiCredentials: Credentials container
- Exceptions: Custom exception classes

Example:
    from api import SecureApiClient, ApiCredentials

    credentials = ApiCredentials(api_key="my-key")
    client = SecureApiClient("192.168.1.100", 80, credentials)

    status = await client.get("/api/status")
"""

from .exceptions import (
    LoviApiError,
    LoviAuthenticationError,
    LoviConnectionError,
    LoviDeviceError,
    LoviException,
    LoviTimeoutError,
    LoviValidationError,
)
from .secure_client import ApiCredentials, SecureApiClient

__all__ = [
    # Client
    "SecureApiClient",
    "ApiCredentials",
    # Exceptions
    "LoviException",
    "LoviConnectionError",
    "LoviAuthenticationError",
    "LoviApiError",
    "LoviTimeoutError",
    "LoviValidationError",
    "LoviDeviceError",
]
