from typing import TYPE_CHECKING, Any, Dict

from docs101._polling import poll_job
from docs101.exceptions import JobFailedError

if TYPE_CHECKING:
    from docs101.client import Docs101Client


class ExportResource:
    """DATEV configuration and export jobs."""

    def __init__(self, client: "Docs101Client") -> None:
        self._client = client

    # -- DATEV Configuration --------------------------------------------------

    def get_datev_config(self) -> Dict[str, Any]:
        """Return the current DATEV configuration."""
        return self._client._request("GET", "/datev/config")

    def configure_datev(
        self,
        *,
        consultant_number: int,
        client_number: int,
        chart_of_accounts: str = "SKR03",
        fiscal_year_start_month: int = 1,
    ) -> Dict[str, Any]:
        """Update the DATEV configuration."""
        body = {
            "consultant_number": consultant_number,
            "client_number": client_number,
            "chart_of_accounts": chart_of_accounts,
            "fiscal_year_start_month": fiscal_year_start_month,
        }
        return self._client._request("PUT", "/datev/config", data=body)

    # -- Export Jobs -----------------------------------------------------------

    def create_datev(
        self,
        *,
        start_date: str,
        end_date: str,
        include_master_data: bool = True,
        include_documents: bool = True,
        only_new: bool = True,
        timeout: float = 120,
        poll_interval: float = 3,
    ) -> Dict[str, Any]:
        """Start a DATEV export job and poll until complete.

        Returns:
            The ``result`` object from the finished job containing
            ``download_ids``, ``is_split``, ``total_invoice_count``, etc.

        Raises:
            JobFailedError: If the job fails or the result contains an error.
            Docs101TimeoutError: If polling exceeds *timeout* seconds.
        """
        body = {
            "task": "process_datev_export_job",
            "start_date": start_date,
            "end_date": end_date,
            "include_master_data": include_master_data,
            "include_documents": include_documents,
            "only_new": only_new,
        }
        result = self._client._request("POST", "/exports/job", data=body)
        job_id = result["job_id"]

        response = poll_job(
            self._client._request,
            f"/exports/job/{job_id}",
            timeout=timeout,
            poll_interval=poll_interval,
        )

        job_result = response.get("result", {})

        if isinstance(job_result, dict) and job_result.get("error"):
            error_info = job_result["error"]
            error_msg = (
                error_info.get("message", "Export failed")
                if isinstance(error_info, dict)
                else str(error_info)
            )
            raise JobFailedError(
                error_msg,
                response=response,
                error_message=error_msg,
            )

        return job_result
