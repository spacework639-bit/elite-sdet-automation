pytestmark = pytest.mark.integration
def test_create_playwright_api(api_client):
    payload = {
        "name": "api_test_user",
        "skill": "automation"
    }
    response = api_client.post("/playwrights", json=payload)


    assert response.status_code == 200
    assert response.json()["status"] == "created"
