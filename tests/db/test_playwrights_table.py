import pytest
pytestmark = pytest.mark.integration
def test_playwrights_insert_and_rollback(db_connection):
    cursor = db_connection.cursor()

    cursor.execute(
        """
        INSERT INTO playwrights (name, skill)
        VALUES (?, ?)
        """,
        ("Test User", "Playwright")
    )

    cursor.execute(
        """
        SELECT name, skill
        FROM playwrights
        WHERE name = ?
        """,
        ("Test User",)
    )

    row = cursor.fetchone()

    assert row is not None
    assert row[0] == "Test User"
    assert row[1] == "Playwright"
