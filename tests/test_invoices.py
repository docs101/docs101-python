import json

import pytest
import responses

from docs101 import Docs101TimeoutError, JobFailedError, LimitExceededError, VatOverrideRequiredError

BASE = "https://docs101.com/api/v1"


class TestInvoiceCRUD:
    @responses.activate
    def test_list(self, client):
        data = {"invoices": [], "total": 0}
        responses.add(responses.GET, f"{BASE}/invoice/", json=data, status=200)
        result = client.invoices.list(page=1, limit=10)
        assert "invoices" in result
        assert "page=1" in responses.calls[0].request.url
        assert "limit=10" in responses.calls[0].request.url

    @responses.activate
    def test_create(self, client):
        resp = {"message": "Invoice created", "invoice_id": 17}
        responses.add(responses.POST, f"{BASE}/invoice/", json=resp, status=201)
        result = client.invoices.create(
            customer_id=42,
            benefit_period_start="2026-04-01",
            benefit_period_end="2026-04-30",
            invoice_format="ZUGFERD",
        )
        assert result["invoice_id"] == 17
        body = json.loads(responses.calls[0].request.body)
        assert body["customer_id"] == 42
        assert body["invoice_format"] == "ZUGFERD"

    @responses.activate
    def test_get(self, client):
        data = {"id": 17, "status": "DRAFT"}
        responses.add(responses.GET, f"{BASE}/invoice/17", json=data, status=200)
        assert client.invoices.get(17)["status"] == "DRAFT"

    @responses.activate
    def test_update(self, client):
        resp = {"message": "Invoice updated"}
        responses.add(responses.PUT, f"{BASE}/invoice/17", json=resp, status=200)
        client.invoices.update(17, invoice_format="PDF")
        body = json.loads(responses.calls[0].request.body)
        assert body["invoice_format"] == "PDF"

    @responses.activate
    def test_duplicate(self, client):
        resp = {"message": "Duplicated", "invoice_id": 18}
        responses.add(responses.POST, f"{BASE}/invoice/17/duplicate", json=resp, status=201)
        result = client.invoices.duplicate(17)
        assert result["invoice_id"] == 18

    @responses.activate
    def test_cancel(self, client):
        resp = {"message": "Invoice cancelled"}
        responses.add(responses.POST, f"{BASE}/invoice/17/cancel", json=resp, status=200)
        result = client.invoices.cancel(17)
        assert result["message"] == "Invoice cancelled"


class TestPositions:
    @responses.activate
    def test_list_positions(self, client):
        data = {"positions": [{"id": 1, "title": "Item"}]}
        responses.add(responses.GET, f"{BASE}/invoice/17/positions", json=data, status=200)
        result = client.invoices.list_positions(17)
        assert len(result["positions"]) == 1

    @responses.activate
    def test_add_position(self, client):
        resp = {"message": "Position added"}
        responses.add(responses.POST, f"{BASE}/invoice/17/positions", json=resp, status=201)
        client.invoices.add_position(
            17,
            title="Pro Plan",
            quantity=1.0,
            unit_id="HUR",
            unit_net_amount=25.00,
            single_net_amount=25.00,
            tax_rate=0.19,
            tax_treatment_id="standard",
        )
        body = json.loads(responses.calls[0].request.body)
        assert body["title"] == "Pro Plan"
        assert body["tax_rate"] == 0.19

    @responses.activate
    def test_get_position(self, client):
        data = {"id": 1, "title": "Item"}
        responses.add(responses.GET, f"{BASE}/invoice/17/position/1", json=data, status=200)
        assert client.invoices.get_position(17, 1)["title"] == "Item"

    @responses.activate
    def test_update_position(self, client):
        resp = {"message": "Position updated"}
        responses.add(responses.PUT, f"{BASE}/invoice/17/position/1", json=resp, status=200)
        client.invoices.update_position(17, 1, title="Updated")
        body = json.loads(responses.calls[0].request.body)
        assert body["title"] == "Updated"

    @responses.activate
    def test_delete_position(self, client):
        resp = {"message": "Position deleted"}
        responses.add(responses.DELETE, f"{BASE}/invoice/17/position/1", json=resp, status=200)
        result = client.invoices.delete_position(17, 1)
        assert result["message"] == "Position deleted"


class TestValidation:
    @responses.activate
    def test_validate(self, client):
        data = {"valid": True, "errors": [], "checks": []}
        responses.add(responses.GET, f"{BASE}/invoice/17/validate", json=data, status=200)
        result = client.invoices.validate(17)
        assert result["valid"] is True

    @responses.activate
    def test_preview_returns_bytes(self, client):
        pdf_bytes = b"%PDF-1.4 fake content"
        responses.add(responses.GET, f"{BASE}/invoice/17/preview", body=pdf_bytes, status=200)
        result = client.invoices.preview(17)
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")


class TestFinalize:
    @responses.activate
    def test_finalize_happy_path(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/invoice/17/job",
            json={"message": "Job started", "job_id": "abc123"},
            status=201,
        )
        responses.add(
            responses.GET,
            f"{BASE}/invoice/17/job/abc123",
            json={"message": "Queued", "status": "queued"},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{BASE}/invoice/17/job/abc123",
            json={"message": "Started", "status": "started"},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{BASE}/invoice/17/job/abc123",
            json={"message": "Done", "status": "finished"},
            status=200,
        )

        result = client.invoices.finalize(17, poll_interval=0.1, timeout=5)
        assert result["status"] == "finished"
        assert len(responses.calls) == 4  # 1 POST + 3 GET

    @responses.activate
    def test_finalize_job_failed(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/invoice/17/job",
            json={"message": "Job started", "job_id": "abc123"},
            status=201,
        )
        responses.add(
            responses.GET,
            f"{BASE}/invoice/17/job/abc123",
            json={"message": "Failed", "status": "failed", "error_message": "PDF generation error"},
            status=200,
        )

        with pytest.raises(JobFailedError) as exc_info:
            client.invoices.finalize(17, poll_interval=0.1)
        assert "PDF generation error" in str(exc_info.value)
        assert exc_info.value.error_message == "PDF generation error"

    @responses.activate
    def test_finalize_timeout(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/invoice/17/job",
            json={"message": "Job started", "job_id": "abc123"},
            status=201,
        )
        # Always return queued
        responses.add(
            responses.GET,
            f"{BASE}/invoice/17/job/abc123",
            json={"message": "Queued", "status": "queued"},
            status=200,
        )

        with pytest.raises(Docs101TimeoutError):
            client.invoices.finalize(17, timeout=0.5, poll_interval=0.3)

    @responses.activate
    def test_finalize_402_limit(self, client):
        body = {
            "message": "Limit reached",
            "error_code": "INVOICE_LIMIT_REACHED",
            "used": 10,
            "limit": 10,
            "reset_date": "2026-05-01",
        }
        responses.add(responses.POST, f"{BASE}/invoice/17/job", json=body, status=402)
        with pytest.raises(LimitExceededError) as exc_info:
            client.invoices.finalize(17)
        assert exc_info.value.used == 10

    @responses.activate
    def test_finalize_422_vat_override(self, client):
        body = {"message": "VAT invalid", "code": "VAT_OVERRIDE_REQUIRED"}
        responses.add(responses.POST, f"{BASE}/invoice/17/job", json=body, status=422)
        with pytest.raises(VatOverrideRequiredError):
            client.invoices.finalize(17)

    @responses.activate
    def test_finalize_with_vat_override_confirmed(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/invoice/17/job",
            json={"message": "Job started", "job_id": "abc123"},
            status=201,
        )
        responses.add(
            responses.GET,
            f"{BASE}/invoice/17/job/abc123",
            json={"message": "Done", "status": "finished"},
            status=200,
        )

        client.invoices.finalize(17, vat_override_confirmed=True, poll_interval=0.1)
        body = json.loads(responses.calls[0].request.body)
        assert body["vat_override_confirmed"] is True


class TestStatus:
    @responses.activate
    def test_mark_as_sent(self, client):
        resp = {"message": "Status updated"}
        responses.add(responses.PUT, f"{BASE}/invoice/17/status", json=resp, status=200)
        client.invoices.mark_as_sent(17)
        body = json.loads(responses.calls[0].request.body)
        assert body["status"] == "SENT"

    @responses.activate
    def test_mark_as_paid(self, client):
        resp = {"message": "Status updated"}
        responses.add(responses.PUT, f"{BASE}/invoice/17/status", json=resp, status=200)
        client.invoices.mark_as_paid(
            17,
            paid_date="2026-04-15",
            payment_method="BANK_TRANSFER",
            payment_reference="SEPA-123",
        )
        body = json.loads(responses.calls[0].request.body)
        assert body["status"] == "PAID"
        assert body["paid_date"] == "2026-04-15"
        assert body["payment_reference"] == "SEPA-123"


class TestDownloadLinks:
    @responses.activate
    def test_get_pdf_url(self, client):
        data = {"url": "https://cdn.example.com/inv.pdf", "filename": "INV-001.pdf"}
        responses.add(responses.GET, f"{BASE}/invoice/17/pdf-link", json=data, status=200)
        result = client.invoices.get_pdf_url(17)
        assert result["filename"] == "INV-001.pdf"

    @responses.activate
    def test_get_xml_url(self, client):
        data = {"url": "https://cdn.example.com/inv.xml", "filename": "INV-001.xml"}
        responses.add(responses.GET, f"{BASE}/invoice/17/xml-link", json=data, status=200)
        result = client.invoices.get_xml_url(17)
        assert result["filename"] == "INV-001.xml"


class TestTaxTreatments:
    @responses.activate
    def test_get_tax_treatments(self, client):
        data = [{"id": "standard", "label": "Standard"}]
        responses.add(responses.GET, f"{BASE}/invoice/tax-treatments", json=data, status=200)
        result = client.invoices.get_tax_treatments(locale="de")
        assert len(result) == 1
        assert "locale=de" in responses.calls[0].request.url
