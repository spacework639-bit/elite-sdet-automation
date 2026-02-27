from fastapi import HTTPException
from backend.db import get_connection
from backend.domain.transitions import validate_transition


def update_order_status(order_id: int, new_status: str, restore_inventory: bool = False):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        # Lock row and fetch required data
        cursor.execute(
            """
            SELECT product_id, quantity, status
            FROM orders WITH (UPDLOCK, ROWLOCK)
            WHERE order_id = ?
            """,
            order_id
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        product_id, quantity, current_status = row

        # ---- Idempotent behavior ----
        if current_status == new_status:
            return {
                "status": f"already_{new_status}",
                "order_id": order_id
            }

        # ---- Validate transition ----
        try:
            validate_transition(current_status, new_status)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        # ---- Update order status ----
        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            new_status,
            order_id
        )

        # ---- Optional inventory restore ----
        if restore_inventory:
            cursor.execute(
                """
                UPDATE inventory
                SET stock = stock + ?
                WHERE product_id = ?
                """,
                quantity,
                product_id
            )

        conn.commit()

        # ---- Preserve original API contract ----
        status_mapping = {
            "confirmed": "order_confirmed",
            "shipped": "order_shipped",
            "completed": "order_completed",
            "cancelled": "order_cancelled",
            "refunded": "order_refunded",
            "return_requested": "return_requested",
            "returned": "return_processed",
        }

        return {
            "status": status_mapping.get(new_status, new_status),
            "order_id": order_id
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Order status update failed")

    finally:
        conn.close()
def create_order_service(payload: dict, idempotency_key: str):
    product_id = payload.get("product_id")
    quantity = payload.get("quantity")
    user_id = payload.get("user_id", 91)
    vendor_id = payload.get("vendor_id", 1)

    if not isinstance(product_id, int) or not isinstance(quantity, int):
        raise HTTPException(status_code=400, detail="product_id and quantity must be integers")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be positive")

    if not isinstance(user_id, int) or not isinstance(vendor_id, int):
        raise HTTPException(status_code=400, detail="user_id and vendor_id must be integers")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        # ---- Idempotency Check ----
        cursor.execute(
            """
            SELECT order_id, total_amount
            FROM orders
            WHERE idempotency_key = ?
            """,
            (idempotency_key,)
        )
        existing_order = cursor.fetchone()

        if existing_order:
            return {
                "status": "order_already_created",
                "order_id": existing_order[0],
                "total_amount": float(existing_order[1])
            }

        # ---- Get Product Price ----
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        price = float(product[0])
        total_amount = price * quantity

        # ---- Atomic Inventory Deduction ----
        cursor.execute(
            """
            UPDATE inventory
            SET stock = stock - ?
            WHERE product_id = ?
            AND stock >= ?
            """,
            (quantity, product_id, quantity)
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=409, detail="Insufficient stock")

        # ---- Insert Order ----
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
                "HERBAL",
                product_id,
                quantity,
                total_amount,
                "pending",
                idempotency_key
            )
        )

        order_id = cursor.fetchone()[0]

        conn.commit()

        return {
            "status": "order_created",
            "order_id": int(order_id),
            "total_amount": total_amount
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        conn.close()