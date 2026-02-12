def test_db_metadata(db_connection):
    cursor = db_connection.cursor()

    cursor.execute("SELECT DB_NAME(), @@VERSION")
    db_name, version = cursor.fetchone()

    assert db_name == "TravelXDB"
    assert "Microsoft SQL Server" in version
