import os
import pytest
import pyodbc
from datetime import datetime
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from backend.main import app
import logging  

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)





# -------------------------------------------------
# DATABASE CONNECTION FIXTURE
# -------------------------------------------------
@pytest.fixture(scope="function")
def db_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    assert server, "DB_SERVER not set"
    assert database, "DB_NAME not set"
    assert username, "DB_USER not set"
    assert password, "DB_PASSWORD not set"

    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
    )

    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


# -------------------------------------------------
# API CLIENT FIXTURE
# -------------------------------------------------
@pytest.fixture(scope="session")
def api_client():
    return TestClient(app)



# -------------------------------------------------
# DETERMINISTIC TEST PRODUCT FIXTURE (FIXED)
# -------------------------------------------------
@pytest.fixture(scope="function")
def test_product(db_connection):
    """
    Creates a clean product + inventory for each test.
    Respects SQL Server IDENTITY rules.
    """

    cursor = db_connection.cursor()
    initial_stock = 10

    # Cleanup old test data safely (by name, not ID)
    cursor.execute("""
        DELETE FROM orders
        WHERE product_id IN (
            SELECT id FROM products WHERE name = 'E2E Test Product'
        )
    """)
    cursor.execute("""
        DELETE FROM inventory
        WHERE product_id IN (
            SELECT id FROM products WHERE name = 'E2E Test Product'
        )
    """)
    cursor.execute("DELETE FROM products WHERE name = 'E2E Test Product'")

    # Insert product (NO explicit ID)
    cursor.execute(
        """
        INSERT INTO products (name, price, category)
        OUTPUT INSERTED.id
        VALUES ('E2E Test Product', 20.00, 'HERBAL')
        """
    )
    product_id = cursor.fetchone()[0]

    # Insert inventory
    cursor.execute(
        "INSERT INTO inventory (product_id, stock) VALUES (?, ?)",
        (product_id, initial_stock)
    )

    db_connection.commit()

    yield {
        "product_id": product_id,
        "initial_stock": initial_stock
    }

    # Cleanup after test
    cursor.execute("DELETE FROM orders WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db_connection.commit()
# -------------------------------------------------

# -------------------------------------------------
# SCREENSHOT + REPORT HOOK
# -------------------------------------------------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if call.when == "call":
        item.rep_call = rep

        page = item.funcargs.get("page")

        # Detect real failure OR expected failure
        is_failed = rep.failed
        is_xfailed = hasattr(rep, "wasxfail")

        if page and (is_failed or is_xfailed):

            os.makedirs("reports/screenshots", exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            status_tag = "FAILED" if is_failed else "XFAILED"

            screenshot_path = (
                f"reports/screenshots/{item.name}_{status_tag}_{timestamp}.png"
            )

            page.screenshot(path=screenshot_path, full_page=True)

            # Attach screenshot path to test item for Excel
            item.screenshot_path = screenshot_path


def pytest_sessionfinish(session, exitstatus):
    from reporting.excel_report import generate_report
    generate_report(session)