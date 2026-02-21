from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Header
from typing import Dict
from .db import get_connection
from fastapi import Query
import pyodbc

load_dotenv()

app = FastAPI()

# -------------------------------------------------
# PLAYWRIGHTS APIs
# -------------------------------------------------
ALLOWED_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["shipped", "cancelled"],
    "shipped": ["completed"],
    "completed": ["return_requested"],
    "return_requested": ["returned"],
    "returned": ["refunded"],
    "cancelled": [],
    "refunded": []
}
def validate_transition(current_status: str, new_status: str):
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Invalid transition from {current_status} to {new_status}"
        )
@app.post("/playwrights")
def create_playwright(payload: Dict):
    name = payload.get("name")
    skill = payload.get("skill")

    if not name or not skill:
        raise HTTPException(status_code=400, detail="name and skill are required")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO playwrights (name, skill) VALUES (?, ?)",
            (name, skill)
        )
        conn.commit()
        return {"status": "created"}
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to create playwright")
    finally:
        conn.close()


@app.get("/playwrights")
def get_playwrights():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, skill FROM playwrights")
        rows = cursor.fetchall()
        return [{"id": r[0], "name": r[1], "skill": r[2]} for r in rows]
    finally:
        conn.close()
@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Begin transaction explicitly
        conn.autocommit = False

        # Lock row to prevent race condition
        cursor.execute(
            "SELECT status FROM Orders WITH (UPDLOCK, ROWLOCK) WHERE order_id = ?",
            order_id
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        current_status = row[0]

        # Idempotent behavior:
        if current_status == "confirmed":
            return {"message": "Order already confirmed"}

        # Validate transition
        validate_transition(current_status, "confirmed")

        # Update status
        cursor.execute(
            "UPDATE Orders SET status = ? WHERE order_id = ?",
            "confirmed",
            order_id
        )

        conn.commit()

        return {"message": "Order confirmed successfully"}

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        print("CONFIRM ERROR:", str(e))
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()

#--------------------------------------------

@app.post("/orders/{order_id}/return-request")
def request_return(order_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        cursor.execute(
            """
            SELECT status
            FROM orders WITH (UPDLOCK, ROWLOCK)
            WHERE order_id = ?
            """,
            order_id
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        current_status = row[0]

        if current_status == "return_requested":
            return {"message": "Return already requested"}

        validate_transition(current_status, "return_requested")

        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            "return_requested",
            order_id
        )

        conn.commit()

        return {"message": "Return requested successfully"}

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Return request failed")

    finally:
        conn.close()
#-----------------------------------------------------

@app.post("/orders/{order_id}/return-received")
def receive_return(order_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        # Lock row
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

        if current_status == "returned":
            return {"message": "Return already processed"}

        validate_transition(current_status, "returned")

        # Update status
        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            "returned",
            order_id
        )

        # Restore inventory
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

        return {"message": "Return received and inventory restored"}

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Return processing failed")

    finally:
        conn.close()
# -------------------------------------------------

@app.post("/orders/{order_id}/refund")
def refund_order(order_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        cursor.execute(
            """
            SELECT status
            FROM orders WITH (UPDLOCK, ROWLOCK)
            WHERE order_id = ?
            """,
            order_id
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        current_status = row[0]

        if current_status == "refunded":
            return {"message": "Order already refunded"}

        validate_transition(current_status, "refunded")

        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            "refunded",
            order_id
        )

        conn.commit()

        return {"message": "Order refunded successfully"}

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Refund failed")

    finally:
        conn.close()

#--------------------------------------------------------------------------
# PRODUCTS API
# -------------------------------------------------

@app.get("/products")
def get_products():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, category FROM products")
        cursor.execute("SELECT DB_NAME()")
        print("APP DB:", cursor.fetchone()[0])

        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "price": float(r[2]),
                "category": r[3]
            }
            for r in rows
        ]
    finally:
        conn.close()


# -------------------------------------------------
# ORDERS API (CORE BUSINESS LOGIC)
# -------------------------------------------------

@app.post("/orders")
def create_order(
    payload: Dict,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    product_id = payload.get("product_id")
    quantity = payload.get("quantity")
    user_id = payload.get("user_id", 91)
    vendor_id = payload.get("vendor_id", 1)

    # ---------- VALIDATION ----------
    if not isinstance(product_id, int) or not isinstance(quantity, int):
        raise HTTPException(status_code=400, detail="product_id and quantity must be integers")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be positive")

    if not isinstance(user_id, int) or not isinstance(vendor_id, int):
        raise HTTPException(status_code=400, detail="user_id and vendor_id must be integers")

    conn = get_connection()

    try:
        cursor = conn.cursor()
        conn.autocommit = False
        cursor.execute("SELECT DB_NAME()")
        print("PYTEST CONNECTED DB:", cursor.fetchone()[0])

        # ---------- Idempotency Check ----------
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

        # ---------- Get Product ----------
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        price = float(product[0])
        total_amount = price * quantity

        # ---------- Atomic Inventory Deduction ----------
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

        # ---------- Insert Order ----------
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
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Order creation failed")
    finally:
        conn.close()


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    conn = get_connection()
    try:
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

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        return {
            "order_id": row[0],
            "user_id": row[1],
            "vendor_id": row[2],
            "product_id": row[3],
            "quantity": row[4],
            "total_amount": float(row[5]),
            "status": row[6],
            "created_at": row[7]
        }

    finally:
        conn.close()


@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        # ---- Lock and Fetch Order ----
        cursor.execute(
            """
            SELECT product_id, quantity, status
            FROM orders WITH (UPDLOCK, ROWLOCK)
            WHERE order_id = ?
            """,
            order_id
        )
        order = cursor.fetchone()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        product_id, quantity, current_status = order

        # ---- Idempotent Behavior ----
        if current_status == "cancelled":
            return {
                "status": "already_cancelled",
                "order_id": order_id
            }

        # ---- Validate Transition ----
        validate_transition(current_status, "cancelled")

        # ---- Update Order Status ----
        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            "cancelled",
            order_id
        )

        # ---- Restore Inventory ----
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

        return {
            "status": "order_cancelled",
            "order_id": order_id
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Order cancellation failed")

    finally:
        conn.close()


@app.post("/orders/{order_id}/ship")
def ship_order(order_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        cursor.execute(
            """
            SELECT status
            FROM orders WITH (UPDLOCK, ROWLOCK)
            WHERE order_id = ?
            """,
            order_id
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        current_status = row[0]

        if current_status == "shipped":
            return {"message": "Order already shipped"}

        validate_transition(current_status, "shipped")

        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            "shipped",
            order_id
        )

        conn.commit()

        return {"message": "Order shipped successfully"}

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Shipping failed")

    finally:
        conn.close()

@app.post("/orders/{order_id}/complete")
def complete_order(order_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        cursor.execute(
            """
            SELECT status
            FROM orders WITH (UPDLOCK, ROWLOCK)
            WHERE order_id = ?
            """,
            order_id
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        current_status = row[0]

        if current_status == "completed":
            return {"message": "Order already completed"}

        validate_transition(current_status, "completed")

        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            "completed",
            order_id
        )

        conn.commit()

        return {"message": "Order completed successfully"}

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Completion failed")

    finally:
        conn.close()

@app.get("/orders")
def list_orders(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """
    List orders with pagination.
    Ordered by newest first.
    Returns total count + paginated data.
    """

    offset = (page - 1) * size

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # ---- Get total count ----
        cursor.execute("SELECT COUNT(*) FROM orders")
        total = cursor.fetchone()[0]

        # ---- Fetch paginated rows ----
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

        rows = cursor.fetchall()

        orders = [
            {
                "order_id": r[0],
                "user_id": r[1],
                "vendor_id": r[2],
                "product_id": r[3],
                "product_type": r[4],
                "quantity": r[5],
                "total_amount": float(r[6]),
                "status": r[7],
                "idempotency_key": r[8],
                "created_at": r[9]
            }
            for r in rows
        ]

        return {
            "page": page,
            "size": size,
            "total": total,
            "orders": orders
        }

    finally:
        conn.close()

@app.patch("/products/{product_id}")
def update_product_price(product_id: int, payload: Dict):
    """
    Update product price.
    """

    new_price = payload.get("price")

    # ---- Validation ----
    if not isinstance(new_price, (int, float)):
        raise HTTPException(status_code=400, detail="Price must be numeric")

    if new_price <= 0:
        raise HTTPException(status_code=400, detail="Price must be greater than zero")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        conn.autocommit = False

        # ---- Check product exists ----
        cursor.execute(
            "SELECT id, name, price, category, created_at FROM products WHERE id = ?",
            (product_id,)
        )
        product = cursor.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # ---- Update price ----
        cursor.execute(
            "UPDATE products SET price = ? WHERE id = ?",
            (new_price, product_id)
        )

        conn.commit()

        # ---- Return updated product ----
        cursor.execute(
            "SELECT id, name, price, category, created_at FROM products WHERE id = ?",
            (product_id,)
        )
        updated = cursor.fetchone()

        return {
            "id": updated[0],
            "name": updated[1],
            "price": float(updated[2]),
            "category": updated[3],
            "created_at": updated[4]
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Product update failed")
    finally:
        conn.close()
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    conn = get_connection()
    conn.autocommit = False

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Product not found")

        try:
            cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
        except pyodbc.IntegrityError:
            conn.rollback()
            raise HTTPException(
                status_code=409,
                detail="Cannot delete product with existing orders"
            )

        return {"status": "deleted", "product_id": product_id}

    finally:
        conn.close()

@app.post("/inventory/restock")
def restock_inventory(payload: Dict):
    product_id = payload.get("product_id")
    quantity = payload.get("quantity")

    if not isinstance(product_id, int) or not isinstance(quantity, int):
        raise HTTPException(status_code=400, detail="product_id and quantity must be integers")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Restock quantity must be positive")

    conn = get_connection()

    try:
        cursor = conn.cursor()
        conn.autocommit = False

        # ---- Check product exists ----
        cursor.execute(
            "SELECT id FROM products WHERE id = ?",
            (product_id,)
        )
        product = cursor.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # ---- Increase stock atomically ----
        cursor.execute(
            """
            UPDATE inventory
            SET stock = stock + ?
            WHERE product_id = ?
            """,
            (quantity, product_id)
        )

        # ---- Get updated stock ----
        cursor.execute(
            "SELECT stock FROM inventory WHERE product_id = ?",
            (product_id,)
        )
        updated_stock = cursor.fetchone()[0]

        conn.commit()

        return {
            "status": "inventory_restocked",
            "product_id": product_id,
            "new_stock": updated_stock
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Inventory restock failed")
    finally:
        conn.close()

@app.get("/products/{product_id}")
def get_product(product_id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                id,
                name,
                price,
                category,
                created_at
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return {
            "product_id": row[0],
            "name": row[1],
            "price": float(row[2]),
            "category": row[3],
            "created_at": row[4]
        }

    finally:
        conn.close()