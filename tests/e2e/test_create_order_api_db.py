# tests/e2e/test_create_order_api_db.py

import pytest
from core.failure_types import FailureType, Severity
import time
import logging


@pytest.mark.failure(
    type=FailureType.SYSTEM,
    severity=Severity.MEDIUM,
    release_blocker=True
)
@pytest.mark.e2e
def test_create_order_success_reduces_inventory_and_creates_order(
    api_client,
    db_connection
):
    """
    Business Rule:
    - A valid order must:
        1) Reduce inventory correctly
        2) Create an order record in DB
        3) Set order status to 'pending'
    """

    cursor = db_connection.cursor()

    # 🔎 Dynamically pick a product with stock >= 5
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 5
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "Precondition failed: No product with sufficient stock found"

    product_id = row[0]
    quantity = 4
    
    logging.info(f"Selected product_id={product_id} for success test")
    # ---------- ARRANGE ----------
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    row = cursor.fetchone()
    assert row is not None, "Precondition failed: inventory record missing"

    before_stock = row[0]
    logging.info(f"Stock before order: {before_stock}")

    assert before_stock >= quantity, (
        f"Precondition failed: stock {before_stock} < quantity {quantity}"
    )

    payload = {
        "product_id": product_id,
        "quantity": quantity
    }

    # ---------- ACT ----------s
    response = api_client.post(
    "/orders",
    json=payload,
    headers={"Idempotency-Key": f"e2e-success-{int(time.time() * 1000)}"})


    # ---------- ASSERT : API ----------
    assert response.status_code == 200, "Order API should succeed"

    body = response.json()
    assert "order_id" in body, "Order ID must be returned"
    assert "total_amount" in body, "Total amount must be returned"
    assert body["total_amount"] > 0, "Total amount must be positive"

    order_id = body["order_id"]

    # ---------- ASSERT : INVENTORY ----------
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    after_stock = cursor.fetchone()[0]
    logging.info(f"Stock after order: {after_stock}")


    assert after_stock == before_stock - quantity, (
        "Inventory was not reduced correctly"
    )

    # ---------- ASSERT : ORDER RECORD ----------
    cursor.execute(
        """
        SELECT product_id, status
        FROM orders
        WHERE order_id = ?
        """,
        (order_id,)
    )
    order_row = cursor.fetchone()

    assert order_row is not None, "Order row not created in database"
    assert order_row[0] == product_id, "Incorrect product_id in order"
    assert order_row[1] == "pending", "Order status must be 'pending'"


@pytest.mark.e2e
@pytest.mark.failure(
    type=FailureType.BUSINESS,
    severity=Severity.HIGH,
    release_blocker=True
)
def test_create_order_fails_when_stock_is_insufficient_and_inventory_unchanged(
    api_client,
    db_connection
):
    """
    Business Rule:
    - Order must fail when requested quantity exceeds stock
    - Inventory must remain unchanged
    """

    cursor = db_connection.cursor()

    # 🔎 Pick any product dynamically
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "Precondition failed: No product found"

    product_id = row[0]
    logging.info(f"Selected product_id={product_id} for success test")
    

    # ---------- ARRANGE ----------
    cursor.execute(
        "UPDATE inventory SET stock = 1 WHERE product_id = ?",
        (product_id,)
    )
    db_connection.commit()

    payload = {
        "product_id": product_id,
        "quantity": 2
    }

    # ---------- ACT ----------
    response = api_client.post(
    "/orders",
    json=payload,
    headers={"Idempotency-Key": f"e2e-success-{int(time.time() * 1000)}"}
    )


    # ---------- ASSERT : API ----------
    assert response.status_code == 409, (
        "Expected 409 Conflict for insufficient stock"
    )
    assert "Insufficient stock" in response.json().get("detail", ""), (
        "Missing insufficient stock error message"
    )

    # ---------- ASSERT : INVENTORY ----------
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    stock_after = cursor.fetchone()[0]
    logging.info(f"Stock after order: {stock_after}")

    assert stock_after == 1, (
        "Inventory should not change when order fails"
    )


@pytest.mark.failure(
    type=FailureType.VALIDATION,
    severity=Severity.MEDIUM,
    release_blocker=False
)
@pytest.mark.e2e
def test_create_order_fails_for_invalid_product_id(api_client):
    """
    Business Rule:
    - Order must fail if product_id does not exist
    """

    payload = {
        "product_id": 999999,
        "quantity": 1
    }

    response = api_client.post(
    "/orders",
    json=payload,
    headers={"Idempotency-Key": f"e2e-success-{int(time.time() * 1000)}"}
    )


    assert response.status_code == 404, "Expected 404 for invalid product"
    assert "Product not found" in response.json().get("detail", ""), (
        "Missing product not found message"
    )
