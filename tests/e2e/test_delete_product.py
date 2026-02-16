# tests/e2e/test_delete_product.py

import pytest
import uuid


# ---------------------------------------------------------
# 1️⃣ PRODUCT NOT FOUND
# ---------------------------------------------------------

@pytest.mark.e2e
def test_delete_product_not_found(api_client):
    """
    Business Rule:
    - Deleting non-existent product must return 404
    """

    response = api_client.delete("/products/999999")

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

    # ---- Pick product ----
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "No product found"

    product_id = row[0]

    # ---- Create order for this product ----
    response = api_client.post(
        "/orders",
        json={"product_id": product_id, "quantity": 1},
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert response.status_code == 200

    try:
        # ---- Attempt delete ----
        delete_response = api_client.delete(f"/products/{product_id}")

        assert delete_response.status_code == 409
        assert "Cannot delete product" in delete_response.json()["detail"]

    finally:
        # ---- Cleanup: cancel order so DB not polluted ----
        order_id = response.json()["order_id"]
        api_client.post(f"/orders/{order_id}/cancel")


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

    # ---- ACT ----
    response = api_client.delete(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # ---- ASSERT DB ----
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    assert cursor.fetchone() is None

    cursor.execute("SELECT * FROM inventory WHERE product_id = ?", (product_id,))
    assert cursor.fetchone() is None
