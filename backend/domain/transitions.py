from enum import Enum
from typing import Dict, Set


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    RETURN_REQUESTED = "return_requested"
    RETURNED = "returned"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


_ALLOWED_TRANSITIONS: Dict[OrderStatus, Set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: {OrderStatus.RETURN_REQUESTED},
    OrderStatus.RETURN_REQUESTED: {OrderStatus.RETURNED},
    OrderStatus.RETURNED: {OrderStatus.REFUNDED},
    OrderStatus.REFUNDED: set(),
    OrderStatus.CANCELLED: set(),
}


def validate_transition(current_status: str, new_status: str) -> None:
    try:
        current = OrderStatus(current_status.lower())
        new = OrderStatus(new_status.lower())
    except ValueError as e:
        raise ValueError("Invalid order status provided") from e

    if new not in _ALLOWED_TRANSITIONS[current]:
        raise ValueError(
            f"Invalid transition from {current.value} to {new.value}"
        )