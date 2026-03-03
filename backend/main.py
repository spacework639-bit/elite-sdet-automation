from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Header
from typing import Dict
from .db import get_connection
from fastapi import Query
import pyodbc
from backend.services.order_service import update_order_status, create_order_service,list_orders_service
from backend.schemas.order_schema import CreateOrderRequest
from fastapi import status
from backend.repositories.order_repository import OrderRepository
from backend.services.order_service import get_products_service,get_order_service,restock_inventory_service,update_product_price_service,delete_product_service, create_playwright_service, get_playwrights_service
from backend.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

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
    return {"status": "ready"}
@app.post("/playwrights")
def create_playwright(payload: Dict):
    conn = get_connection()
    repo = OrderRepository()

    try:
        result = create_playwright_service(
            conn,
            repo,
            payload.get("name"),
            payload.get("skill")
        )
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.get("/playwrights")
def get_playwrights():
    conn = get_connection()
    repo = OrderRepository()

    try:
        return get_playwrights_service(conn, repo)
    finally:
        conn.close()

# -------------------------------------------------
# ORDERS API (CORE BUSINESS LOGIC)
# -------------------------------------------------

def execute_order_status(order_id: int, new_status: str, restore_inventory: bool = False):
    conn = get_connection()
    repo = OrderRepository()

    try:
        result = update_order_status(conn, repo, order_id, new_status, restore_inventory)
        conn.commit()
        return result
    except:
        conn.rollback()
        raise
    finally:
        conn.close()

@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    return execute_order_status(order_id, "confirmed")

@app.post("/orders/{order_id}/return-request")
def request_return(order_id: int):
    return execute_order_status(order_id, "return_requested")

@app.post("/orders/{order_id}/return-received")
def receive_return(order_id: int):
    return execute_order_status(order_id, "returned", restore_inventory=True)

@app.post("/orders/{order_id}/refund")
def refund_order(order_id: int):
    return execute_order_status(order_id, "refunded")

@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int):
    return execute_order_status(order_id, "cancelled", restore_inventory=True)

@app.post("/orders/{order_id}/ship")
def ship_order(order_id: int):
    return execute_order_status(order_id, "shipped")

@app.post("/orders/{order_id}/complete")
def complete_order(order_id: int):
    return execute_order_status(order_id, "completed")    
#--------------------------------------------------------------------------
# PRODUCTS API
# -------------------------------------------------
@app.get("/products")
def get_products():
    conn = get_connection()
    repo = OrderRepository()

    try:
        return get_products_service(conn, repo)
    finally:
        conn.close()


    # -------------------------------------------------
    # ORDERS API (CORE BUSINESS LOGIC)
    # -------------------------------------------------
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    conn = get_connection()
    repo = OrderRepository()

    try:
        return get_order_service(conn, repo, order_id)
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
    conn = get_connection()
    repo = OrderRepository()

    try:
        return list_orders_service(conn, repo, page, size)
    finally:
        conn.close()

@app.patch("/products/{product_id}")
def update_product_price(product_id: int, payload: Dict):

    conn = get_connection()
    repo = OrderRepository()

    try:
        result = update_product_price_service(
            conn,
            repo,
            product_id,
            payload.get("price")
        )

        conn.commit()
        return result

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
@app.delete("/products/{product_id}")
def delete_product(product_id: int):

    conn = get_connection()
    repo = OrderRepository()

    try:
        result = delete_product_service(conn, repo, product_id)
        conn.commit()
        return result

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

@app.post("/inventory/restock")
def restock_inventory(payload: Dict):
    conn = get_connection()
    repo = OrderRepository()

    try:
        result = restock_inventory_service(
            conn,
            repo,
            payload.get("product_id"),
            payload.get("quantity")
        )

        conn.commit()
        return result

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
@app.get("/products/{product_id}")
def get_product(product_id: int):
    conn = get_connection()
    repo = OrderRepository()

    try:
        row = repo.get_product_by_id(conn, product_id)

        if not row:
            raise HTTPException(status_code=404, detail="Product not found")

        return {
            "product_id": row[0],
            "name": row[1],
            "price": float(row[2]),
            "category": row[3],
            "created_at": row[4]
        }

    finally:
        conn.close()


@app.post("/orders")
def create_order(
    payload: CreateOrderRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    conn = get_connection()
    repo = OrderRepository()

    try:
        result = create_order_service(
            conn,
            repo,
            payload.model_dump(),
            idempotency_key
        )
        conn.commit()
        return result
    except:
        conn.rollback()
        raise
    finally:
        conn.close()