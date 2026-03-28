import pytest
from concurrent.futures import ThreadPoolExecutor
import logging

pytestmark = pytest.mark.integration


@pytest.mark.e2e
@pytest.mark.concurrency
def test_concurrent_orders_observe(
    api_client,
    db_connection,
    test_product
):
    """
    OBSERVATION TEST (NO ASSERTIONS)
    """

    product_id = test_product["product_id"]

    # 🔥 LOG product
    logging.info(f"[OBSERVE TEST] product_id={product_id}")

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

    headers_1 = {"Idempotency-Key": "observe-key-1"}
    headers_2 = {"Idempotency-Key": "observe-key-2"}

    def place_order(headers):
        response = api_client.post("/orders", json=payload, headers=headers)

        logging.info(
            f"[OBSERVE] key={headers['Idempotency-Key']} "
            f"status={response.status_code} "
            f"body={response.json()}"
        )

        return response

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(place_order, headers_1)
        executor.submit(place_order, headers_2)