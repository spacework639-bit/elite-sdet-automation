import uuid
import pytest
pytestmark = pytest.mark.integration


def test_cancel_order_flow(api_client, db_connection,test_user):

    cursor = db_connection.cursor()

    # ---- SETUP: Create product ----
    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, ("CancelTestProduct", 400.0, "HERBAL"))

    product_id = cursor.fetchone()[0]

    # ---- SETUP: Add inventory ----
    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 10))

    db_connection.commit()

    try:
        # ---- STEP 1: CREATE ORDER ----
        response = api_client.post(
            "/orders",
            json={
                "user_id": test_user,
                "vendor_id": 1, 
                "product_id": product_id,
                "quantity": 1
            },
            headers={
                "Idempotency-Key": str(uuid.uuid4())
            }
        )
        print("RESPONSE:", response.status_code, response.text)
        assert response.status_code == 200
        order = response.json()

        order_id = order["order_id"]

        # ---- STEP 2: CANCEL ORDER ----
        cancel_response = api_client.post(f"/orders/{order_id}/cancel")

        assert cancel_response.status_code == 200

        # ---- STEP 3: VERIFY DB STATUS ----
        cursor.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,)
        )

        row = cursor.fetchone()

        assert row is not None
        assert row[0] == "cancelled"

    finally:
        # ---- CLEANUP ----
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()