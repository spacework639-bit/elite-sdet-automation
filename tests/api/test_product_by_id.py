from fastapi.testclient import TestClient
from backend.main import app
import pytest
pytestmark = pytest.mark.integration

client = TestClient(app)


def test_get_product_by_id(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---- DB SETUP ----
    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
    """, ("Test Product", 123.0, "Test"))

    product_id = cursor.fetchone()[0]
    db_connection.commit()

    try:
        # ---- API CALL ----
        response = api_client.get(f"/products/{product_id}")

        assert response.status_code == 200

        data = response.json()

        # ---- VALIDATION ----
        assert data["id"] == product_id
        assert data["name"] == "Test Product"
        assert data["price"] == 123.0

    finally:
        # ---- CLEANUP ----
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()