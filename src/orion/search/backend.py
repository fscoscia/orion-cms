from functools import cache

from django.db import DatabaseError, connection


@cache
def has_trigram():
    """Whether PostgreSQL has pg_trgm, needed for approximate (fuzzy) search.

    Checked once per process: enabling it takes `manage.py enable_trigram` and a
    restart.
    """
    if connection.vendor != "postgresql":
        return False
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
            return cursor.fetchone() is not None
    except DatabaseError:
        return False
