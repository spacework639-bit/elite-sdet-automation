import pytest
import uuid

pytestmark = pytest.mark.e2e


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

    # ---------------------------
    # pick product with stock
    # ---------------------------
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 1
    """)
    product_id = cursor.fetchone()[0]

    # ---------------------------
    # create order (pending)
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

    # ---------------------------
    # move through lifecycle
    # ---------------------------
    assert api_client.post(f"/orders/{order_id}/confirm").status_code == 200
    assert api_client.post(f"/orders/{order_id}/ship").status_code == 200
    assert api_client.post(f"/orders/{order_id}/complete").status_code == 200

    # ---------------------------
    # return request (VALID NOW)
    # ---------------------------
    res = api_client.post(f"/orders/{order_id}/return-request")

    assert res.status_code == 200
    assert res.json()["status"] == "return_requested"
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

    # ---------------------------
    # pick product
    # ---------------------------
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 2
    """)
    product_id = cursor.fetchone()[0]

    # ---------------------------
    # stock before
    # ---------------------------
    cursor.execute("SELECT stock FROM inventory WHERE product_id = ?", (product_id,))
    before_stock = cursor.fetchone()[0]

    # ---------------------------
    # create order
    # ---------------------------
    order = api_client.post(
        "/orders",
        json={"user_id": user_id, "product_id": product_id, "quantity": 1},
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )

    order_id = order.json()["order_id"]

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

    assert after_stock == before_stock