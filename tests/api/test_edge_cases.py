import uuid
import pytest

pytestmark = pytest.mark.integration


# =========================================================
# 1️⃣ INVALID PRODUCT → SHOULD RETURN 404
# =========================================================
def test_get_product_not_found(api_client):

    response = api_client.get("/products/999999")

    assert response.status_code == 404


# =========================================================
# 2️⃣ ORDER WITH NO STOCK → SHOULD FAIL
# =========================================================
def test_create_order_no_stock(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---- SETUP: product with ZERO stock ----
    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, ("NoStockProduct", 200.0, "Test"))

    product_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 0))

    db_connection.commit()

    try:
        response = api_client.post(
            "/orders",
            json={
                "user_id": 1,
                "product_id": product_id,
                "quantity": 1
            },
            headers={
                "Idempotency-Key": str(uuid.uuid4())
            }
        )

        # ---- EXPECT FAILURE ----
        assert response.status_code in (400, 422,409)

    finally:
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()


# =========================================================
# 3️⃣ CANCEL AFTER COMPLETED → SHOULD FAIL
# =========================================================
def test_cancel_after_completed_should_fail(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---- SETUP ----
    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, ("CancelEdgeProduct", 300.0, "Test"))

    product_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 10))

    db_connection.commit()

    try:
        # ---- CREATE ORDER ----
        response = api_client.post(
            "/orders",
            json={
                "user_id": 1,
                "product_id": product_id,
                "quantity": 1
            },
            headers={
                "Idempotency-Key": str(uuid.uuid4())
            }
        )

        order_id = response.json()["order_id"]

        # ---- FORCE STATUS TO COMPLETED (simulate lifecycle) ----
        cursor.execute(
            "UPDATE orders SET status = 'completed' WHERE order_id = ?",
            (order_id,)
        )
        db_connection.commit()

        # ---- TRY CANCEL ----
        cancel_response = api_client.post(f"/orders/{order_id}/cancel")

        # ---- EXPECT FAILURE ----
        assert cancel_response.status_code in (400, 422,409)

    finally:
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()