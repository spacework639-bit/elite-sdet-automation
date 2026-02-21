import pytest
from backend.domain.transitions import validate_transition


@pytest.mark.unit
def test_valid_transition_pending_to_confirmed():
    assert validate_transition("pending", "confirmed") is True


@pytest.mark.unit
def test_invalid_transition_cancelled_to_confirmed():
    with pytest.raises(ValueError):
        validate_transition("cancelled", "confirmed")


@pytest.mark.unit
def test_unknown_status():
    with pytest.raises(ValueError):
        validate_transition("invalid_status", "confirmed")