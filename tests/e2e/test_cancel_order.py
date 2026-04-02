import time
import pytest
import uuid
import logging

pytestmark = pytest.mark.integration


@pytest.mark.e2e
def test_cancel_order_success_restores_inventory(api_client, db_connection, test_user):
    """
    Business Rule:
    - Cancelling a pending order must:
        1) Change status to 'cancelled'
        2) Restore inventory

    What this test verifies:
    - Order creation reduces stock
    - Cancelling order restores stock
    - Order status is updated correctly
    """

    # 👉 Get DB cursor (used to directly verify database state)
    cursor = db_connection.cursor()
    try:
        # ---------------------------------------------------------
        # STEP 1: Create isolated test product (VERY IMPORTANT)
        # Why:
        # - Avoid using shared DB data
        # - Prevent stock corruption across tests
        # ---------------------------------------------------------
        product_name = f"E2E_Product_{uuid.uuid4()}"

        cursor.execute("""
            INSERT INTO products (name, price, category)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?)
        """, (product_name, 100.0, "HERBAL"))

        product_id = cursor.fetchone()[0]
        logging.info(f"[cancel success TEST] product_id={product_id}")

        # ---------------------------------------------------------
        # STEP 2: Add inventory for the product
        # ---------------------------------------------------------
        cursor.execute("""
            INSERT INTO inventory (product_id, stock)
            VALUES (?, ?)
        """, (product_id, 5))

        quantity = 2  # quantity we will order

        # ---------------------------------------------------------
        # STEP 3: Capture stock BEFORE placing order
        # ---------------------------------------------------------
        cursor.execute(
            "SELECT stock FROM inventory WHERE product_id = ?",
            (product_id,)
        )
        before_stock = cursor.fetchone()[0]
        db_connection.commit()

        # ---------------------------------------------------------
        # STEP 4: Create order via API
        # Why API:
        # - Simulates real user behavior
        # - Backend will reduce stock + commit
        # ---------------------------------------------------------
        create_response = api_client.post(
            "/orders",
            json={
                "product_id": product_id,
                "quantity": quantity,
                "user_id": test_user,
                "vendor_id": 1
            },
            headers={"Idempotency-Key": f"cancel-test-{int(time.time()*1000)}"}
        )

        assert create_response.status_code == 200
        order_id = create_response.json()["order_id"]

        # ---------------------------------------------------------
        # STEP 5: Verify stock decreased after order
        # ---------------------------------------------------------
        cursor.execute(
            "SELECT stock FROM inventory WHERE product_id = ?",
            (product_id,)
        )
        after_order_stock = cursor.fetchone()[0]

        assert after_order_stock == before_stock - quantity

        # ---------------------------------------------------------
        # STEP 6: Cancel the order via API
        # ---------------------------------------------------------
        cancel_response = api_client.post(f"/orders/{order_id}/cancel")

        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "order_cancelled"

        # ---------------------------------------------------------
        # STEP 7: Verify order status in DB
        # ---------------------------------------------------------
        cursor.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,)
        )
        status = cursor.fetchone()[0]

        assert status == "cancelled"

        # ---------------------------------------------------------
        # STEP 8: Verify inventory restored
        # ---------------------------------------------------------
        cursor.execute(
            "SELECT stock FROM inventory WHERE product_id = ?",
            (product_id,)
        )
        after_cancel_stock = cursor.fetchone()[0]

        assert after_cancel_stock == before_stock

    finally:
        # ---------------------------------------------------------
        # STEP 9: CLEANUP (CRITICAL)
        # Why:
        # - API commits cannot be rolled back
        # - Must manually delete test data
        # ---------------------------------------------------------
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit() 


@pytest.mark.e2e
def test_cancel_order_double_cancel(api_client, db_connection, test_user):

    cursor = db_connection.cursor()

    # ---- SETUP: create isolated product ----
    product_name = f"DoubleCancel_{uuid.uuid4()}"

    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, (product_name, 100.0, "HERBAL"))

    product_id = cursor.fetchone()[0]
    logging.info(f"[double cancel TEST] product_id={product_id}")

    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 5))

    # 🔥 IMPORTANT: release lock for API
    db_connection.commit()

    try:
        # ---- create order ----
        response = api_client.post(
            "/orders",
            json={
                "product_id": product_id,
                "quantity": 1,
                "user_id": test_user,
                "vendor_id": 1
            },
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        assert response.status_code == 200
        order_id = response.json()["order_id"]

        # ---- first cancel (should succeed) ----
        first_cancel = api_client.post(f"/orders/{order_id}/cancel")
        assert first_cancel.status_code == 200

        # ---- second cancel (should fail) ----
        second_cancel = api_client.post(f"/orders/{order_id}/cancel")
        assert second_cancel.status_code == 409

    finally:
        # ---- cleanup ----
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit() 


@pytest.mark.e2e
def test_cancel_order_non_existent(api_client):
    """
    Business Rule:
    - Cancelling a non-existent order returns 404

    What this test verifies:
    - API correctly handles invalid order IDs
    """

    response = api_client.post("/orders/999999999/cancel")

    assert response.status_code == 404