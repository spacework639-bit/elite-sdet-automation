def fetch_one(cursor, query, params=None):
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    return cursor.fetchone()
