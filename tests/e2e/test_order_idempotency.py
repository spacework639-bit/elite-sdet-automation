import pytest
from core.failure_types import FailureType, Severity


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

    headers = {
        "Idempotency-Key": "pytest-idem-1"
    }

    payload = {
        "product_id": product_id,
        "quantity": quantity
    }

    # First request
    response_1 = api_client.post("/orders", payload, headers=headers)
    assert response_1.status_code == 200
    order_id_1 = response_1.json()["order_id"]

    # Second request (same key)
    response_2 = api_client.post("/orders", payload, headers=headers)
    assert response_2.status_code == 200
    order_id_2 = response_2.json()["order_id"]

    # Same order must be returned
    assert order_id_1 == order_id_2

    # Inventory reduced only once
    cursor = db_connection.cursor()
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    stock_after = cursor.fetchone()[0]

    assert stock_after == initial_stock - quantity

    # Only one order row exists
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE idempotency_key = ?
        """,
        ("pytest-idem-1",)
    )
    count = cursor.fetchone()[0]

    assert count == 1
