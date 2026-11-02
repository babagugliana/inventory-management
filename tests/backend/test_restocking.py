"""
Tests for restocking API endpoints (restock pricing on demand forecasts,
and creating/listing restocking orders).
"""
from datetime import datetime, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def reset_restocking_orders():
    """Restocking orders live in a module-level list; clear it so tests stay independent."""
    main.restocking_orders.clear()
    yield
    main.restocking_orders.clear()


def get_forecasts_by_sku(client):
    """Return demand forecasts keyed by SKU."""
    response = client.get("/api/demand")
    assert response.status_code == 200
    return {f["item_sku"]: f for f in response.json()}


class TestDemandForecastRestockFields:
    """Demand forecasts carry the pricing and lead time the Restocking tab needs."""

    def test_demand_forecasts_include_cost_and_lead_time(self, client):
        """Every forecast has a positive unit_cost and lead_time_days."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["lead_time_days"] > 0


class TestRestockingOrderEndpoints:
    """Test suite for /api/restocking-orders."""

    def test_get_restocking_orders_initially_empty(self, client):
        """No orders exist before any are placed."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restocking_order(self, client):
        """Placing an order returns the saved order with server-computed totals."""
        forecasts = get_forecasts_by_sku(client)
        widget = forecasts["WDG-001"]

        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [{"sku": "WDG-001", "quantity": 10}],
        })
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["budget"] == 100000
        assert len(order["items"]) == 1

        item = order["items"][0]
        assert item["sku"] == "WDG-001"
        assert item["name"] == widget["item_name"]
        assert item["quantity"] == 10
        assert item["unit_cost"] == widget["unit_cost"]
        assert abs(item["line_total"] - 10 * widget["unit_cost"]) < 0.01
        assert abs(order["total_cost"] - 10 * widget["unit_cost"]) < 0.01

    def test_create_restocking_order_ignores_client_prices(self, client):
        """The server prices items itself; a unit_cost sent by the client is ignored."""
        forecasts = get_forecasts_by_sku(client)

        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [{"sku": "WDG-001", "quantity": 10, "unit_cost": 0.01}],
        })
        assert response.status_code == 201
        assert response.json()["items"][0]["unit_cost"] == forecasts["WDG-001"]["unit_cost"]

    def test_restocking_order_lead_time_is_slowest_item(self, client):
        """Order lead time is the longest lead time among its items."""
        forecasts = get_forecasts_by_sku(client)
        skus = ["WDG-001", "MTR-304", "GSK-203"]

        response = client.post("/api/restocking-orders", json={
            "budget": 1000000,
            "items": [{"sku": sku, "quantity": 1} for sku in skus],
        })
        assert response.status_code == 201

        expected_lead = max(forecasts[sku]["lead_time_days"] for sku in skus)
        assert response.json()["lead_time_days"] == expected_lead

    def test_restocking_order_expected_delivery_calculation(self, client):
        """Expected delivery is order date plus lead time."""
        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [{"sku": "BRG-102", "quantity": 5}],
        })
        order = response.json()

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert expected_delivery - order_date == timedelta(days=order["lead_time_days"])

    def test_created_orders_listed_newest_first(self, client):
        """Placed orders appear in the list, newest first, with sequential numbers."""
        for sku in ["WDG-001", "GSK-203"]:
            response = client.post("/api/restocking-orders", json={
                "budget": 100000,
                "items": [{"sku": sku, "quantity": 1}],
            })
            assert response.status_code == 201

        response = client.get("/api/restocking-orders")
        assert response.status_code == 200

        data = response.json()
        assert [o["order_number"] for o in data] == ["RST-0002", "RST-0001"]
        assert data[0]["items"][0]["sku"] == "GSK-203"

    def test_create_restocking_order_over_budget(self, client):
        """An order costing more than the budget is rejected and not saved."""
        response = client.post("/api/restocking-orders", json={
            "budget": 1,
            "items": [{"sku": "MTR-304", "quantity": 10}],
        })
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restocking-orders").json() == []

    def test_create_restocking_order_unknown_sku(self, client):
        """An SKU that isn't in the demand forecast is rejected."""
        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [{"sku": "NOPE-999", "quantity": 1}],
        })
        assert response.status_code == 400
        assert "NOPE-999" in response.json()["detail"]

    def test_create_restocking_order_duplicate_sku(self, client):
        """The same SKU may only appear once per order."""
        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [{"sku": "WDG-001", "quantity": 1}, {"sku": "WDG-001", "quantity": 2}],
        })
        assert response.status_code == 400
        assert "duplicate" in response.json()["detail"].lower()

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_create_restocking_order_non_positive_quantity(self, client, quantity):
        """Quantities must be positive."""
        response = client.post("/api/restocking-orders", json={
            "budget": 100000,
            "items": [{"sku": "WDG-001", "quantity": quantity}],
        })
        assert response.status_code == 422

    def test_create_restocking_order_empty_items(self, client):
        """An order must contain at least one item."""
        response = client.post("/api/restocking-orders", json={"budget": 100000, "items": []})
        assert response.status_code == 422

    def test_create_restocking_order_negative_budget(self, client):
        """Budget cannot be negative."""
        response = client.post("/api/restocking-orders", json={
            "budget": -1,
            "items": [{"sku": "WDG-001", "quantity": 1}],
        })
        assert response.status_code == 422
