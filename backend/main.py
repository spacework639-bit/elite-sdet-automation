from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Header
from typing import Dict
from .db import get_connection
from fastapi import Query
import pyodbc
from backend.services.order_service import update_order_status, create_order_service
from backend.schemas.order_schema import CreateOrderRequest
from fastapi import status


load_dotenv()

app = FastAPI()
# -------------------------
# Health Endpoints
# -------------------------

@app.get("/health")
def liveness():
    return {"status": "alive"}


@app.get("/ready")
def readiness():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        return {"status": "ready"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database not reachable"
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
    return update_order_status(order_id, "confirmed")

#--------------------------------------------

@app.post("/orders/{order_id}/return-request")
def request_return(order_id: int):
      return update_order_status(order_id, "return_requested")
    
#-----------------------------------------------------

@app.post("/orders/{order_id}/return-received")
def receive_return(order_id: int):
     return update_order_status(order_id, "returned", restore_inventory=True)
   
# -------------------------------------------------

@app.post("/orders/{order_id}/refund")
def refund_order(order_id: int):
     return update_order_status(order_id, "refunded")
    
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
    payload: CreateOrderRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    return create_order_service(payload.model_dump(), idempotency_key)

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
     return update_order_status(order_id, "cancelled", restore_inventory=True)
  

@app.post("/orders/{order_id}/ship")
def ship_order(order_id: int):
    return update_order_status(order_id, "shipped")
   

@app.post("/orders/{order_id}/complete")
def complete_order(order_id: int):
    return update_order_status(order_id, "completed")
    

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