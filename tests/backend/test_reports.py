"""
Tests for reports API endpoints (quarterly performance and monthly trends).
"""
import pytest

import main


def get_orders(client, query=""):
    """Return orders for the same filters, to cross-check report numbers."""
    response = client.get(f"/api/orders{query}")
    assert response.status_code == 200
    return response.json()


class TestQuarterlyReports:
    """Test suite for /api/reports/quarterly."""

    def test_get_quarterly_reports(self, client):
        """Unfiltered report covers every order, one row per quarter, sorted."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert [q["quarter"] for q in data] == ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"]
        assert sum(q["total_orders"] for q in data) == len(get_orders(client))
        for q in data:
            for field in ["total_orders", "total_revenue", "avg_order_value", "fulfillment_rate"]:
                assert field in q

    @pytest.mark.parametrize("query", [
        "?warehouse=Tokyo",
        "?category=Sensors",
        "?status=Delivered",
        "?month=2025-03",
        "?warehouse=London&category=Circuit Boards&status=Shipped",
    ])
    def test_quarterly_reports_apply_filters(self, client, query):
        """Quarterly totals match the orders endpoint for the same filters."""
        filtered_orders = get_orders(client, query)
        response = client.get(f"/api/reports/quarterly{query}")
        assert response.status_code == 200

        data = response.json()
        assert sum(q["total_orders"] for q in data) == len(filtered_orders)
        expected_revenue = sum(o["total_value"] for o in filtered_orders)
        assert abs(sum(q["total_revenue"] for q in data) - expected_revenue) < 0.05

    def test_quarterly_reports_month_filter_limits_quarters(self, client):
        """A single-month filter yields only that month's quarter."""
        response = client.get("/api/reports/quarterly?month=2025-11")
        assert [q["quarter"] for q in response.json()] == ["Q4-2025"]

    def test_quarterly_reports_no_matches(self, client):
        """Filters that match nothing return an empty list."""
        response = client.get("/api/reports/quarterly?warehouse=Nowhere")
        assert response.status_code == 200
        assert response.json() == []

    def test_quarterly_fulfillment_rate_calculation(self, client):
        """Fulfillment rate is delivered orders / total orders for the quarter."""
        data = client.get("/api/reports/quarterly").json()
        for q in data:
            expected = round(q["delivered_orders"] / q["total_orders"] * 100, 1)
            assert q["fulfillment_rate"] == expected

    def test_quarterly_revenue_is_rounded_to_cents(self, client):
        """Revenue values carry no floating-point noise."""
        for q in client.get("/api/reports/quarterly").json():
            assert q["total_revenue"] == round(q["total_revenue"], 2)
            assert q["avg_order_value"] == round(q["avg_order_value"], 2)

    def test_quarterly_reports_handle_any_year(self, client, monkeypatch):
        """Quarters are derived from the order date, not a hard-coded 2025 list."""
        extra = {**main.orders[0], "id": "test-2026", "order_date": "2026-02-10T00:00:00",
                 "warehouse": "Test Warehouse"}
        monkeypatch.setattr(main, "orders", main.orders + [extra])

        response = client.get("/api/reports/quarterly?warehouse=Test Warehouse")
        assert [q["quarter"] for q in response.json()] == ["Q1-2026"]


class TestMonthlyTrends:
    """Test suite for /api/reports/monthly-trends."""

    def test_get_monthly_trends(self, client):
        """Unfiltered trends cover every order, one row per month, sorted."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        months = [m["month"] for m in data]
        assert months == sorted(months)
        assert sum(m["order_count"] for m in data) == len(get_orders(client))

    @pytest.mark.parametrize("query", [
        "?warehouse=San Francisco",
        "?category=Power Supplies",
        "?status=Backordered",
        "?month=Q2-2025",
        "?warehouse=Tokyo&status=Delivered",
    ])
    def test_monthly_trends_apply_filters(self, client, query):
        """Monthly totals match the orders endpoint for the same filters."""
        filtered_orders = get_orders(client, query)
        response = client.get(f"/api/reports/monthly-trends{query}")
        assert response.status_code == 200

        data = response.json()
        assert sum(m["order_count"] for m in data) == len(filtered_orders)
        expected_revenue = sum(o["total_value"] for o in filtered_orders)
        assert abs(sum(m["revenue"] for m in data) - expected_revenue) < 0.05

    def test_monthly_trends_month_filter(self, client):
        """A month filter returns only that month."""
        data = client.get("/api/reports/monthly-trends?month=2025-07").json()
        assert [m["month"] for m in data] == ["2025-07"]

    def test_monthly_revenue_is_rounded_to_cents(self, client):
        """Revenue values carry no floating-point noise."""
        for m in client.get("/api/reports/monthly-trends").json():
            assert m["revenue"] == round(m["revenue"], 2)
