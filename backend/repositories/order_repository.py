class OrderRepository:
    """
    Repository Layer
    ----------------
    • Only SQL
    • No business logic
    • No HTTP exceptions
    • No commit / rollback
    • No connection creation
    • Encapsulates cursor handling internally
    """

    # ---------- ORDER CREATION ----------

    def get_order_by_idempotency(self, conn, idempotency_key: str):
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT order_id, total_amount
            FROM orders
            WHERE idempotency_key = ?
            """,
            (idempotency_key,)
        )
        return cursor.fetchone()

    def get_product_price(self, conn, product_id: int):
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT price
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        )
        return cursor.fetchone()

    def deduct_inventory(self, conn, product_id: int, quantity: int) -> int:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE inventory
            SET stock = stock - ?
            WHERE product_id = ?
            AND stock >= ?
            """,
            (quantity, product_id, quantity)
        )
        return cursor.rowcount

    def insert_order(
        self,
        conn,
        user_id: int,
        vendor_id: int,
        product_type: str,
        product_id: int,
        quantity: int,
        total_amount: float,
        status: str,
        idempotency_key: str,
    ) -> int:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO orders (
                user_id,
                vendor_id,
                product_type,
                product_id,
                quantity,
                total_amount,
                status,
                idempotency_key,
                created_at
            )
            OUTPUT INSERTED.order_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                vendor_id,
                product_type,
                product_id,
                quantity,
                total_amount,
                status,
                idempotency_key
            )
        )
        row = cursor.fetchone()
        return row[0] if row else None

    # ---------- ORDER STATUS ----------

    def get_order_for_update(self, conn, order_id: int):
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT product_id, quantity, status
            FROM orders WITH (UPDLOCK, ROWLOCK)
            WHERE order_id = ?
            """,
            (order_id,)
        )
        return cursor.fetchone()

    def update_order_status(self, conn, order_id: int, new_status: str):
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE orders
            SET status = ?
            WHERE order_id = ?
            """,
            (new_status, order_id)
        )

    # ---------- PRODUCTS ----------
    def get_all_products(self, conn):
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, price, category,image_url
            FROM products
            """
        )
        return cursor.fetchall()
    def get_orders_count(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        return cursor.fetchone()[0]
    def get_orders_paginated(self, conn, offset: int, size: int):
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                order_id,
                user_id,
                vendor_id,
                product_id,
                product_type,
                quantity,
                total_amount,
                status,
                idempotency_key,
                created_at
            FROM orders
            ORDER BY created_at DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
            """,
            (offset, size)
        )
        return cursor.fetchall()
    def get_order_by_id(self, conn, order_id: int):
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                order_id,
                user_id,
                vendor_id,
                product_id,
                quantity,
                total_amount,
                status,
                created_at
            FROM orders
            WHERE order_id = ?
            """,
            (order_id,)
        )
        return cursor.fetchone()
    def restock_inventory(self, conn, product_id: int, quantity: int):
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE inventory
            SET stock = stock + ?
            WHERE product_id = ?
            """,
            (quantity, product_id)
        )

        return cursor.rowcount
    def product_exists(self, conn, product_id: int):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM products WHERE id = ?",
            (product_id,)
        )
        return cursor.fetchone() is not None    
    def get_product_by_id(self, conn, product_id: int):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, price, category,image_url, created_at FROM products WHERE id = ?",
            (product_id,)
        )
        return cursor.fetchone()
    def update_product_price(self, conn, product_id: int, new_price: float):
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE products SET price = ? WHERE id = ?",
            (new_price, product_id)
        )
        return cursor.rowcount
    def delete_product(self, conn, product_id: int):
        cursor = conn.cursor()

        # delete inventory first
        cursor.execute(
            "DELETE FROM inventory WHERE product_id = ?",
            (product_id,)
        )

        # delete product
        cursor.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,)
        )

        return cursor.rowcount
    def restore_inventory(self, conn, product_id: int, quantity: int):
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE inventory
            SET stock = stock + ?
            WHERE product_id = ?
            """,
            (quantity, product_id)
        )
    def create_playwright(self, conn, name: str, skill: str):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO playwrights (name, skill) VALUES (?, ?)",
            (name, skill)
        )
    def get_playwrights(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, skill FROM playwrights")
        return cursor.fetchall()