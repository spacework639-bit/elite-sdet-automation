import pytest
import uuid
import logging

pytestmark = pytest.mark.integration


# ---------------------------------------------------------
# 1️⃣ BASIC PAGINATION STRUCTURE
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# 2️⃣ PAGINATION LOGIC (ISOLATED)
# ---------------------------------------------------------

@pytest.mark.e2e
def test_list_orders_pagination_logic(api_client, db_connection):

    cursor = db_connection.cursor()

    # 🔥 Create isolated product
    product_name = f"ListTest_{uuid.uuid4()}"

    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, (product_name, 100.0, "TEST"))

    product_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO inventory (product_id, stock)
        VALUES (?, ?)
    """, (product_id, 20))

    db_connection.commit()

    logging.info(f"[LIST TEST] product_id={product_id}")

    created_order_ids = []

    try:
        # 🔥 Create controlled number of orders
        for i in range(5):
            res = api_client.post(
                "/orders",
                json={"product_id": product_id, "quantity": 1},
                headers={"Idempotency-Key": f"list-{uuid.uuid4()}"}
            )
            assert res.status_code == 200
            order_id = res.json()["order_id"]
            created_order_ids.append(order_id)

        logging.info(f"[LIST TEST] created_orders={created_order_ids}")

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

    finally:
        # 🔥 CLEANUP
        cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()