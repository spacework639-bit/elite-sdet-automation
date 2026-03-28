import pytest
import time
import uuid
import logging

pytestmark = pytest.mark.integration


@pytest.mark.e2e
def test_get_order_success(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---- create user ----
    signup = api_client.post("/auth/signup", json={
        "email": f"get_{uuid.uuid4()}@test.com",
        "password": "secure123"
    })
    assert signup.status_code == 200
    user_id = signup.json()["user_id"]

    logging.info(f"[GET ORDER] user_id={user_id}")

    # ---- 🔥 CREATE ISOLATED PRODUCT ----
    product_name = f"E2E_Product_{uuid.uuid4()}"

    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, (product_name, 150.0, "HERBAL"))

    product_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 5))

    logging.info(f"[GET ORDER] product_id={product_id}")

    # 🔥 commit before API
    db_connection.commit()

    try:
        # ---- CREATE ORDER ----
        response = api_client.post(
            "/orders",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "quantity": 1
            },
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        assert response.status_code == 200
        order_id = response.json()["order_id"]

        logging.info(f"[GET ORDER] order_id={order_id}")

        # ---- GET ORDER ----
        start = time.time()
        get_response = api_client.get(f"/orders/{order_id}")
        duration = time.time() - start

        logging.info(f"[GET ORDER] duration={duration}")

        assert duration < 2.5, f"GET took too long: {duration}s"

        assert get_response.status_code == 200

        body = get_response.json()

        assert body["order_id"] == order_id
        assert body["product_id"] == product_id
        assert body["status"] == "pending"
        assert body["total_amount"] > 0
        assert body["created_at"] is not None

    finally:
        # ---- CLEANUP ----
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()


@pytest.mark.e2e
def test_get_order_not_found(api_client):

    response = api_client.get("/orders/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"