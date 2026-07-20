import os
from pathlib import Path
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

if not DB_NAME or DB_NAME.lower() == "default":
    DB_NAME = "lianes_library"

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

ROOT_DIR = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT_DIR / "sql"
SCHEMA_FILE = SQL_DIR / "import.sql"


def get_connection(database: Optional[str] = None) -> mysql.connector.connection.MySQLConnection:
    config = DB_CONFIG.copy()
    if database is not None:
        config["database"] = database
    return mysql.connector.connect(**config)


def load_sql_file(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []

    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buffer))
            buffer = []

    if buffer:
        statements.append("\n".join(buffer))

    return statements


def initialize_schema() -> None:
    sql_text = load_sql_file(SCHEMA_FILE)
    sql_text = sql_text.replace("CREATE DATABASE IF NOT EXISTS lianes_library", f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
    sql_text = sql_text.replace("USE lianes_library;", f"USE `{DB_NAME}`;")

    statements = split_statements(sql_text)
    connection = get_connection(database=None)
    cursor = connection.cursor()

    try:
        for statement in statements:
            cursor.execute(statement)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def test_connection() -> bool:
    connection = get_connection()
    cursor = connection.cursor(buffered=True)
    try:
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True
    finally:
        cursor.close()
        connection.close()


def schema_exists() -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name IN ('books', 'borrowers', 'loans')",
            (DB_NAME,),
        )
        result = cursor.fetchone()
        return bool(result and result[0] >= 3)
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
