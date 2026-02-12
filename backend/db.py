import pyodbc
import os
from contextlib import contextmanager


def _build_connection_string() -> str:
    required_vars = ["DB_SERVER", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [v for v in required_vars if not os.getenv(v)]

    if missing:
        raise RuntimeError(f"Missing DB environment variables: {missing}")

    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=5;"
    )


def get_connection():
    """
    Returns a new DB connection.
    Autocommit is disabled by default to allow explicit transaction control.
    """
    conn = pyodbc.connect(_build_connection_string())
    conn.autocommit = False
    return conn


@contextmanager
def db_session():
    """
    Context manager for DB sessions.
    Ensures commit/rollback safety.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
