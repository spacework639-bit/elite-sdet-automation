# tests/performance/test_sla.py

import time
import pytest
import uuid
import logging


# =========================================================
# 1️⃣ ORDER CREATION – COLD START + STEADY STATE
# =========================================================

@pytest.mark.performance
def test_order_creation_sla(api_client, db_connection):

    cursor = db_connection.cursor()

    product_id = None
    order_ids = []
    user_id = None

    try:
        # ---------------------------
        # CREATE PRODUCT (CONTROLLED)
        # ---------------------------
        product_name = f"SLA_{uuid.uuid4()}"

        cursor.execute("""
            INSERT INTO products (name, price, category)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?)
        """, (product_name, 150.0, "PERF"))

        product_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO inventory (product_id, stock)
            VALUES (?, ?)
        """, (product_id, 20))  # enough for multiple calls

        db_connection.commit()

        logging.info(f"[SLA TEST] product_id={product_id}")

        # ---------------------------
        # CREATE USER
        # ---------------------------
        signup = api_client.post("/auth/signup", json={
            "email": f"sla_{uuid.uuid4()}@test.com",
            "password": "secure123"
        })

        assert signup.status_code == 200
        user_id = signup.json()["user_id"]

        # ---------------------------
        # COLD START
        # ---------------------------
        cold_start = time.perf_counter()

        cold_response = api_client.post(
            "/orders",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "quantity": 1
            },
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        cold_end = time.perf_counter()
        cold_ms = (cold_end - cold_start) * 1000

        print(f"\nOrder Cold Start: {cold_ms:.2f}ms")
        assert cold_response.status_code == 200

        cold_order_id = cold_response.json()["order_id"]
        order_ids.append(cold_order_id)

        # ---------------------------
        # WARM-UP
        # ---------------------------
        warm = api_client.post(
            "/orders",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "quantity": 1
            },
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )
        if warm.status_code == 200:
            order_ids.append(warm.json()["order_id"])

        # ---------------------------
        # STEADY STATE
        # ---------------------------
        steady_start = time.perf_counter()

        steady_response = api_client.post(
            "/orders",
            json={
                "user_id": user_id,
                "product_id": product_id,
                "quantity": 1
            },
            headers={"Idempotency-Key": str(uuid.uuid4())}
        )

        steady_end = time.perf_counter()
        steady_ms = (steady_end - steady_start) * 1000

        print(f"Order Steady State: {steady_ms:.2f}ms")

        assert steady_response.status_code == 200
        assert steady_ms < 2200, f"SLA breached: {steady_ms:.2f}ms"

        order_ids.append(steady_response.json()["order_id"])

    finally:
        # ---------------------------
        # CLEANUP (CRITICAL)
        # ---------------------------
        for oid in order_ids:
            try:
                api_client.post(f"/orders/{oid}/cancel")
            except Exception:
                pass

        if product_id:
            cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
            cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))

        db_connection.commit()


# =========================================================
# 2️⃣ GET PRODUCT – COLD START + STEADY STATE
# =========================================================

@pytest.mark.performance
def test_get_product_sla(api_client, db_connection):

    cursor = db_connection.cursor()
    product_id = None

    try:
        # ---------------------------
        # CREATE PRODUCT
        # ---------------------------
        cursor.execute("""
            INSERT INTO products (name, price, category)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?)
        """, (f"SLA_GET_{uuid.uuid4()}", 100.0, "PERF"))

        product_id = cursor.fetchone()[0]
        db_connection.commit()

        # ---------------------------
        # COLD START
        # ---------------------------
        cold_start = time.perf_counter()
        cold_response = api_client.get(f"/products/{product_id}")
        cold_end = time.perf_counter()

        cold_ms = (cold_end - cold_start) * 1000
        print(f"\nGET Cold: {cold_ms:.2f}ms")

        assert cold_response.status_code == 200

        # ---------------------------
        # WARM-UP
        # ---------------------------
        api_client.get(f"/products/{product_id}")

        # ---------------------------
        # STEADY STATE
        # ---------------------------
        steady_start = time.perf_counter()
        steady_response = api_client.get(f"/products/{product_id}")
        steady_end = time.perf_counter()

        steady_ms = (steady_end - steady_start) * 1000
        print(f"GET Steady: {steady_ms:.2f}ms")

        assert steady_response.status_code == 200
        assert steady_ms < 2200, f"SLA breached: {steady_ms:.2f}ms"

    finally:
        if product_id:
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            db_connection.commit()