from fastapi import HTTPException
from backend.domain.transitions import validate_transition
import pyodbc


def update_order_status(conn, repo, order_id: int, new_status: str, restore_inventory: bool = False):
    try:
        # ---- Lock row and fetch data ----
        row = repo.get_order_for_update(conn, order_id)

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

        # ---- Update status ----
        repo.update_order_status(conn, order_id, new_status)

        # ---- Optional inventory restore ----
        if restore_inventory:
            repo.restore_inventory(conn, product_id, quantity)

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
        raise

    except Exception:
        raise HTTPException(status_code=500, detail="Order status update failed")


def create_order_service(conn, repo, payload: dict, idempotency_key: str):
    product_id = payload.get("product_id")
    quantity = payload.get("quantity")
    user_id = payload.get("user_id", 91)
    vendor_id = payload.get("vendor_id", 1)

    # ---- Validation ----
    if not isinstance(product_id, int) or not isinstance(quantity, int):
        raise HTTPException(status_code=400, detail="product_id and quantity must be integers")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be positive")

    if not isinstance(user_id, int) or not isinstance(vendor_id, int):
        raise HTTPException(status_code=400, detail="user_id and vendor_id must be integers")

    try:
        # ---- Idempotency Check ----
        existing_order = repo.get_order_by_idempotency(conn, idempotency_key)

        if existing_order:
            return {
                "status": "order_already_created",
                "order_id": existing_order[0],
                "total_amount": float(existing_order[1])
            }

        # ---- Fetch Product Price ----
        product = repo.get_product_price(conn, product_id)

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        price = float(product[0])
        total_amount = price * quantity

        # ---- Atomic Inventory Deduction ----
        affected_rows = repo.deduct_inventory(conn, product_id, quantity)

        if affected_rows == 0:
            raise HTTPException(status_code=409, detail="Insufficient stock")

        # ---- Insert Order ----
        order_id = repo.insert_order(
            conn,
            user_id,
            vendor_id,
            "HERBAL",
            product_id,
            quantity,
            total_amount,
            "pending",
            idempotency_key
        )

        return {
            "status": "order_created",
            "order_id": int(order_id),
            "total_amount": total_amount
        }

    except HTTPException:
        raise

    except pyodbc.Error as e:
        error_text = str(e).lower()
        if "deadlock" in error_text or "1205" in error_text:
            raise HTTPException(status_code=409, detail="Concurrent stock conflict")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_products_service(conn, repo):
    rows = repo.get_all_products(conn)

    return [
        {
            "id": r[0],
            "name": r[1],
            "price": float(r[2]),
            "category": r[3]
        }
        for r in rows
    ]
def list_orders_service(conn, repo, page: int, size: int):
    offset = (page - 1) * size

    total = repo.get_orders_count(conn)
    rows = repo.get_orders_paginated(conn, offset, size)

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
def get_order_service(conn, repo, order_id: int):
    row = repo.get_order_by_id(conn, order_id)

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

def list_orders_service(conn, repo, page: int, size: int):
    offset = (page - 1) * size

    total = repo.get_orders_count(conn)
    rows = repo.get_orders_paginated(conn, offset, size)

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


def restock_inventory_service(conn, repo, product_id: int, quantity: int):

    # ---- Validation ----
    if not isinstance(product_id, int) or not isinstance(quantity, int):
        raise HTTPException(status_code=400, detail="product_id and quantity must be integers")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Restock quantity must be positive")

    # ---- Ensure product exists ----
    if not repo.product_exists(conn, product_id):
        raise HTTPException(status_code=404, detail="Product not found")

    # ---- Atomic update ----
    affected = repo.restock_inventory(conn, product_id, quantity)

    if affected == 0:
        # inventory row missing — serious integrity issue
        raise HTTPException(status_code=500, detail="Inventory record missing")

    return {
        "status": "inventory_restocked",
        "product_id": product_id,
        "added_quantity": quantity
    }

def update_product_price_service(conn, repo, product_id: int, new_price):

    # ---- Validation ----
    if not isinstance(new_price, (int, float)):
        raise HTTPException(status_code=400, detail="Price must be numeric")

    if new_price <= 0:
        raise HTTPException(status_code=400, detail="Price must be greater than zero")

    # ---- Check product exists ----
    product = repo.get_product_by_id(conn, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # ---- Update ----
    affected = repo.update_product_price(conn, product_id, new_price)

    if affected == 0:
        raise HTTPException(status_code=500, detail="Product update failed")

    # ---- Return updated product ----
    updated = repo.get_product_by_id(conn, product_id)

    return {
        "id": updated[0],
        "name": updated[1],
        "price": float(updated[2]),
        "category": updated[3],
        "created_at": updated[4]
    }
def delete_product_service(conn, repo, product_id: int):

    # ---- Existence check ----
    if not repo.product_exists(conn, product_id):
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        repo.delete_product(conn, product_id)

    except pyodbc.IntegrityError:
        # FK constraint from orders table
        raise HTTPException(
            status_code=409,
            detail="Cannot delete product with existing orders"
        )

    return {
        "status": "deleted",
        "product_id": product_id
    }

def create_playwright_service(conn, repo, name: str, skill: str):
    if not name or not skill:
        raise HTTPException(status_code=400, detail="name and skill are required")

    repo.create_playwright(conn, name, skill)

    return {"status": "created"}

def get_playwrights_service(conn, repo):
    rows = repo.get_playwrights(conn)

    return [
        {"id": r[0], "name": r[1], "skill": r[2]}
        for r in rows
    ]