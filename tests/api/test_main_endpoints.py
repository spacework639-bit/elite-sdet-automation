from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app

client = TestClient(app)


# =========================
# ✅ LOGIN TESTS
# =========================

def test_login_success():
    with patch("backend.main.login_user", return_value=1):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "pass"
        })

    assert response.status_code == 200
    assert response.json()["user_id"] == 1


def test_login_invalid_credentials():
    from fastapi import HTTPException

    with patch(
        "backend.main.login_user",
        side_effect=HTTPException(status_code=401, detail="Invalid credentials")
    ):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrong"
        })

    assert response.status_code == 401


# =========================
# ✅ SIGNUP TESTS
# =========================

def test_signup_success():
    with patch("backend.main.signup_user", return_value=10):
        response = client.post("/auth/signup", json={
            "email": "test@example.com",
            "password": "password123"   # ✅ FIXED
        })

    assert response.status_code == 200
    assert response.json()["user_id"] == 10


def test_signup_user_exists():
    from fastapi import HTTPException

    with patch(
        "backend.main.signup_user",
        side_effect=HTTPException(status_code=409, detail="User already exists")
    ):
        response = client.post("/auth/signup", json={
            "email": "test@example.com",
            "password": "password123"   # ✅ FIXED
        })

    assert response.status_code == 409