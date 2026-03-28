import pytest
import uuid
import logging

pytestmark = pytest.mark.integration


def test_return_request_success(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---------------------------
    # create user
    # ---------------------------
    signup = api_client.post("/auth/signup", json={
        "email": f"return_{uuid.uuid4()}@test.com",
        "password": "secure123"
    })
    assert signup.status_code == 200
    user_id = signup.json()["user_id"]

    logging.info(f"[RETURN TEST] user_id={user_id}")

    # ---------------------------
    # 🔥 CREATE ISOLATED PRODUCT
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

    logging.info(f"[RETURN TEST] product_id={product_id}")

    # 🔥 commit so API can see data
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

        assert order.status_code == 200
        order_id = order.json()["order_id"]

        logging.info(f"[RETURN TEST] order_id={order_id}")

        # lifecycle
        assert api_client.post(f"/orders/{order_id}/confirm").status_code == 200
        assert api_client.post(f"/orders/{order_id}/ship").status_code == 200
        assert api_client.post(f"/orders/{order_id}/complete").status_code == 200

        # return request
        res = api_client.post(f"/orders/{order_id}/return-request")

        assert res.status_code == 200
        assert res.json()["status"] == "return_requested"

    finally:
        # 🔥 CLEANUP
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()


# -----------------------------------------------------


def test_return_received_restores_inventory(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---------------------------
    # signup + login
    # ---------------------------
    email = f"ret_{uuid.uuid4()}@test.com"
    password = "secure123"

    api_client.post("/auth/signup", json={"email": email, "password": password})
    login = api_client.post("/auth/login", json={"email": email, "password": password})
    user_id = login.json()["user_id"]

    logging.info(f"[RETURN TEST] user_id={user_id}")

    # ---------------------------
    # 🔥 CREATE ISOLATED PRODUCT
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

    logging.info(f"[RETURN TEST] product_id={product_id}")

    # ---------------------------
    # stock before
    # ---------------------------
    cursor.execute("SELECT stock FROM inventory WHERE product_id = ?", (product_id,))
    before_stock = cursor.fetchone()[0]

    # 🔥 commit before API
    db_connection.commit()

    try:
        # ---------------------------
        # create order
        # ---------------------------
        order = api_client.post(
            "/orders",
            json={"user_id": user_id, "product_id": product_id, "quantity": 1},
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        order_id = order.json()["order_id"]

        logging.info(f"[RETURN TEST] order_id={order_id}")

        # lifecycle
        api_client.post(f"/orders/{order_id}/confirm")
        api_client.post(f"/orders/{order_id}/ship")
        api_client.post(f"/orders/{order_id}/complete")

        # return flow
        api_client.post(f"/orders/{order_id}/return-request")
        res = api_client.post(f"/orders/{order_id}/return-received")

        assert res.status_code == 200
        assert res.json()["status"] in ["returned", "return_processed"]

        # ---------------------------
        # stock after
        # ---------------------------
        cursor.execute("SELECT stock FROM inventory WHERE product_id = ?", (product_id,))
        after_stock = cursor.fetchone()[0]

        logging.info(f"[RETURN TEST] before={before_stock}, after={after_stock}")

        assert after_stock == before_stock

    finally:
        # 🔥 CLEANUP
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()