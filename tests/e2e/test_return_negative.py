# tests/e2e/test_return_negative.py

import pytest
import uuid

pytestmark = pytest.mark.e2e


# =========================================================
# 1️⃣ DOUBLE RETURN REQUEST SHOULD FAIL
# =========================================================
def test_double_return_request_fails(api_client, db_connection):

    # ---------------------------
    # create user
    # ---------------------------
    email = f"dup_{uuid.uuid4()}@test.com"
    password = "secure123"

    api_client.post("/auth/signup", json={"email": email, "password": password})
    login = api_client.post("/auth/login", json={"email": email, "password": password})
    user_id = login.json()["user_id"]

    # ---------------------------
    # pick product
    # ---------------------------
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 2
    """)
    product_id = cursor.fetchone()[0]

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

    # ---------------------------
    # move to completed
    # ---------------------------
    api_client.post(f"/orders/{order_id}/confirm")
    api_client.post(f"/orders/{order_id}/ship")
    api_client.post(f"/orders/{order_id}/complete")

    # ---------------------------
    # first return request
    # ---------------------------
    api_client.post(f"/orders/{order_id}/return-request")

    # ---------------------------
    # second return request (should fail)
    # ---------------------------
    res = api_client.post(f"/orders/{order_id}/return-request")

    assert res.status_code == 409


# =========================================================
# 2️⃣ RETURN RECEIVED WITHOUT REQUEST SHOULD FAIL
# =========================================================
def test_return_received_without_request_fails(api_client, db_connection):

    # ---------------------------
    # create user
    # ---------------------------
    email = f"no_req_{uuid.uuid4()}@test.com"
    password = "secure123"

    api_client.post("/auth/signup", json={"email": email, "password": password})
    login = api_client.post("/auth/login", json={"email": email, "password": password})
    user_id = login.json()["user_id"]

    # ---------------------------
    # pick product
    # ---------------------------
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 1
    """)
    product_id = cursor.fetchone()[0]

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

    # ---------------------------
    # move to completed (no return-request)
    # ---------------------------
    api_client.post(f"/orders/{order_id}/confirm")
    api_client.post(f"/orders/{order_id}/ship")
    api_client.post(f"/orders/{order_id}/complete")

    # ---------------------------
    # directly return-received (should fail)
    # ---------------------------
    res = api_client.post(f"/orders/{order_id}/return-received")

    assert res.status_code == 409


# =========================================================
# 3️⃣ INVALID ORDER ID SHOULD RETURN 404
# =========================================================
def test_return_request_invalid_order(api_client):

    res = api_client.post("/orders/999999/return-request")

    assert res.status_code == 404