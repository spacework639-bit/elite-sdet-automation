import os
import pyodbc
from contextlib import contextmanager


def _build_connection_string() -> str:
    """
    Builds SQL Server connection string from environment variables.
    Fails fast if required variables are missing.
    """
    required_vars = ["DB_SERVER", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise RuntimeError(f"Missing DB environment variables: {missing}")

    driver = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")

    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=5;"
    )


def get_connection():
    """
    Creates and returns a new database connection.
    Autocommit is disabled to allow explicit transaction handling.
    """
    connection = pyodbc.connect(_build_connection_string())
    connection.autocommit = False
    return connection


@contextmanager
def db_session():
    """
    Provides a transactional scope around a series of operations.
    Automatically commits on success and rolls back on failure.
    """
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()