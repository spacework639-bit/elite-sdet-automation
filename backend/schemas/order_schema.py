from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    user_id: int = 91
    vendor_id: int = 1


class OrderResponse(BaseModel):
    order_id: int
    status: str
    total_amount: float