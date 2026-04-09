from typing import TYPE_CHECKING, Any, Dict, List, Optional

from docs101._polling import poll_job

if TYPE_CHECKING:
    from docs101.client import Docs101Client


class InvoiceResource:
    """Manage invoices, positions, validation, finalization, and status."""

    def __init__(self, client: "Docs101Client") -> None:
        self._client = client

    # -- Invoice CRUD ---------------------------------------------------------

    def list(
        self, *, page: int = 1, limit: int = 25
    ) -> Dict[str, Any]:
        """Return a paginated list of invoices."""
        return self._client._request(
            "GET", "/invoice/", params={"page": page, "limit": limit}
        )

    def create(
        self,
        *,
        customer_id: int,
        benefit_period_start: Optional[str] = None,
        benefit_period_end: Optional[str] = None,
        invoice_format: Optional[str] = None,
        invoice_number: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a new invoice. Returns ``{"message": "...", "invoice_id": <int>}``."""
        body: Dict[str, Any] = {
            "customer_id": customer_id,
            "benefit_period_start": benefit_period_start,
            "benefit_period_end": benefit_period_end,
            "invoice_format": invoice_format,
            "invoice_number": invoice_number,
            "meta": meta,
        }
        body.update(kwargs)
        return self._client._request("POST", "/invoice/", data=body)

    def get(self, invoice_id: int) -> Dict[str, Any]:
        """Return a single invoice."""
        return self._client._request("GET", f"/invoice/{invoice_id}")

    def update(self, invoice_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update an invoice. Pass only the fields to change."""
        return self._client._request("PUT", f"/invoice/{invoice_id}", data=kwargs)

    def duplicate(self, invoice_id: int) -> Dict[str, Any]:
        """Duplicate an invoice. Returns the new invoice ID."""
        return self._client._request("POST", f"/invoice/{invoice_id}/duplicate")

    def cancel(self, invoice_id: int) -> Dict[str, Any]:
        """Cancel an invoice."""
        return self._client._request("POST", f"/invoice/{invoice_id}/cancel")

    # -- Positions ------------------------------------------------------------

    def list_positions(self, invoice_id: int) -> Dict[str, Any]:
        """Return all positions for an invoice."""
        return self._client._request("GET", f"/invoice/{invoice_id}/positions")

    def add_position(
        self,
        invoice_id: int,
        *,
        title: str,
        quantity: float,
        unit_id: str,
        unit_net_amount: float,
        single_net_amount: float,
        description: Optional[str] = None,
        tax_rate: Optional[float] = None,
        tax_treatment_id: Optional[str] = None,
        discount_type: Optional[str] = None,
        discount_value: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Add a position to an invoice."""
        body: Dict[str, Any] = {
            "title": title,
            "quantity": quantity,
            "unit_id": unit_id,
            "unit_net_amount": unit_net_amount,
            "single_net_amount": single_net_amount,
            "description": description,
            "tax_rate": tax_rate,
            "tax_treatment_id": tax_treatment_id,
            "discount_type": discount_type,
            "discount_value": discount_value,
        }
        body.update(kwargs)
        return self._client._request(
            "POST", f"/invoice/{invoice_id}/positions", data=body
        )

    def get_position(
        self, invoice_id: int, position_id: int
    ) -> Dict[str, Any]:
        """Return a single position."""
        return self._client._request(
            "GET", f"/invoice/{invoice_id}/position/{position_id}"
        )

    def update_position(
        self, invoice_id: int, position_id: int, **kwargs: Any
    ) -> Dict[str, Any]:
        """Update a position. Pass only the fields to change."""
        return self._client._request(
            "PUT", f"/invoice/{invoice_id}/position/{position_id}", data=kwargs
        )

    def delete_position(
        self, invoice_id: int, position_id: int
    ) -> Dict[str, Any]:
        """Delete a position."""
        return self._client._request(
            "DELETE", f"/invoice/{invoice_id}/position/{position_id}"
        )

    # -- Validation & Preview -------------------------------------------------

    def validate(self, invoice_id: int) -> Dict[str, Any]:
        """Validate an invoice before finalization."""
        return self._client._request("GET", f"/invoice/{invoice_id}/validate")

    def preview(self, invoice_id: int) -> bytes:
        """Return a preview PDF as raw bytes."""
        return self._client._request(
            "GET", f"/invoice/{invoice_id}/preview", raw=True
        )

    # -- Finalization ---------------------------------------------------------

    def finalize(
        self,
        invoice_id: int,
        *,
        timeout: float = 60,
        poll_interval: float = 2,
        vat_override_confirmed: bool = False,
    ) -> Dict[str, Any]:
        """Start the finalization job and poll until complete.

        Raises:
            LimitExceededError: If the monthly invoice limit is reached (402).
            VatOverrideRequiredError: If VAT override is needed (422).
            JobFailedError: If the job fails.
            Docs101TimeoutError: If polling exceeds *timeout* seconds.
        """
        body: Dict[str, Any] = {"task": "process_invoice_flag_invoice_send_job"}
        if vat_override_confirmed:
            body["vat_override_confirmed"] = True

        result = self._client._request(
            "POST", f"/invoice/{invoice_id}/job", data=body
        )
        job_id = result["job_id"]

        return poll_job(
            self._client._request,
            f"/invoice/{invoice_id}/job/{job_id}",
            timeout=timeout,
            poll_interval=poll_interval,
        )

    # -- Status ---------------------------------------------------------------

    def mark_as_sent(self, invoice_id: int) -> Dict[str, Any]:
        """Mark an invoice as sent."""
        return self._client._request(
            "PUT", f"/invoice/{invoice_id}/status", data={"status": "SENT"}
        )

    def mark_as_paid(
        self,
        invoice_id: int,
        *,
        paid_date: str,
        payment_method: str,
        payment_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mark an invoice as paid."""
        body: Dict[str, Any] = {
            "status": "PAID",
            "paid_date": paid_date,
            "payment_method": payment_method,
        }
        if payment_reference is not None:
            body["payment_reference"] = payment_reference
        return self._client._request(
            "PUT", f"/invoice/{invoice_id}/status", data=body
        )

    # -- Downloads ------------------------------------------------------------

    def get_pdf_url(self, invoice_id: int) -> Dict[str, Any]:
        """Return the PDF download URL and filename."""
        return self._client._request("GET", f"/invoice/{invoice_id}/pdf-link")

    def get_xml_url(self, invoice_id: int) -> Dict[str, Any]:
        """Return the XML download URL and filename."""
        return self._client._request("GET", f"/invoice/{invoice_id}/xml-link")

    # -- Tax Treatments -------------------------------------------------------

    def get_tax_treatments(self, *, locale: str = "en") -> List[Dict[str, Any]]:
        """Return available tax treatments."""
        return self._client._request(
            "GET", "/invoice/tax-treatments", params={"locale": locale}
        )
