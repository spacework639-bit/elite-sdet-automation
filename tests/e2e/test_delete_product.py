# tests/e2e/test_delete_product.py

import pytest
import uuid
pytestmark = pytest.mark.integration
# ---------------------------------------------------------
# 1️⃣ PRODUCT NOT FOUND
# ---------------------------------------------------------

@pytest.mark.e2e
def test_delete_product_not_found(api_client):
    """
    Business Rule:
    - Deleting non-existent product must return 404
    """

    response = api_client.delete("/products/99999999")

    assert response.status_code == 404
    assert "Product not found" in response.json()["detail"]


# ---------------------------------------------------------
# 2️⃣ PRODUCT WITH EXISTING ORDERS (409)
# ---------------------------------------------------------

@pytest.mark.e2e
def test_delete_product_with_existing_orders(api_client, db_connection):
    """
    Business Rule:
    - Product cannot be deleted if orders exist
    """

    cursor = db_connection.cursor()

    # ---- Create isolated product ----
    cursor.execute(
        """
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
        """,
        ("Delete409Product", 200.00, "Test")
    )
    product_id = cursor.fetchone()[0]

    cursor.execute(
        "INSERT INTO inventory (product_id, stock) VALUES (?, ?)",
        (product_id, 10)
    )
    db_connection.commit()

    # ---- Create order ----
    create_response = api_client.post(
        "/orders",
        json={"product_id": product_id, "quantity": 1},
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )

    assert create_response.status_code == 200
    order_id = create_response.json()["order_id"]

    try:
        # ---- Attempt delete ----
        delete_response = api_client.delete(f"/products/{product_id}")

        assert delete_response.status_code == 409
        assert "Cannot delete product" in delete_response.json()["detail"]

    finally:
        # ---- Cleanup ----
        api_client.post(f"/orders/{order_id}/cancel")
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()


# ---------------------------------------------------------
# 3️⃣ SAFE DELETE (SUCCESS)
# ---------------------------------------------------------

@pytest.mark.e2e
def test_delete_product_success(api_client, db_connection):
    """
    Business Rule:
    - Product without orders should delete successfully
    """

    cursor = db_connection.cursor()

    # ---- Create isolated product ----
    cursor.execute(
        """
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
        """,
        ("TempDeleteProduct", 123.00, "Test")
    )
    product_id = cursor.fetchone()[0]

    cursor.execute(
        "INSERT INTO inventory (product_id, stock) VALUES (?, ?)",
        (product_id, 10)
    )
    db_connection.commit()

    try:
        # ---- ACT ----
        response = api_client.delete(f"/products/{product_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
        assert response.json()["product_id"] == product_id

        # ---- ASSERT DB ----
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        assert cursor.fetchone() is None

        cursor.execute("SELECT * FROM inventory WHERE product_id = ?", (product_id,))
        assert cursor.fetchone() is None

    finally:
        # Extra safety cleanup (in case test fails mid-way)
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()
