from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from docs101.client import Docs101Client


class CustomerResource:
    """Manage customers and their addresses."""

    def __init__(self, client: "Docs101Client") -> None:
        self._client = client

    # -- Customers ------------------------------------------------------------

    def list(self) -> List[Dict[str, Any]]:
        """Return all customers."""
        return self._client._request("GET", "/customer/")

    def create(
        self,
        *,
        organization_name: Optional[str] = None,
        email: Optional[str] = None,
        contact_type: Optional[str] = None,
        vat_id: Optional[str] = None,
        language: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        salutation: Optional[str] = None,
        payment_term_id: Optional[int] = None,
        default_ftl_template_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a new customer. Returns ``{"message": "...", "id": <int>}``."""
        body: Dict[str, Any] = {
            "organization_name": organization_name,
            "email": email,
            "contact_type": contact_type,
            "vat_id": vat_id,
            "language": language,
            "first_name": first_name,
            "last_name": last_name,
            "salutation": salutation,
            "payment_term_id": payment_term_id,
            "default_ftl_template_id": default_ftl_template_id,
            "is_active": is_active,
        }
        body.update(kwargs)
        return self._client._request("POST", "/customer/", data=body)

    def get(self, customer_id: int) -> Dict[str, Any]:
        """Return a single customer."""
        return self._client._request("GET", f"/customer/{customer_id}")

    def update(self, customer_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update a customer. Pass only the fields to change."""
        return self._client._request("PUT", f"/customer/{customer_id}", data=kwargs)

    # -- Addresses ------------------------------------------------------------

    def list_addresses(self, customer_id: int) -> List[Dict[str, Any]]:
        """Return all addresses for a customer."""
        return self._client._request("GET", f"/customer/{customer_id}/addresses")

    def create_address(
        self,
        customer_id: int,
        *,
        address_line_1: str,
        city: str,
        country_code: str,
        company: Optional[str] = None,
        address_line_2: Optional[str] = None,
        postal_code: Optional[str] = None,
        state_province: Optional[str] = None,
        is_default: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Add an address to a customer."""
        body: Dict[str, Any] = {
            "address_line_1": address_line_1,
            "city": city,
            "country_code": country_code,
            "company": company,
            "address_line_2": address_line_2,
            "postal_code": postal_code,
            "state_province": state_province,
            "is_default": is_default,
        }
        body.update(kwargs)
        return self._client._request(
            "POST", f"/customer/{customer_id}/addresses", data=body
        )

    def get_address(
        self, customer_id: int, address_id: int
    ) -> Dict[str, Any]:
        """Return a single address."""
        return self._client._request(
            "GET", f"/customer/{customer_id}/addresses/{address_id}"
        )

    def update_address(
        self, customer_id: int, address_id: int, **kwargs: Any
    ) -> Dict[str, Any]:
        """Update an address. Pass only the fields to change."""
        return self._client._request(
            "PUT", f"/customer/{customer_id}/addresses/{address_id}", data=kwargs
        )

    def delete_address(
        self, customer_id: int, address_id: int
    ) -> Dict[str, Any]:
        """Delete an address."""
        return self._client._request(
            "DELETE", f"/customer/{customer_id}/addresses/{address_id}"
        )
