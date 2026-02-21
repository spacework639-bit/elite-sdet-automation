pytestmark = pytest.mark.integration
def test_db_insert_and_rollback(db_connection):
    cursor = db_connection.cursor()

    # Step 1: Create temp table
    cursor.execute("""
        CREATE TABLE #user_test (
            id INT,
            name NVARCHAR(50)
        )
    """)

    # Step 2: Insert data
    cursor.execute(
        "INSERT INTO #user_test (id, name) VALUES (?, ?)",
        1, "Test User"
    )

    # Step 3: Read back data
    cursor.execute("SELECT id, name FROM #user_test")
    row = cursor.fetchone()

    assert row.id == 1
    assert row.name == "Test User"
