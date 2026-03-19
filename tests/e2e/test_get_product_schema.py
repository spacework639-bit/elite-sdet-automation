import pytest

pytestmark = pytest.mark.integration
# ---------------------------------------------------------
# 1️⃣ SUCCESS – VALID RESPONSE SCHEMA
# ---------------------------------------------------------

@pytest.mark.e2e
def test_get_product_success_schema(api_client, db_connection):
    """
    Business Rule:
    - GET /products/{id} must return correct schema and types
    """

    cursor = db_connection.cursor()

    # ---- Create isolated product ----
    cursor.execute(
        """
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
        """,
        ("SchemaTestProduct", 321.00, "SchemaCategory")
    )
    product_id = cursor.fetchone()[0]
    db_connection.commit()

    try:
        response = api_client.get(f"/products/{product_id}")

        assert response.status_code == 200

        data = response.json()

        # ---- Required Keys ----
        expected_keys = {
            "id",
            "name",
            "price",
            "category",
            "created_at",
            "image_url" 
        }

        assert set(data.keys()) == expected_keys

        # ---- Type Validation ----
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)
        assert isinstance(data["category"], str)
        assert isinstance(data["created_at"], str)
        # NEW (since your API returns it)
        assert isinstance(data["image_url"], (str, type(None)))

    finally:
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()


# ---------------------------------------------------------
# 2️⃣ PRODUCT NOT FOUND – 404 STRUCTURE
# ---------------------------------------------------------

@pytest.mark.e2e
def test_get_product_not_found_schema(api_client):
    """
    Business Rule:
    - Non-existent product must return 404 with error structure
    """

    response = api_client.get("/products/99999999")

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data
    assert isinstance(data["detail"], str)


# ---------------------------------------------------------
# 3️⃣ INVALID PRODUCT ID TYPE
# ---------------------------------------------------------

@pytest.mark.e2e
def test_get_product_invalid_id_type(api_client):
    """
    Business Rule:
    - Non-integer product ID must trigger validation error
    """

    response = api_client.get("/products/invalid")

    # FastAPI validation error
    assert response.status_code == 422

    data = response.json()

    assert "detail" in data
    assert isinstance(data["detail"], list)
