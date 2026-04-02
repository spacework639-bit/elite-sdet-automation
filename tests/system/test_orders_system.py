import pytest
import uuid
import logging

pytestmark = pytest.mark.system


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
def test_health(api_client):
    response = api_client.get("/docs")
    assert response.status_code == 200


# ---------------------------------------------------------
# CREATE + GET ORDER (ISOLATED, CLEAN)
# ---------------------------------------------------------
def test_create_and_get_order_system(api_client, db_connection):

    cursor = db_connection.cursor()

    product_id = None
    order_id = None
    user_id = None

    try:
        # ---------------------------
        # CREATE PRODUCT (CONTROLLED)
        # ---------------------------
        product_name = f"SYS_{uuid.uuid4()}"

        cursor.execute("""
            INSERT INTO products (name, price, category)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?)
        """, (product_name, 200.0, "SYSTEM"))

        product_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO inventory (product_id, stock)
            VALUES (?, ?)
        """, (product_id, 5))

        logging.info(f"[SYSTEM TEST] product_id={product_id}")

        # 🔥 commit so API can see product
        db_connection.commit()

        # ---------------------------
        # CREATE USER
        # ---------------------------
        signup = api_client.post("/auth/signup", json={
            "email": f"sys_{uuid.uuid4()}@test.com",
            "password": "secure123"
        })

        assert signup.status_code == 200
        user_id = signup.json()["user_id"]

        logging.info(f"[SYSTEM TEST] user_id={user_id}")

        # ---------------------------
        # CREATE ORDER
        # ---------------------------
        create = api_client.post(
            "/orders",
            json={
                "product_id": product_id,
                "quantity": 1,
                "user_id": user_id
            },
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        assert create.status_code in [200, 201]

        body = create.json()
        order_id = body["order_id"]

        logging.info(f"[SYSTEM TEST] order_id={order_id}")

        # ---------------------------
        # GET ORDER
        # ---------------------------
        get = api_client.get(f"/orders/{order_id}")

        assert get.status_code == 200
        assert get.json()["order_id"] == order_id

    finally:
        # ---------------------------
        # CLEANUP (BULLETPROOF)
        # ---------------------------

        # restore stock safely
        if order_id:
            try:
                api_client.post(f"/orders/{order_id}/cancel")
            except Exception:
                pass

        if product_id:
            cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
            cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))

        db_connection.commit()