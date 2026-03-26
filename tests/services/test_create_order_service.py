import pytest
from fastapi import HTTPException
import pyodbc
from unittest.mock import Mock

from backend.services.order_service import create_order_service


# ✅ 1. Invalid product_id
def test_create_order_invalid_product_id():
    repo = Mock()
    conn = Mock()

    payload = {
        "product_id": "abc",
        "quantity": 2,
        "user_id": 1
    }

    with pytest.raises(HTTPException) as exc:
        create_order_service(conn, repo, payload, "key1")

    assert exc.value.status_code == 400


# ✅ 2. Missing user_id
def test_create_order_missing_user_id():
    repo = Mock()
    conn = Mock()

    payload = {
        "product_id": 1,
        "quantity": 2
    }

    with pytest.raises(HTTPException) as exc:
        create_order_service(conn, repo, payload, "key1")

    assert exc.value.status_code == 400
    assert "user_id is required" in exc.value.detail


# ✅ 3. Quantity <= 0
def test_create_order_invalid_quantity():
    repo = Mock()
    conn = Mock()

    payload = {
        "product_id": 1,
        "quantity": 0,
        "user_id": 1
    }

    with pytest.raises(HTTPException) as exc:
        create_order_service(conn, repo, payload, "key1")

    assert exc.value.status_code == 400


# ✅ 4. Idempotency hit
def test_create_order_idempotent():
    repo = Mock()
    conn = Mock()

    payload = {
        "product_id": 1,
        "quantity": 2,
        "user_id": 1
    }

    repo.get_order_by_idempotency.return_value = (123, 250.0)

    result = create_order_service(conn, repo, payload, "key1")

    assert result["status"] == "order_already_created"
    assert result["order_id"] == 123

    repo.get_product_price.assert_not_called()


# ✅ 5. Product not found
def test_create_order_product_not_found():
    repo = Mock()
    conn = Mock()

    payload = {
        "product_id": 1,
        "quantity": 2,
        "user_id": 1
    }

    repo.get_order_by_idempotency.return_value = None
    repo.get_product_price.return_value = None

    with pytest.raises(HTTPException) as exc:
        create_order_service(conn, repo, payload, "key1")

    assert exc.value.status_code == 404
    assert "Product not found" in exc.value.detail


# ✅ 6. Insufficient stock
def test_create_order_insufficient_stock():
    repo = Mock()
    conn = Mock()

    payload = {
        "product_id": 1,
        "quantity": 2,
        "user_id": 1
    }

    repo.get_order_by_idempotency.return_value = None
    repo.get_product_price.return_value = (100.0,)
    repo.deduct_inventory.return_value = 0  # no stock

    with pytest.raises(HTTPException) as exc:
        create_order_service(conn, repo, payload, "key1")

    assert exc.value.status_code == 409
    assert "Insufficient stock" in exc.value.detail


# ✅ 7. Happy path
def test_create_order_success():
    repo = Mock()
    conn = Mock()

    payload = {
        "product_id": 1,
        "quantity": 2,
        "user_id": 1,
        "vendor_id": 10
    }

    repo.get_order_by_idempotency.return_value = None
    repo.get_product_price.return_value = (100.0,)
    repo.deduct_inventory.return_value = 1
    repo.insert_order.return_value = 999

    result = create_order_service(conn, repo, payload, "key1")

    assert result["status"] == "order_created"
    assert result["order_id"] == 999
    assert result["total_amount"] == 200.0

    repo.insert_order.assert_called_once()


# ✅ 8. Deadlock error handling
def test_create_order_deadlock_error():
    repo = Mock()
    conn = Mock()

    payload = {
        "product_id": 1,
        "quantity": 2,
        "user_id": 1
    }

    repo.get_order_by_idempotency.return_value = None
    repo.get_product_price.return_value = (100.0,)
    repo.deduct_inventory.side_effect = pyodbc.Error("1205 deadlock")

    with pytest.raises(HTTPException) as exc:
        create_order_service(conn, repo, payload, "key1")

    assert exc.value.status_code == 409
    assert "Concurrent stock conflict" in exc.value.detail


# ✅ 9. Generic DB error → 500
def test_create_order_db_error():
    repo = Mock()
    conn = Mock()

    payload = {
        "product_id": 1,
        "quantity": 2,
        "user_id": 1
    }

    repo.get_order_by_idempotency.return_value = None
    repo.get_product_price.return_value = (100.0,)
    repo.deduct_inventory.side_effect = pyodbc.Error("some db error")

    with pytest.raises(HTTPException) as exc:
        create_order_service(conn, repo, payload, "key1")

    assert exc.value.status_code == 500