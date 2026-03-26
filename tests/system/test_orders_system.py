import pytest
import uuid


@pytest.mark.system
def test_health(api_client):
    response = api_client.get("/docs")
    assert response.status_code == 200


@pytest.mark.system
def test_create_and_get_order_system(api_client, db_connection):

    cursor = db_connection.cursor()

    # ✅ create user
    signup = api_client.post("/auth/signup", json={
        "email": f"sys_{uuid.uuid4()}@test.com",
        "password": "secure123"
    })
    assert signup.status_code == 200
    user_id = signup.json()["user_id"]

    # ✅ pick product with stock
    cursor.execute("""
        SELECT TOP 1 p.id
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock > 0
        ORDER BY p.id
    """)
    row = cursor.fetchone()
    assert row is not None, "No product with stock available"

    product_id = row[0]

    payload = {
        "product_id": product_id,   # ✅ FIXED
        "quantity": 1,
        "user_id": user_id
    }

    headers = {
        "Idempotency-Key": str(uuid.uuid4())
    }

    create = api_client.post("/orders", json=payload, headers=headers)

    assert create.status_code in [200, 201]

    body = create.json()
    assert "order_id" in body

    order_id = body["order_id"]

    get = api_client.get(f"/orders/{order_id}")

    assert get.status_code == 200
    assert get.json()["order_id"] == order_id