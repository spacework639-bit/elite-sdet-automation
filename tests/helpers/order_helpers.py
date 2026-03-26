


def create_test_order(db_connection):
    cursor = db_connection.cursor()

    # Pick product with enough stock
    cursor.execute("""
        SELECT TOP 1 p.id, i.stock
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.stock >= 5
        ORDER BY p.id
    """)
    row = cursor.fetchone()

    assert row is not None, "No product with sufficient stock"

    product_id = row[0]
    quantity = 2

    # Insert order with 'pending' status
    cursor.execute("""
        INSERT INTO orders (product_id, quantity, status)
        OUTPUT INSERTED.order_id
        VALUES (?, ?, 'pending')
    """, (product_id, quantity))

    order_id = cursor.fetchone()[0]

    # Reduce stock (simulate real order behavior)
    cursor.execute("""
        UPDATE inventory
        SET stock = stock - ?
        WHERE product_id = ?
    """, (quantity, product_id))

    db_connection.commit()

    return order_id
