import json

import pytest
import responses

from docs101 import Docs101TimeoutError, JobFailedError

BASE = "https://docs101.com/api/v1"


class TestDatevConfig:
    @responses.activate
    def test_get_datev_config(self, client):
        data = {"consultant_number": 1234567, "client_number": 12345}
        responses.add(responses.GET, f"{BASE}/datev/config", json=data, status=200)
        result = client.exports.get_datev_config()
        assert result["consultant_number"] == 1234567

    @responses.activate
    def test_configure_datev(self, client):
        resp = {"message": "Config updated"}
        responses.add(responses.PUT, f"{BASE}/datev/config", json=resp, status=200)
        client.exports.configure_datev(
            consultant_number=1234567,
            client_number=12345,
            chart_of_accounts="SKR03",
        )
        body = json.loads(responses.calls[0].request.body)
        assert body["consultant_number"] == 1234567
        assert body["chart_of_accounts"] == "SKR03"


class TestDatevExport:
    @responses.activate
    def test_create_datev_happy_path(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/exports/job",
            json={"message": "Job started", "job_id": "exp-123"},
            status=201,
        )
        responses.add(
            responses.GET,
            f"{BASE}/exports/job/exp-123",
            json={"message": "Queued", "status": "queued"},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{BASE}/exports/job/exp-123",
            json={
                "message": "Done",
                "status": "finished",
                "result": {
                    "download_ids": [1, 2],
                    "is_split": True,
                    "split_reason": "year_boundary",
                    "total_invoice_count": 42,
                },
            },
            status=200,
        )

        result = client.exports.create_datev(
            start_date="2026-01-01",
            end_date="2026-03-31",
            poll_interval=0.1,
            timeout=5,
        )
        assert result["download_ids"] == [1, 2]
        assert result["is_split"] is True
        assert result["total_invoice_count"] == 42

        body = json.loads(responses.calls[0].request.body)
        assert body["task"] == "process_datev_export_job"
        assert body["start_date"] == "2026-01-01"

    @responses.activate
    def test_create_datev_result_error(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/exports/job",
            json={"message": "Job started", "job_id": "exp-123"},
            status=201,
        )
        responses.add(
            responses.GET,
            f"{BASE}/exports/job/exp-123",
            json={
                "message": "Done",
                "status": "finished",
                "result": {
                    "error": {
                        "message": "No invoices found",
                        "error_code": "no_invoices_found",
                    }
                },
            },
            status=200,
        )

        with pytest.raises(JobFailedError) as exc_info:
            client.exports.create_datev(
                start_date="2026-01-01",
                end_date="2026-03-31",
                poll_interval=0.1,
            )
        assert "No invoices found" in str(exc_info.value)

    @responses.activate
    def test_create_datev_timeout(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/exports/job",
            json={"message": "Job started", "job_id": "exp-123"},
            status=201,
        )
        responses.add(
            responses.GET,
            f"{BASE}/exports/job/exp-123",
            json={"message": "Queued", "status": "queued"},
            status=200,
        )

        with pytest.raises(Docs101TimeoutError):
            client.exports.create_datev(
                start_date="2026-01-01",
                end_date="2026-03-31",
                timeout=0.5,
                poll_interval=0.3,
            )

    @responses.activate
    def test_create_datev_job_failed(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/exports/job",
            json={"message": "Job started", "job_id": "exp-123"},
            status=201,
        )
        responses.add(
            responses.GET,
            f"{BASE}/exports/job/exp-123",
            json={"message": "Failed", "status": "failed", "error_message": "Internal error"},
            status=200,
        )

        with pytest.raises(JobFailedError):
            client.exports.create_datev(
                start_date="2026-01-01",
                end_date="2026-03-31",
                poll_interval=0.1,
            )


class TestDownloadResource:
    @responses.activate
    def test_list_downloads(self, client):
        data = [{"id": 1, "filename": "export.zip"}]
        responses.add(responses.GET, f"{BASE}/downloads/", json=data, status=200)
        result = client.downloads.list()
        assert result[0]["id"] == 1

    @responses.activate
    def test_get_download_url(self, client):
        data = {"url": "https://s3.example.com/export.zip"}
        responses.add(responses.GET, f"{BASE}/downloads/1/download", json=data, status=200)
        result = client.downloads.get_url(1)
        assert "s3.example.com" in result["url"]

    @responses.activate
    def test_delete_download(self, client):
        resp = {"message": "Deleted"}
        responses.add(responses.DELETE, f"{BASE}/downloads/1", json=resp, status=200)
        result = client.downloads.delete(1)
        assert result["message"] == "Deleted"
