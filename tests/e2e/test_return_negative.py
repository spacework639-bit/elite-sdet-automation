import pytest
import uuid
import logging

pytestmark = pytest.mark.integration


# =========================================================
# 1️⃣ DOUBLE RETURN REQUEST SHOULD FAIL
# =========================================================
def test_double_return_request_fails(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---------------------------
    # create user
    # ---------------------------
    email = f"dup_{uuid.uuid4()}@test.com"
    password = "secure123"

    api_client.post("/auth/signup", json={"email": email, "password": password})
    login = api_client.post("/auth/login", json={"email": email, "password": password})
    user_id = login.json()["user_id"]

    logging.info(f"[RETURN NEG] user_id={user_id}")

    # ---------------------------
    # 🔥 isolated product
    # ---------------------------
    product_name = f"E2E_Product_{uuid.uuid4()}"

    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, (product_name, 100.0, "HERBAL"))

    product_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 5))

    logging.info(f"[RETURN NEG] product_id={product_id}")

    # 🔥 commit before API
    db_connection.commit()

    try:
        # ---------------------------
        # create order
        # ---------------------------
        order = api_client.post(
            "/orders",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "quantity": 1
            },
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        order_id = order.json()["order_id"]

        logging.info(f"[RETURN NEG] order_id={order_id}")

        # lifecycle
        api_client.post(f"/orders/{order_id}/confirm")
        api_client.post(f"/orders/{order_id}/ship")
        api_client.post(f"/orders/{order_id}/complete")

        # first return request
        api_client.post(f"/orders/{order_id}/return-request")

        # second return request (should fail)
        res = api_client.post(f"/orders/{order_id}/return-request")

        assert res.status_code == 409

    finally:
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()


# =========================================================
# 2️⃣ RETURN RECEIVED WITHOUT REQUEST SHOULD FAIL
# =========================================================
def test_return_received_without_request_fails(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---------------------------
    # create user
    # ---------------------------
    email = f"no_req_{uuid.uuid4()}@test.com"
    password = "secure123"

    api_client.post("/auth/signup", json={"email": email, "password": password})
    login = api_client.post("/auth/login", json={"email": email, "password": password})
    user_id = login.json()["user_id"]

    logging.info(f"[RETURN NEG] user_id={user_id}")

    # ---------------------------
    # 🔥 isolated product
    # ---------------------------
    product_name = f"E2E_Product_{uuid.uuid4()}"

    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, (product_name, 100.0, "HERBAL"))

    product_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 5))

    logging.info(f"[RETURN NEG] product_id={product_id}")

    # 🔥 commit before API
    db_connection.commit()

    try:
        # ---------------------------
        # create order
        # ---------------------------
        order = api_client.post(
            "/orders",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "quantity": 1
            },
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        order_id = order.json()["order_id"]

        logging.info(f"[RETURN NEG] order_id={order_id}")

        # lifecycle
        api_client.post(f"/orders/{order_id}/confirm")
        api_client.post(f"/orders/{order_id}/ship")
        api_client.post(f"/orders/{order_id}/complete")

        # directly return-received (should fail)
        res = api_client.post(f"/orders/{order_id}/return-received")

        assert res.status_code == 409

    finally:
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()


# =========================================================
# 3️⃣ INVALID ORDER ID SHOULD RETURN 404
# =========================================================
def test_return_request_invalid_order(api_client):

    res = api_client.post("/orders/999999/return-request")

    assert res.status_code == 404