def test_transaction_isolation(db_connection):
    cursor = db_connection.cursor()

    cursor.execute("CREATE TABLE #temp_test (id INT)")
    cursor.execute("INSERT INTO #temp_test VALUES (1)")

    cursor.execute("SELECT COUNT(*) FROM #temp_test")
    count = cursor.fetchone()[0]

    assert count == 1
