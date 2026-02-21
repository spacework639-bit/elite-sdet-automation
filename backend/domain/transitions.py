ALLOWED_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["shipped", "cancelled"],
    "shipped": ["completed"],
    "completed": ["return_requested"],
    "return_requested": ["returned"],
    "returned": ["refunded"],
    "refunded": [],
    "cancelled": [],
}

def validate_transition(current_status: str, new_status: str) -> bool:
    allowed = ALLOWED_TRANSITIONS.get(current_status)

    if allowed is None:
        raise ValueError(f"Unknown current status: {current_status}")

    if new_status not in allowed:
        raise ValueError(
            f"Invalid transition from {current_status} to {new_status}"
        )

    return True