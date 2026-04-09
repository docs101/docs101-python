from typing import Any, Dict, Optional, Union

import requests

from docs101.exceptions import (
    AuthenticationError,
    Docs101Error,
    LimitExceededError,
    NotFoundError,
    ValidationError,
    VatOverrideRequiredError,
)
from docs101.resources.customers import CustomerResource
from docs101.resources.downloads import DownloadResource
from docs101.resources.exports import ExportResource
from docs101.resources.invoices import InvoiceResource
from docs101.resources.templates import TemplateResource

DEFAULT_BASE_URL = "https://docs101.com/api/v1"


class Docs101Client:
    """High-level client for the docs101 REST API.

    Usage::

        from docs101 import Docs101Client

        client = Docs101Client(api_key="ak_live_...")
        customers = client.customers.list()
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        self.customers = CustomerResource(self)
        self.invoices = InvoiceResource(self)
        self.templates = TemplateResource(self)
        self.exports = ExportResource(self)
        self.downloads = DownloadResource(self)

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        raw: bool = False,
    ) -> Union[Dict[str, Any], bytes]:
        """Send an HTTP request and return the parsed response.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API path (e.g. ``/customer/``).
            data: JSON request body.
            params: URL query parameters.
            raw: If ``True``, return raw bytes instead of parsed JSON.

        Returns:
            Parsed JSON as a dict/list, or raw bytes when *raw* is True.

        Raises:
            AuthenticationError: On 401.
            ValidationError: On 400.
            NotFoundError: On 404.
            LimitExceededError: On 402.
            VatOverrideRequiredError: On 422 with VAT override code.
            Docs101Error: On any other HTTP error.
        """
        url = self.base_url + path

        response = self._session.request(
            method,
            url,
            json=data,
            params=params,
            timeout=self.timeout,
        )

        if response.ok:
            if raw:
                return response.content
            return response.json()

        # Try to parse error body
        try:
            body = response.json()
        except ValueError:
            body = {}

        message = body.get("message") or body.get("error") or response.text
        status_code = response.status_code

        if status_code == 401:
            raise AuthenticationError(
                message, status_code=status_code, response=body
            )

        if status_code == 400:
            raise ValidationError(
                message, status_code=status_code, response=body
            )

        if status_code == 404:
            raise NotFoundError(
                message, status_code=status_code, response=body
            )

        if status_code == 402:
            raise LimitExceededError(
                message,
                status_code=status_code,
                response=body,
                used=body.get("used", 0),
                limit=body.get("limit", 0),
                reset_date=body.get("reset_date", ""),
            )

        if status_code == 422:
            error_code = body.get("code") or body.get("error_code", "")
            if error_code == "VAT_OVERRIDE_REQUIRED":
                raise VatOverrideRequiredError(
                    message, status_code=status_code, response=body
                )
            raise ValidationError(
                message, status_code=status_code, response=body
            )

        raise Docs101Error(message, status_code=status_code, response=body)
