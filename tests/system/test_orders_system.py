import pytest
import uuid


@pytest.mark.system
def test_health(api_client):
    response = api_client.get("/docs")
    assert response.status_code == 200


@pytest.mark.system
def test_create_and_get_order_system(api_client):
    payload = {
        "product_id": 1,
        "quantity": 1,
        "user_id": 1,
        "vendor_id": 1
    }

    headers = {
        "Idempotency-Key": str(uuid.uuid4())
    }

    create = api_client.post(
        "/orders",
        json=payload,
        headers=headers
    )

    assert create.status_code in [200, 201]

    order_id = create.json()["order_id"]

    get = api_client.get(f"/orders/{order_id}")

    assert get.status_code == 200
    assert get.json()["order_id"] == order_id