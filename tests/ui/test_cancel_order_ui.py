import pytest
from tests.ui.pages.orders_page import OrdersPage
import json
import uuid



def create_order_via_api(page, product_id, quantity):
    response = page.request.post(
        "http://127.0.0.1:8000/orders",
        data=json.dumps({
            "product_id": product_id,
            "quantity": quantity
        }),
        headers={
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4())
        }
    )

    assert response.status == 200, response.text()

    return response.json()["order_id"]

# ---------------------------------------------------------
# UI CANCEL ORDER – HAPPY PATH
# ---------------------------------------------------------
@pytest.mark.e2e_ui
@pytest.mark.regression
def test_ui_cancel_order_success(page, db_connection):

    cursor = db_connection.cursor()

    # ---------- SETUP ----------
    # Pick product with enough stock
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 5
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "No product with sufficient stock"

    product_id = row[0]
    quantity = 2

    # Create real order via backend API
    order_id = create_order_via_api(page, product_id, quantity)

    # ---------- PRE-CONDITION ----------
    cursor.execute(
        "SELECT status FROM orders WHERE order_id = ?",
        (order_id,)
    )
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "pending"

    # Capture stock before cancel
    cursor.execute("""
        SELECT i.stock
        FROM inventory i
        JOIN orders o ON i.product_id = o.product_id
        WHERE o.order_id = ?
    """, (order_id,))
    stock_before = cursor.fetchone()[0]

    # ---------- UI ACTION ----------
    ui = OrdersPage(page)
    ui.open_cancel_order_api()
    response = ui.cancel_order_via_swagger(order_id)

    # ---------- HTTP VALIDATION ----------
    assert response.status == 200
    body = response.json()
    assert body["status"] == "order_cancelled"
    assert body["order_id"] == order_id

    # ---------- DB VALIDATION ----------
    cursor.execute(
        "SELECT status FROM orders WHERE order_id = ?",
        (order_id,)
    )
    updated_status = cursor.fetchone()[0]
    assert updated_status == "cancelled"

    # Validate inventory restored
    cursor.execute("""
        SELECT i.stock
        FROM inventory i
        JOIN orders o ON i.product_id = o.product_id
        WHERE o.order_id = ?
    """, (order_id,))
    stock_after = cursor.fetchone()[0]

    assert stock_after == stock_before + quantity

@pytest.mark.e2e_ui
@pytest.mark.regression
def test_ui_cancel_order_not_found(page):

    fake_order_id = 99999999

    ui = OrdersPage(page)
    ui.open_cancel_order_api()
    response = ui.cancel_order_via_swagger(fake_order_id)

    # HTTP validation
    assert response.status == 404

    body = response.json()
    assert body["detail"] == "Order not found"

@pytest.mark.e2e_ui
@pytest.mark.regression



# ---------------------------------------------------------
# UI DOUBLE CANCEL TEST
# ---------------------------------------------------------
@pytest.mark.e2e_ui
@pytest.mark.regression
def test_ui_double_cancel_order(page, db_connection):

    cursor = db_connection.cursor()

    # ---------- SETUP ----------
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 5
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "No product with stock"

    product_id = row[0]
    quantity = 2

    order_id = create_order_via_api(page, product_id, quantity)

    # ---------- FIRST CANCEL ----------
    ui = OrdersPage(page)
    ui.open_cancel_order_api()

    first_response = ui.cancel_order_via_swagger(order_id)
    assert first_response.status == 200

    # Validate status updated
    cursor.execute(
        "SELECT status FROM orders WHERE order_id = ?",
        (order_id,)
    )
    status_after_first = cursor.fetchone()[0]
    assert status_after_first == "cancelled"

    # Capture stock after first cancel
    cursor.execute("""
        SELECT i.stock
        FROM inventory i
        JOIN orders o ON i.product_id = o.product_id
        WHERE o.order_id = ?
    """, (order_id,))
    stock_after_first = cursor.fetchone()[0]

    # ---------- SECOND CANCEL (fresh page load) ----------
    ui.open_cancel_order_api()

    second_response = ui.cancel_order_via_swagger(order_id)

    assert second_response.status == 200
    body = second_response.json()
    assert "already" in str(body).lower()

    # ---------- DB VALIDATION ----------
    cursor.execute(
        "SELECT status FROM orders WHERE order_id = ?",
        (order_id,)
    )
    status_after_second = cursor.fetchone()[0]

    assert status_after_second == "cancelled"

    # Ensure stock not modified again
    cursor.execute("""
        SELECT i.stock
        FROM inventory i
        JOIN orders o ON i.product_id = o.product_id
        WHERE o.order_id = ?
    """, (order_id,))
    stock_after_second = cursor.fetchone()[0]

    assert stock_after_second == stock_after_first



