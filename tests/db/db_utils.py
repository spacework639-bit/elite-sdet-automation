import psycopg2
from contextlib import contextmanager


def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="your_db",
        user="your_user",
        password="your_password"
    )


@contextmanager
def db_cursor():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()



def fetch_one(query, params=None):
    with db_cursor() as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()


def execute(query, params=None):
    with db_cursor() as cursor:
        cursor.execute(query, params or ())