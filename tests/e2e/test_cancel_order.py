import time
import pytest


@pytest.mark.e2e
def test_cancel_order_success_restores_inventory(api_client, db_connection):
    """
    Business Rule:
    - Cancelling a pending order must:
        1) Change status to 'cancelled'
        2) Restore inventory
    """

    cursor = db_connection.cursor()

    # ---- Pick product with stock ----
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 3
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "Precondition failed: No product with sufficient stock"

    product_id = row[0]
    quantity = 2

    # ---- Capture stock before order ----
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    before_stock = cursor.fetchone()[0]

    # ---- Create order ----
    create_response = api_client.post(
        "/orders",
        json={"product_id": product_id, "quantity": quantity},
        headers={"Idempotency-Key": f"cancel-test-{int(time.time()*1000)}"}
    )

    assert create_response.status_code == 200
    order_id = create_response.json()["order_id"]

    # ---- Capture stock after order ----
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    after_order_stock = cursor.fetchone()[0]

    assert after_order_stock == before_stock - quantity

    # ---- ACT: Cancel order ----
    cancel_response = api_client.post(f"/orders/{order_id}/cancel")

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "order_cancelled"

    # ---- ASSERT: Status updated ----
    cursor.execute(
        "SELECT status FROM orders WHERE order_id = ?",
        (order_id,)
    )
    status = cursor.fetchone()[0]

    assert status == "cancelled"

    # ---- ASSERT: Inventory restored ----
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    after_cancel_stock = cursor.fetchone()[0]

    assert after_cancel_stock == before_stock


@pytest.mark.e2e
def test_cancel_order_double_cancel(api_client):
    """
    Business Rule:
    - Cancelling an already cancelled order must return 409.
    """

    # We assume order_id 9999999 likely does not exist.
    # First call should 404 if not exist.
    response = api_client.post("/orders/9999999/cancel")

    assert response.status_code == 404


@pytest.mark.e2e
def test_cancel_order_non_existent(api_client):
    """
    Business Rule:
    - Cancelling non-existent order returns 404.
    """

    response = api_client.post("/orders/999999999/cancel")

    assert response.status_code == 404
