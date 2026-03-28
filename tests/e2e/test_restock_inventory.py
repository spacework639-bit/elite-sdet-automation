# tests/e2e/test_restock_inventory.py
import pytest
import logging
import uuid

pytestmark = pytest.mark.integration


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

    # 🔥 FIX: create isolated product (no shared data)
    product_name = f"E2E_Product_{uuid.uuid4()}"

    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, (product_name, 100.0, "HERBAL"))

    product_id = cursor.fetchone()[0]
    logging.info(f"product id: {product_id}")

    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 10))

    # ---- Save original stock ----
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    original_stock = cursor.fetchone()[0]

    logging.info(f"Stock before restock: {original_stock}")

    restock_qty = 5

    # 🔥 FIX: commit before API (avoid locks)
    db_connection.commit()

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

        logging.info(f"Stock after restock: {updated_stock}")

        assert updated_stock == original_stock + restock_qty

    finally:
        # ---- CLEANUP ----
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
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