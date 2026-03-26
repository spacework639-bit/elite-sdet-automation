from fastapi import HTTPException
import hashlib
import pyodbc
from backend.db import get_connection
from backend.repositories.user_repository import create_user, get_user_by_email


def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


def signup_user(email: str, password: str):
    conn = get_connection()
    email = email.lower().strip()
    password_hash = hash_password(password)

    try:
        user_id = create_user(conn, email, password_hash)
        conn.commit()
        return user_id

    except pyodbc.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=409, detail="User already exists")

    except Exception as e:
        conn.rollback()
        print("DEBUG ERROR:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        conn.close()


def login_user(email: str, password: str):
    conn = get_connection()
    email = email.lower().strip()

    try:
        user = get_user_by_email(conn, email)

        password_hash = hash_password(password)

        if not user or password_hash != user[2]:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return user[0]

    finally:
        conn.close()