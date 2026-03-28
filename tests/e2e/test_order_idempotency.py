import pytest
import uuid
import logging
from core.failure_types import FailureType, Severity

pytestmark = pytest.mark.integration


@pytest.mark.e2e
@pytest.mark.idempotency
@pytest.mark.failure(
    type=FailureType.BUSINESS,
    severity=Severity.CRITICAL,
    release_blocker=True
)
def test_create_order_is_idempotent(
    api_client,
    db_connection,
    test_product
):
    """
    Idempotency Rule:
    - Same order request with same Idempotency-Key
      must NOT create duplicate orders
    - Inventory must be reduced only once
    """

    product_id = test_product["product_id"]
    initial_stock = test_product["initial_stock"]
    quantity = 1

    # 🔥 FIX: unique idempotency key (safe)
    idem_key = f"pytest-idem-{uuid.uuid4()}"

    logging.info(f"[IDEMPOTENCY TEST] product_id={product_id}, key={idem_key}")

    headers = {
        "Idempotency-Key": idem_key
    }

    payload = {
        "product_id": product_id,
        "quantity": quantity
    }

    # First request
    response_1 = api_client.post("/orders", json=payload, headers=headers)
    assert response_1.status_code == 200
    order_id_1 = response_1.json()["order_id"]

    logging.info(f"[IDEMPOTENCY TEST] first_order_id={order_id_1}")

    # Second request (same key)
    response_2 = api_client.post("/orders", json=payload, headers=headers)
    assert response_2.status_code == 200
    order_id_2 = response_2.json()["order_id"]

    logging.info(f"[IDEMPOTENCY TEST] second_order_id={order_id_2}")

    # Same order must be returned
    assert order_id_1 == order_id_2

    # Inventory reduced only once
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    stock_after = cursor.fetchone()[0]

    logging.info(f"[IDEMPOTENCY TEST] stock_after={stock_after}")

    assert stock_after == initial_stock - quantity

    # Only one order row exists
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE idempotency_key = ?
        """,
        (idem_key,)
    )
    count = cursor.fetchone()[0]

    logging.info(f"[IDEMPOTENCY TEST] order_count={count}")

    assert count == 1