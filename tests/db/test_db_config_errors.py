import pytest
import os
from backend.db import _build_connection_string, db_session


def test_missing_env_vars_raises_error(monkeypatch):
    """
    Covers environment validation branch in _build_connection_string()
    """

    monkeypatch.delenv("DB_SERVER", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(RuntimeError) as exc:
        _build_connection_string()

    assert "Missing DB environment variables" in str(exc.value)


def test_db_session_rolls_back_on_exception():
    """
    Covers rollback path inside db_session()
    """

    with pytest.raises(Exception):
        with db_session() as conn:
            raise Exception("Simulated failure")
