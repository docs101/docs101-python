import json

import responses

BASE = "https://docs101.com/api/v1"


class TestCustomerResource:
    @responses.activate
    def test_list(self, client):
        data = [{"id": 1, "organization_name": "Acme"}]
        responses.add(responses.GET, f"{BASE}/customer/", json=data, status=200)
        result = client.customers.list()
        assert result == data

    @responses.activate
    def test_create(self, client):
        resp = {"message": "Customer created", "id": 42}
        responses.add(responses.POST, f"{BASE}/customer/", json=resp, status=201)
        result = client.customers.create(
            organization_name="Acme Corp",
            email="billing@acme.com",
            contact_type="B2B",
        )
        assert result["id"] == 42
        body = json.loads(responses.calls[0].request.body)
        assert body["organization_name"] == "Acme Corp"
        assert body["contact_type"] == "B2B"

    @responses.activate
    def test_get(self, client):
        data = {"id": 42, "organization_name": "Acme"}
        responses.add(responses.GET, f"{BASE}/customer/42", json=data, status=200)
        result = client.customers.get(42)
        assert result["id"] == 42

    @responses.activate
    def test_update(self, client):
        resp = {"message": "Customer updated"}
        responses.add(responses.PUT, f"{BASE}/customer/42", json=resp, status=200)
        result = client.customers.update(42, email="new@acme.com")
        body = json.loads(responses.calls[0].request.body)
        assert body["email"] == "new@acme.com"
        assert result["message"] == "Customer updated"


class TestCustomerAddresses:
    @responses.activate
    def test_list_addresses(self, client):
        data = [{"id": 1, "city": "Berlin"}]
        responses.add(responses.GET, f"{BASE}/customer/42/addresses", json=data, status=200)
        result = client.customers.list_addresses(42)
        assert result == data

    @responses.activate
    def test_create_address(self, client):
        resp = {"message": "Address created"}
        responses.add(responses.POST, f"{BASE}/customer/42/addresses", json=resp, status=201)
        result = client.customers.create_address(
            42,
            address_line_1="Musterstraße 1",
            city="Berlin",
            country_code="DE",
            is_default=True,
        )
        body = json.loads(responses.calls[0].request.body)
        assert body["address_line_1"] == "Musterstraße 1"
        assert body["country_code"] == "DE"
        assert body["is_default"] is True
        assert result["message"] == "Address created"

    @responses.activate
    def test_get_address(self, client):
        data = {"id": 1, "city": "Berlin"}
        responses.add(responses.GET, f"{BASE}/customer/42/addresses/1", json=data, status=200)
        result = client.customers.get_address(42, 1)
        assert result["city"] == "Berlin"

    @responses.activate
    def test_update_address(self, client):
        resp = {"message": "Address updated"}
        responses.add(responses.PUT, f"{BASE}/customer/42/addresses/1", json=resp, status=200)
        result = client.customers.update_address(42, 1, city="Munich")
        body = json.loads(responses.calls[0].request.body)
        assert body["city"] == "Munich"
        assert result["message"] == "Address updated"

    @responses.activate
    def test_delete_address(self, client):
        resp = {"message": "Address deleted"}
        responses.add(responses.DELETE, f"{BASE}/customer/42/addresses/1", json=resp, status=200)
        result = client.customers.delete_address(42, 1)
        assert result["message"] == "Address deleted"
