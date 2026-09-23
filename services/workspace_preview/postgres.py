"""PostgreSQL boundary for the existing workspace SQL contract.

Application SQL uses qmark parameters, portable upserts and a small json_extract
compatibility function. A transaction advisory lock preserves the preview's
single-writer semantics across Cloud Run instances until finer locks are needed.
No connection strings or database errors are returned to callers.
"""
from contextlib import contextmanager
import re
import sqlite3


class Row(dict):
    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


def row_factory(cursor):
    names = [c.name for c in cursor.description] if cursor.description else []
    return lambda values: Row(zip(names, values))


def parameters(sql):
    # Only replace placeholders outside SQL string literals. SQL is application-owned.
    return ''.join(piece if i % 2 else piece.replace('?', '%s')
                   for i, piece in enumerate(re.split("('(?:[^']|'')*')", sql)))


class Connection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, sql, values=()):
        if sql.strip().upper() == 'BEGIN IMMEDIATE':
            return self.connection.execute('SELECT pg_advisory_xact_lock(910004733138)')
        if sql.strip().upper() == 'BEGIN':
            return self.connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        return self.connection.execute(parameters(sql), values)


class PostgreSQLStorage:
    def __init__(self, dsn):
        if not dsn:
            raise ValueError('Database connection is required')
        self.dsn = dsn

    @contextmanager
    def connect(self):
        import psycopg
        try:
            with psycopg.connect(self.dsn, row_factory=row_factory, connect_timeout=10) as connection:
                connection.execute("SET statement_timeout = '15s'")
                connection.execute("SET lock_timeout = '5s'")
                yield Connection(connection)
        except psycopg.Error as error:
            raise sqlite3.DatabaseError('Database operation failed') from error

    def initialize(self):
        with self.connect() as db:
            db.execute("""CREATE OR REPLACE FUNCTION json_extract(document TEXT, path TEXT)
                RETURNS TEXT LANGUAGE SQL IMMUTABLE STRICT AS $$
                SELECT document::jsonb #>> string_to_array(substr(path, 3), '.')
                $$""")
