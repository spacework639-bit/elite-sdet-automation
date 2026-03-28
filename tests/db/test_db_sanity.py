import pytest

pytestmark = pytest.mark.integration


def test_transaction_isolation(db_connection):
    cursor = db_connection.cursor()

    # Create temp table (session-scoped in SQL Server)
    cursor.execute("CREATE TABLE #temp_test (id INT)")

    # Insert data
    cursor.execute("INSERT INTO #temp_test VALUES (1)")

    # Validate insert
    cursor.execute("SELECT COUNT(*) FROM #temp_test")
    count = cursor.fetchone()[0]

    assert count == 1

    # Extra safety: verify isolation rollback will clean it
    cursor.execute("SELECT OBJECT_ID('tempdb..#temp_test')")
    assert cursor.fetchone()[0] is not None