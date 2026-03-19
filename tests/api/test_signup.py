import uuid
import pytest
pytestmark = pytest.mark.integration

def test_signup_success(api_client):
    payload = {
        "email": f"user_{uuid.uuid4()}@test.com",
        "password": "secure123"
    }

    res = api_client.post("/auth/signup", json=payload)

    # 🔥 DEBUG HERE
    print("STATUS:", res.status_code)
    print("BODY:", res.json())

    assert res.status_code == 200

    data = res.json()
    assert "user_id" in data
    assert isinstance(data["user_id"], int)
def test_signup_duplicate(api_client):
    import uuid

    email = f"dup_{uuid.uuid4()}@test.com"

    payload = {
        "email": email,
        "password": "secure123"
    }

    # First signup
    res1 = api_client.post("/auth/signup", json=payload)
    print("FIRST:", res1.status_code, res1.json())
    assert res1.status_code == 200

    # Duplicate signup
    res2 = api_client.post("/auth/signup", json=payload)
    print("SECOND:", res2.status_code, res2.json())

    assert res2.status_code == 409

    assert res2.json()["detail"] == "User already exists"
def test_login_api_failure(api_client):
    from fastapi import HTTPException
    from unittest.mock import patch

    with patch(
        "backend.main.login_user",   # keep this FIRST
        side_effect=HTTPException(status_code=401, detail="Invalid credentials")
    ):
        response = api_client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpass"
            }
        )

    assert response.status_code == 401