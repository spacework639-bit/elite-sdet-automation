import pytest
from core.failure_types import FailureType, Severity
import logging
import uuid

pytestmark = pytest.mark.integration


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

    # 🔥 FIX: Create isolated product (no shared data)
    product_name = f"E2E_Product_{uuid.uuid4()}"

    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, (product_name, 100.0, "HERBAL"))

    product_id = cursor.fetchone()[0]
    logging.info(f"Using product_id={product_id}")

    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 10))

    quantity = 4

    # ---------- ARRANGE ----------
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    before_stock = cursor.fetchone()[0]

    logging.info(f"Stock before order: {before_stock}")

    payload = {
        "product_id": product_id,
        "quantity": quantity
    }

    # 🔥 FIX: release DB lock before API
    db_connection.commit()

    try:
        # ---------- ACT ----------
        response = api_client.post(
            "/orders",
            json=payload,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        # ---------- ASSERT : API ----------
        assert response.status_code == 200

        body = response.json()
        assert "order_id" in body
        assert body["total_amount"] > 0

        order_id = body["order_id"]

        # ---------- ASSERT : INVENTORY ----------
        cursor.execute(
            "SELECT stock FROM inventory WHERE product_id = ?",
            (product_id,)
        )
        after_stock = cursor.fetchone()[0]

        assert after_stock == before_stock - quantity

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

        assert order_row is not None
        assert order_row[0] == product_id
        assert order_row[1] == "pending"

    finally:
        # 🔥 FIX: cleanup to avoid DB pollution
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit() 


# ------------------------------------------------------------


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
    try:
        # 🔥 FIX: isolated product instead of shared
        product_name = f"E2E_Product_{uuid.uuid4()}"

        cursor.execute("""
            INSERT INTO products (name, price, category)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?)
        """, (product_name, 100.0, "HERBAL"))

        product_id = cursor.fetchone()[0]
        logging.info(f"[create order fail TEST] product_id={product_id}")

        cursor.execute("""
            INSERT INTO inventory (product_id, stock)
            VALUES (?, ?)
        """, (product_id, 1))  # low stock

        # 🔥 commit before API
        db_connection.commit()

        payload = {
            "product_id": product_id,
            "quantity": 2
        }

        # ---------- ACT ----------
        response = api_client.post(
            "/orders",
            json=payload,
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        # ---------- ASSERT ----------
        assert response.status_code == 409
        assert "Insufficient stock" in response.json().get("detail", "")

        cursor.execute(
            "SELECT stock FROM inventory WHERE product_id = ?",
            (product_id,)
        )
        stock_after = cursor.fetchone()[0]

        assert stock_after == 1

    finally:
        # cleanup
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit() 


# ------------------------------------------------------------


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
        "product_id": 999999999999999999,
        "quantity": 1
    }

    response = api_client.post(
        "/orders",
        json=payload,
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )

    assert response.status_code == 404
    assert "Product not found" in response.json().get("detail", "")