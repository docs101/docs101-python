from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from docs101.client import Docs101Client


class DownloadResource:
    """Manage file downloads."""

    def __init__(self, client: "Docs101Client") -> None:
        self._client = client

    def list(self) -> List[Dict[str, Any]]:
        """Return all available downloads."""
        return self._client._request("GET", "/downloads/")

    def get_url(self, download_id: int) -> Dict[str, Any]:
        """Return the presigned download URL for *download_id*."""
        return self._client._request("GET", f"/downloads/{download_id}/download")

    def delete(self, download_id: int) -> Dict[str, Any]:
        """Delete a download."""
        return self._client._request("DELETE", f"/downloads/{download_id}")
