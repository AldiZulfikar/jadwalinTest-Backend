from typing import Any, Optional


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(self, message: str, status_code: int = 400, data: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data


class BusinessLogicException(AppException):
    """Raised when business logic rules are violated."""

    def __init__(self, message: str = "Business logic validation failed."):
        super().__init__(message=message, status_code=400)


class ResourceNotFoundException(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found."):
        super().__init__(message=message, status_code=404)


class BookingOverlapException(AppException):
    """Raised when a booking schedule conflicts with an existing reservation."""

    def __init__(self, message: str = "Booking schedule overlaps with existing reservation."):
        super().__init__(message=message, status_code=409)


class BookingNotFoundException(AppException):
    """Raised when a requested booking ID does not exist or has been soft deleted."""

    def __init__(self, message: str = "Booking not found."):
        super().__init__(message=message, status_code=404)


class EnvironmentNotFoundException(AppException):
    """Raised when a specified environment_id does not exist."""

    def __init__(self, message: str = "Environment not found or inactive."):
        super().__init__(message=message, status_code=404)


class InvalidBookingStateException(AppException):
    """Raised when an invalid state transition is requested."""

    def __init__(self, message: str = "Invalid booking state transition."):
        super().__init__(message=message, status_code=422)


class EmailServiceException(AppException):
    """Raised when email delivery fails."""

    def __init__(self, message: str = "Failed to send email notification."):
        super().__init__(message=message, status_code=500)
