from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Header
from typing import Dict
from .db import get_connection


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
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        title="Idempotency-Key",
        description="Unique key to ensure the request is idempotent (prevents duplicate orders if retried)",
        example="idem-test-123"
    )
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

    # No need to check idempotency_key == None anymore — FastAPI already enforces it
    # (because we used Header(...) with ... which means required)

    conn = get_connection()

    try:
        cursor = conn.cursor()
        conn.autocommit = False

        # ---------- PRODUCT ----------
        # STEP 4: check existing order (PASTE HERE)
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

        # EXISTING CODE CONTINUES BELOW
    
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if product[0] is None:
            raise HTTPException(status_code=500, detail="Product price is NULL")

        price = float(product[0])
        total_amount = price * quantity

        # ---------- INVENTORY (LOCK ROW) ----------
        # ---------- ATOMIC INVENTORY UPDATE ----------
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
            raise HTTPException(
                status_code=409,
                detail="Insufficient stock"
    )


        # ---------- INSERT ORDER (CORRECT SQL SERVER PATTERN) ----------
        cursor.execute(
            """
            INSERT INTO orders (
                user_id,
                vendor_id,
                product_type,
                product_id,
                total_amount,
                status,
                idempotency_key,
                created_at
            )
            OUTPUT INSERTED.order_id
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                vendor_id,
                "HERBAL",
                product_id,
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