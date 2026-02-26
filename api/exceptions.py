"""Custom exceptions for Lovi API."""

from __future__ import annotations


class LoviException(Exception):
    """Base exception for Lovi errors."""

    pass


class LoviConnectionError(LoviException):
    """Exception for connection errors.

    Raised when the device cannot be reached or connection times out.
    """

    pass


class LoviAuthenticationError(LoviException):
    """Exception for authentication failures.

    Raised when authentication fails or credentials are invalid.
    """

    pass


class LoviApiError(LoviException):
    """Exception for API errors.

    Raised when the device returns an error response.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        endpoint: str | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code if available
            endpoint: API endpoint that caused the error
        """
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint


class LoviTimeoutError(LoviConnectionError):
    """Exception for timeout errors.

    Raised when a request times out.
    """

    pass


class LoviValidationError(LoviException):
    """Exception for validation errors.

    Raised when input validation fails.
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            field: Field name that failed validation
        """
        super().__init__(message)
        self.field = field


class LoviDeviceError(LoviException):
    """Exception for device-specific errors.

    Raised when the device returns an error or is in an invalid state.
    """

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """Initialize device error.

        Args:
            message: Error message
            error_code: Device-specific error code
        """
        super().__init__(message)
        self.error_code = error_code
