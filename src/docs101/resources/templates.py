from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from docs101.client import Docs101Client


class TemplateResource:
    """Access invoice templates."""

    def __init__(self, client: "Docs101Client") -> None:
        self._client = client

    def list(self) -> List[Dict[str, Any]]:
        """Return all templates."""
        return self._client._request("GET", "/template/")

    def get(self, template_id: int) -> Dict[str, Any]:
        """Return a single template by ID."""
        return self._client._request("GET", f"/template/{template_id}")
