import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

pytestmark = pytest.mark.integration


@pytest.mark.e2e
@pytest.mark.concurrency
@pytest.mark.failure(
    type="BUSINESS",
    severity="CRITICAL",
    release_blocker=True
)
def test_concurrent_orders_single_stock(
    api_client,
    db_connection,
    test_product
):
    """
    FINAL CONCURRENCY TEST
    """

    product_id = test_product["product_id"]

    # 🔥 LOG product
    logging.info(f"[CONCURRENCY TEST] product_id={product_id}")

    # -------------------------------------------------
    # FORCE BOUNDARY CONDITION
    # -------------------------------------------------
    cursor = db_connection.cursor()
    cursor.execute(
        "UPDATE inventory SET stock = 1 WHERE product_id = ?",
        (product_id,)
    )
    db_connection.commit()

    payload = {
        "product_id": product_id,
        "quantity": 1
    }

    headers = [
        {"Idempotency-Key": "concurrency-key-1"},
        {"Idempotency-Key": "concurrency-key-2"}
    ]

    def place_order(h):
        logging.info(f"[THREAD] placing order with key={h['Idempotency-Key']}")
        response = api_client.post("/orders", json=payload, headers=h)
        logging.info(f"[THREAD] response={response.status_code}")
        return response

    # -------------------------------------------------
    # PARALLEL EXECUTION
    # -------------------------------------------------
    responses = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(place_order, h) for h in headers]
        for future in as_completed(futures):
            responses.append(future.result())

    status_codes = [r.status_code for r in responses]

    logging.info(f"[RESULT] status_codes={status_codes}")

    # -------------------------------------------------
    # ASSERT API BEHAVIOR
    # -------------------------------------------------
    assert status_codes.count(200) == 1, f"Expected 1 success, got {status_codes}"
    assert status_codes.count(409) == 1, f"Expected 1 conflict, got {status_codes}"

    # -------------------------------------------------
    # ASSERT DB STATE
    # -------------------------------------------------
    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE product_id = ?",
        (product_id,)
    )
    order_count = cursor.fetchone()[0]

    logging.info(f"[DB] order_count={order_count}")

    assert order_count == 1, f"Expected 1 order in DB, found {order_count}"

    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    stock = cursor.fetchone()[0]

    logging.info(f"[DB] final_stock={stock}")

    assert stock == 0, f"Expected stock=0, found {stock}"