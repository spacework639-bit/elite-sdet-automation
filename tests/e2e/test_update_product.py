import pytest
pytestmark = pytest.mark.integration
@pytest.mark.e2e
def test_update_product_price_success(api_client, db_connection):
    cursor = db_connection.cursor()

    cursor.execute("SELECT TOP 1 id, price FROM products ORDER BY id")
    row = cursor.fetchone()
    assert row is not None

    product_id = row[0]
    old_price = float(row[1])
    new_price = old_price + 50

    try:
        response = api_client.patch(
            f"/products/{product_id}",
            json={"price": new_price}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["price"] == new_price

        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        updated_price = float(cursor.fetchone()[0])
        assert updated_price == new_price

    finally:
        # ---- Restore original price ----
        cursor.execute(
            "UPDATE products SET price = ? WHERE id = ?",
            (old_price, product_id)
        )
        db_connection.commit()
