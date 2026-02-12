import pytest

# =========================================================
# SMOKE TESTS — REAL ENDPOINTS ONLY
# =========================================================
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.parametrize(
    "endpoint",
    [
        "/products",
        "/playwrights",
    ],
    ids=["products_ok", "playwrights_ok"]
)
def test_api_smoke_real_endpoints(api_client, endpoint):
    response = api_client.get(endpoint)
    assert response.status_code == 200


# =========================================================
# REGRESSION — POSITIVE + NEGATIVE
# =========================================================
@pytest.mark.regression
@pytest.mark.api
@pytest.mark.parametrize(
    "endpoint, expected_status",
    [
        ("/products", 200),
        ("/playwrights", 200),
        ("/invalid-endpoint", 404),
    ],
    ids=["products_ok", "playwrights_ok", "invalid_404"]
)
def test_api_regression_real(api_client, endpoint, expected_status):
    response = api_client.get(endpoint)
    assert response.status_code == expected_status


# =========================================================
# CONTRACT VALIDATION — PRODUCTS RESPONSE SHAPE
# =========================================================
@pytest.mark.regression
@pytest.mark.api
def test_products_response_contract(api_client):
    response = api_client.get("/products")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    if data:
        product = data[0]
        assert "id" in product
        assert "name" in product
        assert "price" in product
        assert "category" in product
