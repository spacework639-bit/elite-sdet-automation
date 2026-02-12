def test_get_products(api_client):
    response = api_client.get("/products")

    assert response.status_code == 200

    products = response.json()
    assert isinstance(products, list)

    # If DB has data, validate structure
    if len(products) > 0:
        product = products[0]
        assert "id" in product
        assert "name" in product
        assert "price" in product
    
