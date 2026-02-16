import pytest
from tests.ui.pages.products_page import ProductsPage
import logging
import uuid

@pytest.mark.e2e_ui
@pytest.mark.regression
def test_ui_order_success_reduces_inventory(page, db_connection):
    cursor = db_connection.cursor()

    # 🔎 Get a real product with enough stock (works in CI + local)
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 5
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "Precondition failed: No product with sufficient stock"

    product_id = row[0]
    logging.info(f"Selected product_id={product_id} for success test")
    order_qty = 2
    idem_key = str(uuid.uuid4())

    # ---------- BEFORE ----------
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    before_stock = cursor.fetchone()[0]
    logging.info(f"Stock before order: {before_stock}")


    # ---------- UI ACTION ----------
    ui = ProductsPage(page)
    ui.open_orders_api()
    ui.place_order_via_swagger(product_id, order_qty, idem_key)

    # ---------- AFTER ----------
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    after_stock = cursor.fetchone()[0]
    logging.info(f"Stock after order: {after_stock}")

    assert after_stock == before_stock - order_qty, \
        "Inventory was not reduced correctly via UI order"


# ---------------------------------------------------------
# NEGATIVE SCENARIO 1 – PRODUCT NOT FOUND
# ---------------------------------------------------------

@pytest.mark.e2e_ui
@pytest.mark.regression
@pytest.mark.xfail(
    reason="Negative UI scenario - product not found",
    strict=True
)
def test_ui_order_product_not_found(page):
    product_id = 999999   # non-existent product
    order_qty = 1
    idem_key = str(uuid.uuid4())

    ui = ProductsPage(page)
    ui.open_orders_api()
    ui.place_order_via_swagger(product_id, order_qty, idem_key)

    pytest.fail("Product not found scenario triggered")


# ---------------------------------------------------------
# NEGATIVE SCENARIO 2 – INSUFFICIENT STOCK
# ---------------------------------------------------------
@pytest.mark.e2e_ui
@pytest.mark.regression
@pytest.mark.xfail(
    reason="Negative UI scenario - insufficient stock",
    strict=True
)
def test_ui_order_insufficient_stock(page, db_connection):
    cursor = db_connection.cursor()

    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "Precondition failed: No product found"

    product_id = row[0]

    # ---------- SAVE ORIGINAL ----------
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    original_stock = cursor.fetchone()[0]

    try:
        # Force low stock
        cursor.execute(
            "UPDATE inventory SET stock = 1 WHERE product_id = ?",
            (product_id,)
        )
        db_connection.commit()

        order_qty = 5
        idem_key = str(uuid.uuid4())

        ui = ProductsPage(page)
        ui.open_orders_api()
        ui.place_order_via_swagger(product_id, order_qty, idem_key)

        pytest.fail("Insufficient stock scenario triggered")

    finally:
        # ---------- RESTORE ----------
        cursor.execute(
            "UPDATE inventory SET stock = ? WHERE product_id = ?",
            (original_stock, product_id)
        )
        db_connection.commit()
