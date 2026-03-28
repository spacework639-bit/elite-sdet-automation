import pytest
import uuid

pytestmark = pytest.mark.integration


@pytest.mark.e2e
@pytest.mark.lifecycle
def test_full_order_lifecycle(
    api_client,
    db_connection,
    test_product
):
    """
    FULL LIFECYCLE E2E TEST
    """

    product_id = test_product["product_id"]
    cursor = db_connection.cursor()

    # -------------------------------------------------
    # Capture Original Stock
    # -------------------------------------------------
    cursor.execute(
        "SELECT stock FROM inventory WHERE product_id = ?",
        (product_id,)
    )
    original_stock = cursor.fetchone()[0]

    order_id = None

    try:
        # -------------------------------------------------
        # Set Controlled Inventory State
        # -------------------------------------------------
        cursor.execute(
            "UPDATE inventory SET stock = 10 WHERE product_id = ?",
            (product_id,)
        )

        # 🔥 FIX: commit before API (prevents DB lock / hang)
        db_connection.commit()

        payload = {
            "product_id": product_id,
            "quantity": 2
        }

        # -------------------------------------------------
        # CREATE
        # -------------------------------------------------
        idempotency_key = str(uuid.uuid4())

        response = api_client.post(
            "/orders",
            json=payload,
            headers={"Idempotency-Key": idempotency_key}
        )

        assert response.status_code == 200

        order_id = response.json()["order_id"]

        cursor.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,)
        )
        assert cursor.fetchone()[0] == "pending"

        # -------------------------------------------------
        # CONFIRM
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/confirm")
        assert r.status_code == 200

        cursor.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,)
        )
        assert cursor.fetchone()[0] == "confirmed"

        # -------------------------------------------------
        # SHIP
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/ship")
        assert r.status_code == 200

        cursor.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,)
        )
        assert cursor.fetchone()[0] == "shipped"

        # -------------------------------------------------
        # NEGATIVE 1: Cancel After Shipped
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/cancel")
        assert r.status_code == 409

        # -------------------------------------------------
        # COMPLETE
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/complete")
        assert r.status_code == 200

        cursor.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,)
        )
        assert cursor.fetchone()[0] == "completed"

        # -------------------------------------------------
        # NEGATIVE 2: Confirm After Completed
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/confirm")
        assert r.status_code == 409

        # -------------------------------------------------
        # RETURN REQUEST
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/return-request")
        assert r.status_code == 200

        cursor.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,)
        )
        assert cursor.fetchone()[0] == "return_requested"

        # -------------------------------------------------
        # RETURN RECEIVED
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/return-received")
        assert r.status_code == 200

        cursor.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,)
        )
        assert cursor.fetchone()[0] == "returned"

        cursor.execute(
            "SELECT stock FROM inventory WHERE product_id = ?",
            (product_id,)
        )
        assert cursor.fetchone()[0] == 10

        # -------------------------------------------------
        # REFUND
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/refund")
        assert r.status_code == 200

        cursor.execute(
            "SELECT status FROM orders WHERE order_id = ?",
            (order_id,)
        )
        assert cursor.fetchone()[0] == "refunded"

        # -------------------------------------------------
        # NEGATIVE 3: Double Refund
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/refund")
        assert r.status_code == 409

        # -------------------------------------------------
        # NEGATIVE 4: Cancel After Refunded
        # -------------------------------------------------
        r = api_client.post(f"/orders/{order_id}/cancel")
        assert r.status_code == 409

    finally:
        # -------------------------------------------------
        # CLEANUP
        # -------------------------------------------------
        if order_id:
            cursor.execute(
                "DELETE FROM orders WHERE order_id = ?",
                (order_id,)
            )

        cursor.execute(
            "UPDATE inventory SET stock = ? WHERE product_id = ?",
            (original_stock, product_id)
        )

        db_connection.commit()