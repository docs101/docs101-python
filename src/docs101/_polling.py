import time
from typing import Any, Callable, Dict

from docs101.exceptions import Docs101TimeoutError, JobFailedError


def poll_job(
    request_fn: Callable[..., Dict[str, Any]],
    status_path: str,
    *,
    timeout: float = 60,
    poll_interval: float = 2,
) -> Dict[str, Any]:
    """Poll an async job until it reaches a terminal state.

    Args:
        request_fn: The client's ``_request`` method.
        status_path: API path to query for job status.
        timeout: Maximum seconds to wait before raising timeout.
        poll_interval: Seconds between status checks.

    Returns:
        The full response dict when the job reaches ``finished``.

    Raises:
        JobFailedError: If the job status is ``failed``.
        Docs101TimeoutError: If *timeout* seconds elapse without completion.
    """
    start = time.monotonic()

    while True:
        response = request_fn("GET", status_path)
        status = response.get("status")

        if status == "finished":
            return response

        if status == "failed":
            error_msg = response.get("error_message", "Job failed")
            raise JobFailedError(
                error_msg,
                response=response,
                error_message=error_msg,
            )

        elapsed = time.monotonic() - start
        if elapsed + poll_interval > timeout:
            raise Docs101TimeoutError(
                f"Job did not complete within {timeout}s (last status: {status})",
            )

        time.sleep(poll_interval)
