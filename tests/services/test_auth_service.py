import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
import hashlib

from backend.services.auth_service import login_user


# ✅ 1. User not found
def test_login_user_not_found():
    mock_conn = Mock()

    with (
        patch("backend.services.auth_service.get_connection", return_value=mock_conn),
        patch("backend.services.auth_service.get_user_by_email", return_value=None) as mock_repo
    ):
        with pytest.raises(HTTPException) as exc:
            login_user("test@example.com", "pass")

    assert exc.value.status_code == 401
    assert "Invalid credentials" in exc.value.detail

    mock_repo.assert_called_once()
    mock_conn.close.assert_called_once()


# ✅ 2. Invalid password
def test_login_user_invalid_password():
    mock_conn = Mock()

    fake_user = (1, "test@example.com", "wronghash")

    with (
        patch("backend.services.auth_service.get_connection", return_value=mock_conn),
        patch("backend.services.auth_service.get_user_by_email", return_value=fake_user) as mock_repo
    ):
        with pytest.raises(HTTPException) as exc:
            login_user("test@example.com", "pass")

    assert exc.value.status_code == 401
    assert "Invalid credentials" in exc.value.detail

    mock_repo.assert_called_once()
    mock_conn.close.assert_called_once()


# ✅ 3. Successful login
def test_login_user_success():
    mock_conn = Mock()

    correct_hash = hashlib.sha256("pass".encode()).hexdigest()
    fake_user = (1, "test@example.com", correct_hash)

    with (
        patch("backend.services.auth_service.get_connection", return_value=mock_conn),
        patch("backend.services.auth_service.get_user_by_email", return_value=fake_user) as mock_repo
    ):
        result = login_user("test@example.com", "pass")

    assert result == 1  # returns user_id

    mock_repo.assert_called_once()
    mock_conn.close.assert_called_once()