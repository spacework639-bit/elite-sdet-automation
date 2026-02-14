from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Header
from typing import Dict
from .db import get_connection

load_dotenv()

app = FastAPI()

# -------------------------------------------------
# PLAYWRIGHTS APIs
# -------------------------------------------------

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


# -------------------------------------------------
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

    try:
        cursor = conn.cursor()
        conn.autocommit = False

        # ---- Fetch order ----
        cursor.execute(
            "SELECT product_id, quantity, status FROM orders WHERE order_id = ?",
            (order_id,)
        )
        order = cursor.fetchone()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        product_id, quantity, status = order

        # ---- Atomic state transition ----
        cursor.execute(
            """
            UPDATE orders
            SET status = 'cancelled'
            WHERE order_id = ?
            AND status = 'pending'
            """,
            (order_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=409, detail="Order cannot be cancelled")

        # ---- Restore inventory ----
        cursor.execute(
            """
            UPDATE inventory
            SET stock = stock + ?
            WHERE product_id = ?
            """,
            (quantity, product_id)
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
