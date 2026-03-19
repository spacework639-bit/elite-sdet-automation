import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL
from dotenv import load_dotenv

load_dotenv()


# -----------------------------
# Helper: Build server string with optional port
# -----------------------------
def _build_server_with_port() -> str:
    server = os.getenv("DB_SERVER")
    port = os.getenv("DB_PORT")

    if not server:
        raise RuntimeError("Missing required DB_SERVER environment variable")

    if port:
        return f"{server},{port}"  # SQL Server requires comma
    return server


# -----------------------------
# Legacy Connection String Builder (for tests)
# -----------------------------
def _build_connection_string() -> str:
    required_vars = ["DB_SERVER", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise RuntimeError(f"Missing DB environment variables: {missing}")

    driver = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    server_with_port = _build_server_with_port()

    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={server_with_port};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=5;"
    )


# -----------------------------
# SQLAlchemy Engine (Pooled)
# -----------------------------
driver = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
server_with_port = _build_server_with_port()

connection_url = URL.create(
    "mssql+pyodbc",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=server_with_port,
    database=os.getenv("DB_NAME"),
    query={
        "driver": driver,
        "TrustServerCertificate": "yes",
    },
)

engine: Engine = create_engine(
    connection_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)


def get_connection():
    conn = engine.raw_connection()
    conn.autocommit = False
    return conn

# -----------------------------
# Legacy db_session (for tests)
# -----------------------------
@contextmanager
def db_session():
    """
    Provides transactional scope for compatibility.
    Uses pooled connection underneath.
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