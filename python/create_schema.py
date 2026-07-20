import argparse
import os

from db import execute_statement, get_connection

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "..", "sql", "import.sql")


def load_sql_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_statements(sql_text):
    statements = []
    current = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current))
            current = []
    if current:
        statements.append("\n".join(current))
    return statements


def main(seed=False):
    sql_text = load_sql_file(SCHEMA_FILE)
    statements = split_statements(sql_text)

    print(f"Lade {len(statements)} SQL-Anweisungen aus {SCHEMA_FILE}")

    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        print("Ausführen:", stmt.splitlines()[0])
        execute_statement(stmt, database=None)

    if seed:
        from pathlib import Path
        seed_file = Path(__file__).resolve().parents[1] / "sql" / "testdata.sql"
        seed_sql = load_sql_file(seed_file)
        for stmt in split_statements(seed_sql):
            execute_statement(stmt)

    print("Schema erstellt.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Erstellt das Datenbankschema und optional Testdaten.")
    parser.add_argument("--seed", action="store_true", help="Testdaten nach dem Schema einfügen")
    args = parser.parse_args()
    main(seed=args.seed)
