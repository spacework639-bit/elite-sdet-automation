# tests/performance/test_sla.py

import time
import pytest
import uuid


# =========================================================
# 1️⃣ ORDER CREATION – COLD START + STEADY STATE
# =========================================================

@pytest.mark.performance
def test_order_creation_sla(api_client):

    # ---------------------------
    # COLD START MEASUREMENT
    # ---------------------------
    cold_start_begin = time.perf_counter()

    cold_response = api_client.post(
        "/orders",
        json={"product_id": 1, "quantity": 1},
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )

    cold_start_end = time.perf_counter()
    cold_duration_ms = (cold_start_end - cold_start_begin) * 1000

    print(f"\nOrder Creation Cold Start: {cold_duration_ms:.2f}ms")

    assert cold_response.status_code == 200

    # Cleanup cold order
    cold_order_id = cold_response.json()["order_id"]
    api_client.post(f"/orders/{cold_order_id}/cancel")

    # ---------------------------
    # STEADY STATE MEASUREMENT
    # ---------------------------
    # Warm-up call
    api_client.post(
        "/orders",
        json={"product_id": 1, "quantity": 1},
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )

    steady_start = time.perf_counter()

    steady_response = api_client.post(
        "/orders",
        json={"product_id": 1, "quantity": 1},
        headers={"Idempotency-Key": str(uuid.uuid4())}
    )

    steady_end = time.perf_counter()
    steady_duration_ms = (steady_end - steady_start) * 1000

    print(f"Order Creation Steady State: {steady_duration_ms:.2f}ms")

    assert steady_response.status_code == 200
    assert steady_duration_ms < 500, f"Steady SLA breached: {steady_duration_ms:.2f}ms"

    # Cleanup steady order
    steady_order_id = steady_response.json()["order_id"]
    api_client.post(f"/orders/{steady_order_id}/cancel")


# =========================================================
# 2️⃣ GET PRODUCT – COLD START + STEADY STATE
# =========================================================

@pytest.mark.performance
def test_get_product_sla(api_client):

    # ---------------------------
    # COLD START
    # ---------------------------
    cold_start = time.perf_counter()
    cold_response = api_client.get("/products/1")
    cold_end = time.perf_counter()

    cold_duration_ms = (cold_end - cold_start) * 1000

    print(f"\nGET Product Cold Start: {cold_duration_ms:.2f}ms")

    assert cold_response.status_code == 200

    # ---------------------------
    # STEADY STATE
    # ---------------------------
    # Warm-up call
    api_client.get("/products/1")

    steady_start = time.perf_counter()
    steady_response = api_client.get("/products/1")
    steady_end = time.perf_counter()

    steady_duration_ms = (steady_end - steady_start) * 1000

    print(f"GET Product Steady State: {steady_duration_ms:.2f}ms")

    assert steady_response.status_code == 200
    assert steady_duration_ms < 300, f"Steady SLA breached: {steady_duration_ms:.2f}ms"
