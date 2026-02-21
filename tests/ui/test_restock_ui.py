import pytest
import logging
from tests.ui.pages.inventory_page import InventoryPage


@pytest.mark.e2e_ui
@pytest.mark.regression
def test_ui_restock_success(page, db_connection):

    cursor = db_connection.cursor()

    # Pick product
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None

    product_id = row[0]
    restock_qty = 5

    logging.info(f"[RESTOCK TEST] Selected product_id={product_id}")

    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    stock_before = cursor.fetchone()[0]

    logging.info(f"[RESTOCK TEST] Stock before: {stock_before}")

    try:
        # UI Action
        ui = InventoryPage(page)
        ui.open_restock_api()
        response = ui.restock_via_swagger(product_id, restock_qty)

        assert response.status == 200
        body = response.json()

        logging.info(f"[RESTOCK TEST] API response: {body}")

        cursor.execute(
            "SELECT stock FROM inventory WHERE product_id = ?",
            (product_id,)
        )
        stock_after = cursor.fetchone()[0]

        logging.info(f"[RESTOCK TEST] Stock after: {stock_after}")

        assert stock_after == stock_before + restock_qty

    finally:
        # Restore original stock
        cursor.execute(
            "UPDATE inventory SET stock = ? WHERE product_id = ?",
            (stock_before, product_id)
        )
        db_connection.commit()

        logging.info(
            f"[RESTOCK TEST] Restored stock to original value: {stock_before}"
        )
@pytest.mark.e2e_ui
@pytest.mark.regression
def test_ui_restock_product_not_found(page):

    ui = InventoryPage(page)
    ui.open_restock_api()

    fake_product_id = 99999999
    quantity = 5

    response = ui.restock_via_swagger(fake_product_id, quantity)

    assert response.status == 404
    body = response.json()
    assert body["detail"] == "Product not found"


@pytest.mark.e2e_ui
@pytest.mark.regression
def test_ui_restock_negative_quantity(page, db_connection):

    cursor = db_connection.cursor()

    cursor.execute("""
        SELECT TOP 1 id FROM products ORDER BY id
    """)
    product_id = cursor.fetchone()[0]

    ui = InventoryPage(page)
    ui.open_restock_api()

    response = ui.restock_via_swagger(product_id, -5)

    assert response.status == 400
    body = response.json()
    assert body["detail"] == "Restock quantity must be positive"
