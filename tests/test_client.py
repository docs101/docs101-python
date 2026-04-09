import pytest
import responses

from docs101 import (
    AuthenticationError,
    Docs101Client,
    Docs101Error,
    LimitExceededError,
    NotFoundError,
    ValidationError,
    VatOverrideRequiredError,
)

BASE = "https://docs101.com/api/v1"


class TestClientInit:
    def test_default_base_url(self):
        c = Docs101Client(api_key="ak_test")
        assert c.base_url == "https://docs101.com/api/v1"

    def test_custom_base_url_strips_trailing_slash(self):
        c = Docs101Client(api_key="ak_test", base_url="https://staging.example.com/api/v1/")
        assert c.base_url == "https://staging.example.com/api/v1"

    def test_session_headers(self):
        c = Docs101Client(api_key="ak_test")
        assert c._session.headers["X-API-Key"] == "ak_test"

    def test_resources_attached(self):
        c = Docs101Client(api_key="ak_test")
        assert c.customers is not None
        assert c.invoices is not None
        assert c.templates is not None
        assert c.exports is not None
        assert c.downloads is not None


class TestErrorHandling:
    @responses.activate
    def test_401_raises_authentication_error(self, client):
        responses.add(responses.GET, f"{BASE}/template/", json={"message": "Invalid API key"}, status=401)
        with pytest.raises(AuthenticationError) as exc_info:
            client.templates.list()
        assert exc_info.value.status_code == 401

    @responses.activate
    def test_400_raises_validation_error(self, client):
        responses.add(responses.POST, f"{BASE}/customer/", json={"message": "email required"}, status=400)
        with pytest.raises(ValidationError) as exc_info:
            client.customers.create()
        assert exc_info.value.status_code == 400

    @responses.activate
    def test_404_raises_not_found_error(self, client):
        responses.add(responses.GET, f"{BASE}/customer/999", json={"message": "Not found"}, status=404)
        with pytest.raises(NotFoundError) as exc_info:
            client.customers.get(999)
        assert exc_info.value.status_code == 404

    @responses.activate
    def test_402_raises_limit_exceeded_error(self, client):
        body = {
            "message": "Invoice limit reached",
            "error_code": "INVOICE_LIMIT_REACHED",
            "used": 10,
            "limit": 10,
            "reset_date": "2026-05-01",
        }
        responses.add(responses.POST, f"{BASE}/invoice/1/job", json=body, status=402)
        with pytest.raises(LimitExceededError) as exc_info:
            client.invoices.finalize(1)
        err = exc_info.value
        assert err.status_code == 402
        assert err.used == 10
        assert err.limit == 10
        assert err.reset_date == "2026-05-01"

    @responses.activate
    def test_422_vat_override_raises_specific_error(self, client):
        body = {"message": "VAT ID invalid", "code": "VAT_OVERRIDE_REQUIRED"}
        responses.add(responses.POST, f"{BASE}/invoice/1/job", json=body, status=422)
        with pytest.raises(VatOverrideRequiredError):
            client.invoices.finalize(1)

    @responses.activate
    def test_422_generic_raises_validation_error(self, client):
        body = {"message": "Unprocessable entity"}
        responses.add(responses.POST, f"{BASE}/customer/", json=body, status=422)
        with pytest.raises(ValidationError):
            client.customers.create()

    @responses.activate
    def test_500_raises_docs101_error(self, client):
        responses.add(responses.GET, f"{BASE}/template/", json={"message": "Internal error"}, status=500)
        with pytest.raises(Docs101Error) as exc_info:
            client.templates.list()
        assert exc_info.value.status_code == 500
