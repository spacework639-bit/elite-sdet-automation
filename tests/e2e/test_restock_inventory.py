# tests/e2e/test_restock_inventory.py

import pytest


# ---------------------------------------------------------
# 1️⃣ SUCCESS – STOCK INCREASES
# ---------------------------------------------------------

@pytest.mark.e2e
def test_restock_inventory_success(api_client, db_connection):
    """
    Business Rule:
    - Restocking increases inventory correctly
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

    # ---- Save original stock ----
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    original_stock = cursor.fetchone()[0]

    restock_qty = 5

    try:
        # ---- ACT ----
        response = api_client.post(
            "/inventory/restock",
            json={"product_id": product_id, "quantity": restock_qty}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "inventory_restocked"

        # ---- ASSERT DB ----
        cursor.execute(
            "SELECT stock FROM inventory WHERE product_id = ?",
            (product_id,)
        )
        updated_stock = cursor.fetchone()[0]

        assert updated_stock == original_stock + restock_qty

    finally:
        # ---- RESTORE DB ----
        cursor.execute(
            "UPDATE inventory SET stock = ? WHERE product_id = ?",
            (original_stock, product_id)
        )
        db_connection.commit()


# ---------------------------------------------------------
# 2️⃣ INVALID QUANTITY
# ---------------------------------------------------------

@pytest.mark.e2e
def test_restock_inventory_invalid_quantity(api_client):
    """
    Business Rule:
    - Restock quantity must be positive
    """

    response = api_client.post(
        "/inventory/restock",
        json={"product_id": 1, "quantity": 0}
    )

    assert response.status_code == 400
    assert "Restock quantity must be positive" in response.json()["detail"]


# ---------------------------------------------------------
# 3️⃣ PRODUCT NOT FOUND
# ---------------------------------------------------------

@pytest.mark.e2e
def test_restock_inventory_product_not_found(api_client):
    """
    Business Rule:
    - Restock must fail if product does not exist
    """

    response = api_client.post(
        "/inventory/restock",
        json={"product_id": 999999, "quantity": 5}
    )

    assert response.status_code == 404
    assert "Product not found" in response.json()["detail"]
