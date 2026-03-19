import uuid
import pytest

pytestmark = pytest.mark.integration


def test_create_order_success(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---- SETUP: Create user (SAFE ADD) ----
    cursor.execute("""
        INSERT INTO users_elite (email, password_hash)
        OUTPUT INSERTED.id
        VALUES (?, ?)
    """, (f"user_{uuid.uuid4()}@test.com", "dummyhash"))

    user_id = cursor.fetchone()[0]

    # ---- SETUP: Create product ----
    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, ("OrderTestProduct", 500.0, "Test"))

    product_id = cursor.fetchone()[0]

    # ---- SETUP: Add inventory ----
    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 10))

    db_connection.commit()

    try:
        # ---- API CALL ----
        response = api_client.post(
            "/orders",
            json={
                "user_id": user_id,   # ✅ FIXED (no more hardcoded 1)
                "product_id": product_id,
                "quantity": 2
            },
            headers={
                "Idempotency-Key": str(uuid.uuid4())
            }
        )

        assert response.status_code == 200

        data = response.json()

        # ---- VALIDATION (API RESPONSE) ----
        assert "order_id" in data
        assert data["status"] == "order_created"

        # ---- DB VALIDATION (STRONG) ----
        cursor.execute(
            """
            SELECT product_id, quantity, status, total_amount
            FROM orders
            WHERE product_id = ?
            """,
            (product_id,)
        )

        row = cursor.fetchone()

        assert row is not None
        assert row[0] == product_id
        assert row[1] == 2
        assert row[2] == "pending"
        assert float(row[3]) == 1000.0  # 500 * 2

    finally:
        # ---- CLEANUP ----
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        cursor.execute("DELETE FROM users_elite WHERE id = ?", (user_id,))  # ✅ added
        db_connection.commit()