import pytest
from fastapi import HTTPException
from unittest.mock import Mock

from backend.services.order_service import (
    get_order_service,
    restock_inventory_service
)


# =========================
# ✅ get_order_service
# =========================

def test_get_order_service_success():
    repo = Mock()
    conn = Mock()

    repo.get_order_by_id.return_value = (
        1, 10, 20, 30, 2, 500.0, "pending", "2025-01-01"
    )

    result = get_order_service(conn, repo, 1)

    assert result["order_id"] == 1
    assert result["user_id"] == 10
    assert result["total_amount"] == 500.0
    assert result["status"] == "pending"


def test_get_order_service_not_found():
    repo = Mock()
    conn = Mock()

    repo.get_order_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        get_order_service(conn, repo, 1)

    assert exc.value.status_code == 404
    assert "Order not found" in exc.value.detail


# =========================
# ✅ restock_inventory_service
# =========================

def test_restock_inventory_invalid_types():
    repo = Mock()
    conn = Mock()

    with pytest.raises(HTTPException) as exc:
        restock_inventory_service(conn, repo, "abc", 5)

    assert exc.value.status_code == 400


def test_restock_inventory_negative_quantity():
    repo = Mock()
    conn = Mock()

    with pytest.raises(HTTPException) as exc:
        restock_inventory_service(conn, repo, 1, 0)

    assert exc.value.status_code == 400
    assert "Restock quantity must be positive" in exc.value.detail


def test_restock_inventory_product_not_found():
    repo = Mock()
    conn = Mock()

    repo.product_exists.return_value = False

    with pytest.raises(HTTPException) as exc:
        restock_inventory_service(conn, repo, 1, 5)

    assert exc.value.status_code == 404
    assert "Product not found" in exc.value.detail


def test_restock_inventory_missing_record():
    repo = Mock()
    conn = Mock()

    repo.product_exists.return_value = True
    repo.restock_inventory.return_value = 0

    with pytest.raises(HTTPException) as exc:
        restock_inventory_service(conn, repo, 1, 5)

    assert exc.value.status_code == 500
    assert "Inventory record missing" in exc.value.detail


def test_restock_inventory_success():
    repo = Mock()
    conn = Mock()

    repo.product_exists.return_value = True
    repo.restock_inventory.return_value = 1

    result = restock_inventory_service(conn, repo, 1, 5)

    assert result["status"] == "inventory_restocked"
    assert result["product_id"] == 1
    assert result["added_quantity"] == 5