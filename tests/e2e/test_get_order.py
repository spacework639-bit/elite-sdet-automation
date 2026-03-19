import pytest
import time
import uuid

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

    # ---- pick product ----
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 2
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None

    product_id = row[0]

    # ---- CREATE ORDER ----
    response = api_client.post(
        "/orders",
        json={
            "user_id": user_id,   # ✅ FIXED
            "product_id": product_id,
            "quantity": 1
        },
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )

    assert response.status_code == 200
    order_id = response.json()["order_id"]

    # ---- GET ORDER ----
    start = time.time()
    get_response = api_client.get(f"/orders/{order_id}")
    duration = time.time() - start

    # ✅ realistic SLA
    assert duration < 2.5, f"GET took too long: {duration}s"

    assert get_response.status_code == 200

    body = get_response.json()

    assert body["order_id"] == order_id
    assert body["product_id"] == product_id
    assert body["status"] == "pending"
    assert body["total_amount"] > 0
    assert body["created_at"] is not None


@pytest.mark.e2e
def test_get_order_not_found(api_client):

    response = api_client.get("/orders/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"