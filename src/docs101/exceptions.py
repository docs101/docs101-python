from typing import Any, Dict, Optional


class Docs101Error(Exception):
    """Base exception for all docs101 API errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(Docs101Error):
    """Raised on 401 Unauthorized."""


class ValidationError(Docs101Error):
    """Raised on 400 Bad Request."""


class NotFoundError(Docs101Error):
    """Raised on 404 Not Found."""


class LimitExceededError(Docs101Error):
    """Raised on 402 when the monthly invoice limit is reached."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        used: int = 0,
        limit: int = 0,
        reset_date: str = "",
    ) -> None:
        super().__init__(message, status_code=status_code, response=response)
        self.used = used
        self.limit = limit
        self.reset_date = reset_date


class VatOverrideRequiredError(Docs101Error):
    """Raised on 422 when the customer VAT ID is invalid and override is needed."""


class JobFailedError(Docs101Error):
    """Raised when an async job finishes with status 'failed'."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        error_message: str = "",
    ) -> None:
        super().__init__(message, status_code=status_code, response=response)
        self.error_message = error_message


class Docs101TimeoutError(Docs101Error):
    """Raised when polling for a job exceeds the timeout."""
