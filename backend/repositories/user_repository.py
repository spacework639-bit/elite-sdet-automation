from fastapi import HTTPException
from backend.db import get_connection
import hashlib

def create_user(conn, email, password_hash):
    cursor = conn.cursor()

    query = """
    INSERT INTO users_elite (email, password_hash)
    OUTPUT INSERTED.id
    VALUES (?, ?)
    """

    cursor.execute(query, (email, password_hash))
    row = cursor.fetchone()
    return row[0]


def get_user_by_email(conn, email):
    cursor = conn.cursor()

    query = """
    SELECT id, email, password_hash
    FROM users_elite
    WHERE email = ?
    """

    cursor.execute(query, (email,))
    return cursor.fetchone()

def login_user(email: str, password: str):

    conn = get_connection()

    try:
        user = get_user_by_email(conn, email)

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if not user or password_hash != user[2]:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return user[0]

    finally:
        conn.close()