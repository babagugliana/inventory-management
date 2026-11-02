"""
Tests for task endpoints (/api/tasks) and purchase order endpoints
(/api/purchase-orders) used by the Tasks modal and the Dashboard backlog table.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Tasks and purchase orders live in module-level lists; clear them between tests."""
    main.tasks.clear()
    main.purchase_orders.clear()
    yield
    main.tasks.clear()
    main.purchase_orders.clear()


def new_task(client, **overrides):
    payload = {"title": "Check Q4 stock", "priority": "high", "dueDate": "2025-12-01", **overrides}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def first_backlog_item(client):
    response = client.get("/api/backlog")
    assert response.status_code == 200
    return response.json()[0]


def new_po_payload(backlog_item_id, **overrides):
    return {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": 350,
        "unit_cost": 8.4,
        "expected_delivery_date": "2025-12-15",
        "notes": "Rush",
        **overrides,
    }


class TestTaskEndpoints:
    """Test suite for /api/tasks."""

    def test_get_tasks_initially_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """A new task is pending and echoes the submitted fields."""
        task = new_task(client)
        assert task["title"] == "Check Q4 stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-12-01"
        assert task["status"] == "pending"
        assert isinstance(task["id"], str)

    def test_created_task_ids_do_not_collide_with_mock_ids(self, client):
        """The frontend mixes API tasks with numeric mock tasks (ids 1-4), so API ids must differ."""
        task = new_task(client)
        assert task["id"] not in [1, 2, 3, 4, "1", "2", "3", "4"]

    def test_created_tasks_are_listed(self, client):
        first = new_task(client, title="A")
        second = new_task(client, title="B")
        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert set(ids) == {first["id"], second["id"]}

    def test_toggle_task(self, client):
        """PATCH flips pending <-> completed."""
        task = new_task(client)
        response = client.patch(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task['id']}")
        assert response.json()["status"] == "pending"

    def test_delete_task(self, client):
        task = new_task(client)
        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        assert client.get("/api/tasks").json() == []

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_nonexistent_task(self, client, method):
        response = getattr(client, method)("/api/tasks/nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.parametrize("payload", [
        {"title": "", "priority": "high", "dueDate": "2025-12-01"},
        {"title": "X", "priority": "urgent", "dueDate": "2025-12-01"},
        {"title": "X", "priority": "high"},
    ])
    def test_create_task_invalid(self, client, payload):
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 422


class TestPurchaseOrderEndpoints:
    """Test suite for /api/purchase-orders."""

    def test_create_purchase_order(self, client):
        item = first_backlog_item(client)
        response = client.post("/api/purchase-orders", json=new_po_payload(item["id"]))
        assert response.status_code == 201

        po = response.json()
        assert po["backlog_item_id"] == item["id"]
        assert po["supplier_name"] == "Acme Supply"
        assert po["quantity"] == 350
        assert po["unit_cost"] == 8.4
        assert po["status"] == "Pending"
        assert po["id"].startswith("PO-")
        assert po["created_date"]

    def test_get_purchase_order_by_backlog_item(self, client):
        item = first_backlog_item(client)
        created = client.post("/api/purchase-orders", json=new_po_payload(item["id"])).json()

        response = client.get(f"/api/purchase-orders/{item['id']}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_purchase_order_none(self, client):
        response = client.get("/api/purchase-orders/1")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_backlog_reflects_purchase_order(self, client):
        """After a PO is created, /api/backlog marks the item and exposes the PO id."""
        item = first_backlog_item(client)
        assert item["has_purchase_order"] is False
        assert item["purchase_order_id"] is None

        po = client.post("/api/purchase-orders", json=new_po_payload(item["id"])).json()
        updated = first_backlog_item(client)
        assert updated["has_purchase_order"] is True
        assert updated["purchase_order_id"] == po["id"]

    def test_create_purchase_order_unknown_backlog_item(self, client):
        response = client.post("/api/purchase-orders", json=new_po_payload("nope-999"))
        assert response.status_code == 404

    def test_create_duplicate_purchase_order(self, client):
        """Only one PO per backlog item."""
        item = first_backlog_item(client)
        assert client.post("/api/purchase-orders", json=new_po_payload(item["id"])).status_code == 201
        response = client.post("/api/purchase-orders", json=new_po_payload(item["id"]))
        assert response.status_code == 400

    @pytest.mark.parametrize("overrides", [
        {"quantity": 0},
        {"unit_cost": -1},
        {"supplier_name": ""},
    ])
    def test_create_purchase_order_invalid(self, client, overrides):
        item = first_backlog_item(client)
        response = client.post("/api/purchase-orders", json=new_po_payload(item["id"], **overrides))
        assert response.status_code == 422
