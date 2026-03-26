import pytest
from backend.domain.transitions import validate_transition


@pytest.mark.unit
def test_valid_transition_pending_to_confirmed():
    validate_transition("pending", "confirmed")


@pytest.mark.unit
def test_invalid_transition_cancelled_to_confirmed():
    with pytest.raises(ValueError):
        validate_transition("cancelled", "confirmed")


@pytest.mark.unit
def test_unknown_current_status():
    with pytest.raises(ValueError):
        validate_transition("invalid_status", "confirmed")


@pytest.mark.unit
def test_invalid_new_status():
    with pytest.raises(ValueError):
        validate_transition("pending", "ghost")


@pytest.mark.unit
def test_terminal_state_refunded():
    with pytest.raises(ValueError):
        validate_transition("refunded", "confirmed")


@pytest.mark.unit
def test_same_status_not_allowed():
    with pytest.raises(ValueError):
        validate_transition("pending", "pending")