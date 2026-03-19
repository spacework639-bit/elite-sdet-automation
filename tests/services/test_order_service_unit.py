import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from backend.services.order_service import update_order_status


# ✅ 1. Order not found
def test_update_order_status_not_found():
    repo = Mock()
    conn = Mock()

    repo.get_order_for_update.return_value = None

    with pytest.raises(HTTPException) as exc:
        update_order_status(conn, repo, 1, "confirmed")

    assert exc.value.status_code == 404
    assert "Order not found" in exc.value.detail


# ✅ 2. Idempotent case
def test_update_order_status_idempotent():
    repo = Mock()
    conn = Mock()

    repo.get_order_for_update.return_value = (101, 2, "confirmed")

    result = update_order_status(conn, repo, 1, "confirmed")

    assert result["status"] == "already_confirmed"
    repo.update_order_status.assert_not_called()


# ✅ 3. Happy path
def test_update_order_status_success():
    repo = Mock()
    conn = Mock()

    repo.get_order_for_update.return_value = (101, 2, "pending")

    with patch(
        "backend.services.order_service.validate_transition",
        return_value=None
    ):
        result = update_order_status(conn, repo, 1, "confirmed")

    assert result["status"] == "order_confirmed"
    repo.update_order_status.assert_called_once_with(conn, 1, "confirmed")


# ✅ 4. Invalid transition (FIXED)
def test_update_order_status_invalid_transition():
    repo = Mock()
    conn = Mock()

    repo.get_order_for_update.return_value = (101, 2, "pending")

    with patch(
        "backend.services.order_service.validate_transition",
        side_effect=ValueError("Invalid transition")
    ) as mock_validate:

        with pytest.raises(HTTPException) as exc:
            update_order_status(conn, repo, 1, "cancelled")

        assert mock_validate.called  # ensures patch actually worked

    assert exc.value.status_code == 409
    assert "Invalid transition" in exc.value.detail


# ✅ 5. Restore inventory path
def test_update_order_status_restore_inventory():
    repo = Mock()
    conn = Mock()

    repo.get_order_for_update.return_value = (101, 5, "pending")

    with patch(
        "backend.services.order_service.validate_transition",
        return_value=None
    ):
        update_order_status(conn, repo, 1, "cancelled", restore_inventory=True)

    repo.restore_inventory.assert_called_once_with(conn, 101, 5)


# ✅ 6. Unexpected exception → 500
def test_update_order_status_unexpected_error():
    repo = Mock()
    conn = Mock()

    repo.get_order_for_update.side_effect = Exception("DB crash")

    with pytest.raises(HTTPException) as exc:
        update_order_status(conn, repo, 1, "confirmed")

    assert exc.value.status_code == 500
    assert "Order status update failed" in exc.value.detail


# ✅ 7. Return already requested
def test_update_order_status_duplicate_return_request():
    repo = Mock()
    conn = Mock()

    repo.get_order_for_update.return_value = (101, 2, "return_requested")

    with pytest.raises(HTTPException) as exc:
        update_order_status(conn, repo, 1, "return_requested")

    assert exc.value.status_code == 409
    assert "Return already requested" in exc.value.detail


# ✅ 8. Return already processed
def test_update_order_status_duplicate_return_processed():
    repo = Mock()
    conn = Mock()

    repo.get_order_for_update.return_value = (101, 2, "returned")

    with pytest.raises(HTTPException) as exc:
        update_order_status(conn, repo, 1, "returned")

    assert exc.value.status_code == 409
    assert "Return already processed" in exc.value.detail