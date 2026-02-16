import pytest

@pytest.mark.e2e
def test_list_orders_returns_paginated_data(api_client):
    response = api_client.get("/orders?page=1&size=5")

    assert response.status_code == 200

    body = response.json()

    assert "page" in body
    assert "size" in body
    assert "total" in body
    assert "orders" in body

    assert isinstance(body["orders"], list)

@pytest.mark.e2e
def test_list_orders_pagination_logic(api_client, db_connection):
    cursor = db_connection.cursor()

    # Create multiple orders for deterministic pagination
    cursor.execute("SELECT TOP 1 id FROM products ORDER BY id")
    product_id = cursor.fetchone()[0]

    for i in range(5):
        api_client.post(
            "/orders",
            json={"product_id": product_id, "quantity": 1},
            headers={"Idempotency-Key": f"list-test-{i}-{product_id}"}
        )

    # Page 1
    response_page_1 = api_client.get("/orders?page=1&size=2")
    assert response_page_1.status_code == 200
    body1 = response_page_1.json()

    # Page 2
    response_page_2 = api_client.get("/orders?page=2&size=2")
    assert response_page_2.status_code == 200
    body2 = response_page_2.json()

    assert len(body1["orders"]) <= 2
    assert len(body2["orders"]) <= 2

    # Ensure different data between pages
    if body1["orders"] and body2["orders"]:
        assert body1["orders"][0]["order_id"] != body2["orders"][0]["order_id"]
