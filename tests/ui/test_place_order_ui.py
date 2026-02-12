import pytest
import time
from tests.ui.pages.products_page import ProductsPage


@pytest.mark.e2e_ui
@pytest.mark.regression
def test_ui_order_success_reduces_inventory(page, db_connection):
    product_id = cursor.fetchone()[0]
    order_qty = 2
    idem_key = f"ui-ok-{int(time.time())}"

    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    before_stock = cursor.fetchone()[0]

    ui = ProductsPage(page)
    ui.open_orders_api()
    ui.place_order_via_swagger(product_id, order_qty, idem_key)

    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    after_stock = cursor.fetchone()[0]

    assert after_stock == before_stock - order_qty


@pytest.mark.e2e_ui
@pytest.mark.regression
@pytest.mark.xfail(
    reason="Negative UI scenario - product not found",
    strict=True
)
def test_ui_order_product_not_found(page):
    product_id = 99999
    order_qty = 1
    idem_key = f"ui-nf-{int(time.time())}"

    ui = ProductsPage(page)
    ui.open_orders_api()
    ui.place_order_via_swagger(product_id, order_qty, idem_key)

    pytest.fail("Product not found scenario triggered")


@pytest.mark.e2e_ui
@pytest.mark.regression
@pytest.mark.xfail(
    reason="Negative UI scenario - insufficient stock",
    strict=True
)
def test_ui_order_insufficient_stock(page):
    product_id = 9
    order_qty = 65
    idem_key = f"ui-stock-{int(time.time())}"

    ui = ProductsPage(page)
    ui.open_orders_api()
    ui.place_order_via_swagger(product_id, order_qty, idem_key)

    pytest.fail("Insufficient stock scenario triggered")
