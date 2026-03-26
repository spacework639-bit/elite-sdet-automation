from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app

client = TestClient(app)


# ✅ 1. Create order
def test_create_order_api():
    with patch(
        "backend.main.create_order_service",
        return_value={"status": "order_created", "order_id": 1}
    ):
        response = client.post(
            "/orders/",
            json={
                "product_id": 1,
                "quantity": 2,
                "user_id": 1,
                "vendor_id": 1
            },
            headers={"Idempotency-Key": "test-key-123"}
        )

    assert response.status_code == 200
    assert response.json()["order_id"] == 1


# ✅ 2. Return request
def test_return_request_api():
    with patch(
        "backend.main.execute_order_status",
        return_value={"status": "return_requested", "order_id": 1}
    ):
        response = client.post("/orders/1/return-request")

    assert response.status_code == 200


# ✅ 3. Create order failure
def test_create_order_api_failure():
    from fastapi import HTTPException

    with patch(
        "backend.main.create_order_service",
        side_effect=HTTPException(status_code=409, detail="Stock issue")
    ):
        response = client.post(
            "/orders/",
            json={
                "product_id": 1,
                "quantity": 2,
                "user_id": 1,
                "vendor_id": 1
            },
            headers={"Idempotency-Key": "test-key-123"}
        )

    assert response.status_code == 409


# ✅ 4. Get products (success)
def test_get_products_api():
    with patch(
        "backend.main.get_products_service",
        return_value=[]
    ):
        response = client.get("/products")

    assert response.status_code == 200


# ✅ 5. Get products (failure)
def test_get_products_api_failure():
    from fastapi import HTTPException

    with patch(
        "backend.main.get_products_service",
        side_effect=HTTPException(status_code=500, detail="DB error")
    ):
        response = client.get("/products")

    assert response.status_code == 500


# ✅ 6. Restock inventory
def test_restock_inventory_api():
    with patch(
        "backend.main.restock_inventory_service",
        return_value={"status": "inventory_restocked"}
    ):
        response = client.post(
            "/inventory/restock",
            json={
                "product_id": 1,
                "quantity": 10
            }
        )

    assert response.status_code == 200


# ✅ 7. Update price (success)
def test_update_price_api():
    with patch(
        "backend.main.update_product_price_service",
        return_value={"id": 1, "price": 200}
    ):
        response = client.patch(
            "/products/1",
            json={"price": 200}
        )

    assert response.status_code == 200


# ✅ 8. Delete product
def test_delete_product_api():
    with patch(
        "backend.main.delete_product_service",
        return_value={"status": "deleted"}
    ):
        response = client.delete("/products/1")

    assert response.status_code == 200