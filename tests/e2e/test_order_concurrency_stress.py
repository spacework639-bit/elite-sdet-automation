import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed


@pytest.mark.e2e
@pytest.mark.concurrency
@pytest.mark.failure(
    type="BUSINESS",
    severity="CRITICAL",
    release_blocker=True
)
def test_concurrent_orders_stress(
    api_client,
    db_connection,
    test_product
):
    """
    STRESS CONCURRENCY TEST

    Scenario:
    - Stock = 5
    - 10 parallel order requests
    - Quantity = 1 per request

    Expected:
    - 5 successes (200)
    - 5 failures (409)
    - Exactly 5 orders in DB
    - Inventory ends at 0
    """

    product_id = test_product["product_id"]

    # -------------------------------------------------
    # FORCE STOCK = 5
    # -------------------------------------------------
    cursor = db_connection.cursor()
    cursor.execute(
        "UPDATE inventory SET stock = 5 WHERE product_id = ?",
        (product_id,)
    )
    db_connection.commit()

    payload = {
        "product_id": product_id,
        "quantity": 1
    }

    headers_list = [
        {"Idempotency-Key": f"stress-key-{i}"}
        for i in range(10)
    ]

    def place_order(h):
        return api_client.post("/orders", payload, headers=h)

    # -------------------------------------------------
    # PARALLEL EXECUTION (10 REQUESTS)
    # -------------------------------------------------
    responses = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(place_order, h) for h in headers_list]
        for future in as_completed(futures):
            responses.append(future.result())

    status_codes = [r.status_code for r in responses]

    # -------------------------------------------------
    # ASSERT API RESULTS
    # -------------------------------------------------
    assert status_codes.count(200) == 5, f"Expected 5 successes, got {status_codes}"
    assert status_codes.count(409) == 5, f"Expected 5 conflicts, got {status_codes}"

    # -------------------------------------------------
    # ASSERT DB STATE
    # -------------------------------------------------
    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE product_id = ?",
        (product_id,)
    )
    order_count = cursor.fetchone()[0]
    assert order_count == 5, f"Expected 5 orders in DB, found {order_count}"

    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    stock = cursor.fetchone()[0]
    assert stock == 0, f"Expected stock=0, found {stock}"
