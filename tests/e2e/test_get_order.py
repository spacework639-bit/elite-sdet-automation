
import pytest
import time
import uuid


@pytest.mark.e2e
def test_get_order_success(api_client, db_connection):
    """
    Business Rule:
    - After creating an order,
      GET /orders/{id} must return correct lifecycle data.
    """

    cursor = db_connection.cursor()

    # ---- ARRANGE: pick product with stock ----
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 2
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "Precondition failed: No product with sufficient stock"

    product_id = row[0]
    quantity = 1

    # ---- CREATE ORDER ----
    response = api_client.post(
        "/orders",
        json={"product_id": product_id, "quantity": quantity},
        idem_key = str(uuid.uuid4())
    )

    assert response.status_code == 200
    order_id = response.json()["order_id"]

    # ---- ACT: GET ORDER ----
    start = time.time()
    get_response = api_client.get(f"/orders/{order_id}")
    duration = time.time() - start

    # ---- ASSERT: Performance ----
    assert duration < 0.3, f"GET took too long: {duration}s"

    # ---- ASSERT: API ----
    assert get_response.status_code == 200

    body = get_response.json()

    assert body["order_id"] == order_id
    assert body["product_id"] == product_id
    assert body["status"] == "pending"
    assert body["total_amount"] > 0
    assert body["created_at"] is not None


@pytest.mark.e2e
def test_get_order_not_found(api_client):
    """
    Business Rule:
    - GET on non-existent order must return 404.
    """

    response = api_client.get("/orders/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


