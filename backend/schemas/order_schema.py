from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    user_id: int 
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    user_id: int = 91
    vendor_id: int = 1


class OrderResponse(BaseModel):
    order_id: int
    status: str
    total_amount: float

class OrderRequest(BaseModel):
    user_id: int
    vendor_id: int
    product_type: str
    product_id: int
    quantity: int
    total_amount: float