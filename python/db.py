import datetime
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


def get_connection(database: Optional[str] = DB_NAME) -> mysql.connector.connection.MySQLConnection:
    config = DB_CONFIG.copy()
    if database is None:
        config.pop("database")
    else:
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


def prepare_schema_statements(db_exists: bool) -> list[str]:
    sql_text = load_sql_file(SCHEMA_FILE)
    statements = split_statements(sql_text)

    if db_exists:
        filtered = [
            stmt for stmt in statements
            if not stmt.strip().upper().startswith("CREATE DATABASE")
            and not stmt.strip().upper().startswith("USE ")
        ]
        return filtered

    replaced = [
        stmt.replace("CREATE DATABASE IF NOT EXISTS lianes_library", f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
            .replace("USE lianes_library;", f"USE `{DB_NAME}`;")
        for stmt in statements
    ]
    return replaced


def initialize_schema() -> None:
    db_exists = database_exists()
    if db_exists:
        connection = get_connection(database=DB_NAME)
        statements = prepare_schema_statements(db_exists=True)
    else:
        connection = get_connection(database=None)
        statements = prepare_schema_statements(db_exists=False)

    cursor = connection.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
        connection.commit()
    except mysql.connector.Error as err:
        connection.rollback()
        error_msg = str(err).lower()
        if db_exists:
            raise RuntimeError(
                "Schema-Initialisierung fehlgeschlagen. Der Benutzer kann die vorhandene Datenbank nicht verwenden oder hat keine Rechte zum Erstellen von Tabellen. "
                f"Original: {err}"
            ) from err
        raise RuntimeError(
            "Schema-Initialisierung fehlgeschlagen. Der Benutzer kann die Datenbank nicht erstellen oder verwenden. "
            "Falls die Datenbank bereits existiert, setze die Verbindungsdaten so, dass du darauf zugreifen darfst. "
            f"Original: {err}"
        ) from err
    finally:
        cursor.close()
        connection.close()


def seed_sample_data_if_empty() -> bool:
    """Create a small demo dataset once, but never mix it into existing data."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT "
            "(SELECT COUNT(*) FROM books), "
            "(SELECT COUNT(*) FROM borrowers), "
            "(SELECT COUNT(*) FROM loans)"
        )
        counts = cursor.fetchone()
        if counts is None or any(counts):
            return False

        books = [
            ("Der Gesang der Flusskrebse", "Delia Owens", "9783453424011", "Roman", "Regal A1"),
            ("Die Mitternachtsbibliothek", "Matt Haig", "9783426282564", "Roman", "Regal A2"),
            ("Eine kurze Geschichte der Menschheit", "Yuval Noah Harari", "9783570552698", "Sachbuch", "Regal B1"),
            ("Der kleine Prinz", "Antoine de Saint-Exupéry", "9783792000496", "Klassiker", "Regal C1"),
        ]
        cursor.executemany(
            """
            INSERT INTO books (title, author, isbn, category, shelf_location)
            VALUES (%s, %s, %s, %s, %s)
            """,
            books,
        )

        borrowers = [
            ("Anna Schmidt", "anna.schmidt@example.com", "0151 12345678", "Freundin"),
            ("Max Müller", "max.mueller@example.com", "0170 87654321", "Familie"),
            ("Sofia Wagner", "sofia.wagner@example.com", "0160 24681357", "Kollegin"),
        ]
        cursor.executemany(
            """
            INSERT INTO borrowers (name, email, phone, relationship)
            VALUES (%s, %s, %s, %s)
            """,
            borrowers,
        )

        cursor.execute("SELECT book_id FROM books WHERE isbn = %s", (books[0][2],))
        open_book_id = cursor.fetchone()[0]
        cursor.execute("SELECT book_id FROM books WHERE isbn = %s", (books[3][2],))
        returned_book_id = cursor.fetchone()[0]
        cursor.execute("SELECT borrower_id FROM borrowers WHERE email = %s", (borrowers[0][1],))
        first_borrower_id = cursor.fetchone()[0]
        cursor.execute("SELECT borrower_id FROM borrowers WHERE email = %s", (borrowers[1][1],))
        second_borrower_id = cursor.fetchone()[0]

        today = datetime.date.today()
        cursor.executemany(
            """
            INSERT INTO loans (
                book_id, borrower_id, loan_date, due_date, return_date, notes
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    open_book_id,
                    first_borrower_id,
                    today - datetime.timedelta(days=5),
                    today + datetime.timedelta(days=9),
                    None,
                    "Beispielausleihe",
                ),
                (
                    returned_book_id,
                    second_borrower_id,
                    today - datetime.timedelta(days=30),
                    today - datetime.timedelta(days=16),
                    today - datetime.timedelta(days=18),
                    "Pünktlich zurückgegeben",
                ),
            ],
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def test_connection() -> bool:
    connection = get_connection(database=None)
    cursor = connection.cursor(buffered=True)
    try:
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True
    finally:
        cursor.close()
        connection.close()


def database_exists() -> bool:
    connection = get_connection(database=None)
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = %s",
            (DB_NAME,),
        )
        result = cursor.fetchone()
        return bool(result and result[0] == 1)
    finally:
        cursor.close()
        connection.close()


def schema_exists() -> bool:
    connection = get_connection(database=None)
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name IN ('books', 'borrowers', 'loans')",
            (DB_NAME,),
        )
        result = cursor.fetchone()
        return bool(result and result[0] >= 3)
    except mysql.connector.Error:
        return False
    finally:
        cursor.close()
        connection.close()


def execute_statement(
    sql: str,
    params: Optional[Iterable[Any]] = None,
    database: Optional[str] = DB_NAME,
) -> int:
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


def execute_many(
    sql: str,
    parameter_rows: Iterable[Iterable[Any]],
    database: Optional[str] = DB_NAME,
) -> int:
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


def query_dataframe(
    sql: str,
    params: Optional[Iterable[Any]] = None,
    database: Optional[str] = DB_NAME,
) -> pd.DataFrame:
    connection = get_connection(database)
    try:
        return pd.read_sql(sql, connection, params=params)
    finally:
        connection.close()
