import os
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

import mysql.connector
import pandas as pd

MYSQL_URL = os.getenv("MYSQL_URL")
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "library_user")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "library_password")
DB_NAME = os.getenv("MYSQL_DATABASE", "lianes_library")

if MYSQL_URL:
    parsed = urlparse(MYSQL_URL)
    if parsed.scheme.startswith("mysql"):
        DB_HOST = parsed.hostname or DB_HOST
        DB_PORT = parsed.port or DB_PORT
        DB_USER = parsed.username or DB_USER
        DB_PASSWORD = parsed.password or DB_PASSWORD
        DB_NAME = parsed.path.lstrip("/") or DB_NAME

if not DB_NAME:
    DB_NAME = "default"

DB_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
}

SAFE_CONFIG = {
    **DB_CONFIG,
    "password": "***" if DB_PASSWORD else "",
}


def get_connection(database: Optional[str] = None) -> mysql.connector.connection.MySQLConnection:
    config = DB_CONFIG.copy()
    if database is None:
        config.pop("database", None)
    else:
        config["database"] = database
    return mysql.connector.connect(**config)


def test_connection() -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT 1")
        return True
    finally:
        cursor.close()
        connection.close()


def execute_statement(sql: str, params: Optional[Iterable[Any]] = None, database: Optional[str] = None) -> int:
    connection = get_connection(database)
    cursor = connection.cursor()

    try:
        cursor.execute(sql, params or ())
        connection.commit()
        return cursor.rowcount
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def execute_many(sql: str, parameter_rows: Iterable[Iterable[Any]], database: Optional[str] = None) -> int:
    connection = get_connection(database)
    cursor = connection.cursor()

    try:
        cursor.executemany(sql, list(parameter_rows))
        connection.commit()
        return cursor.rowcount
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def query_dataframe(sql: str, params: Optional[Iterable[Any]] = None, database: Optional[str] = None) -> pd.DataFrame:
    connection = get_connection(database)
    try:
        return pd.read_sql(sql, connection, params=params)
    finally:
        connection.close()
