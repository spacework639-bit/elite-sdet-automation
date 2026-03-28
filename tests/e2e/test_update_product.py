import pytest
import uuid
import logging

pytestmark = pytest.mark.integration


@pytest.mark.e2e
def test_update_product_price_success(api_client, db_connection):

    cursor = db_connection.cursor()

    # ---------------------------
    # 🔥 CREATE ISOLATED PRODUCT
    # ---------------------------
    product_name = f"E2E_Product_{uuid.uuid4()}"

    cursor.execute("""
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id, INSERTED.price
        VALUES (?, ?, ?)
    """, (product_name, 100.0, "HERBAL"))

    row = cursor.fetchone()
    product_id = row[0]
    old_price = float(row[1])

    logging.info(f"[UPDATE TEST] product_id={product_id}, old_price={old_price}")

    new_price = old_price + 50

    # 🔥 commit before API
    db_connection.commit()

    try:
        # ---------------------------
        # UPDATE via API
        # ---------------------------
        response = api_client.patch(
            f"/products/{product_id}",
            json={"price": new_price}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["price"] == new_price

        # ---------------------------
        # VERIFY DB
        # ---------------------------
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        updated_price = float(cursor.fetchone()[0])

        logging.info(f"[UPDATE TEST] updated_price={updated_price}")

        assert updated_price == new_price

    finally:
        # 🔥 CLEANUP (stronger than restore)
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db_connection.commit()