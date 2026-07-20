import datetime
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from python.db import (
    DB_CONFIG,
    SAFE_CONFIG,
    execute_statement,
    initialize_schema,
    query_dataframe,
    schema_exists,
    test_connection,
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #f4f7fb;
            color: #0f172a;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
        }
        .css-1d391kg {
            padding: 1rem 1.2rem 0.8rem;
        }
        .metric-label {
            color: #475569;
        }
        .card {
            background: #ffffff;
            border-radius: 16px;
            padding: 1.1rem;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
            margin-bottom: 1.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_query(sql: str, params=None):
    try:
        return query_dataframe(sql, params=params)
    except Exception as error:
        st.error(f"Datenbankfehler: {error}")
        return pd.DataFrame()


def load_counts():
    books = safe_query("SELECT COUNT(*) AS anzahl_buecher FROM books WHERE is_active = TRUE")
    borrowers = safe_query("SELECT COUNT(*) AS anzahl_personen FROM borrowers WHERE is_active = TRUE")
    open_loans = safe_query("SELECT COUNT(*) AS offene_ausleihen FROM loans WHERE return_date IS NULL")

    return (
        int(books.iloc[0]["anzahl_buecher"]) if not books.empty else 0,
        int(borrowers.iloc[0]["anzahl_personen"]) if not borrowers.empty else 0,
        int(open_loans.iloc[0]["offene_ausleihen"]) if not open_loans.empty else 0,
    )


def load_books(active_only: bool = True) -> pd.DataFrame:
    query = "SELECT * FROM books"
    if active_only:
        query += " WHERE is_active = TRUE"
    query += " ORDER BY title"
    return safe_query(query)


def load_borrowers(active_only: bool = True) -> pd.DataFrame:
    query = "SELECT * FROM borrowers"
    if active_only:
        query += " WHERE is_active = TRUE"
    query += " ORDER BY name"
    return safe_query(query)


def load_open_loans() -> pd.DataFrame:
    return safe_query(
        "SELECT * FROM v_open_loans ORDER BY due_date, loan_date"
    )


def load_loan_history(limit: int = 50) -> pd.DataFrame:
    return safe_query(
        "SELECT * FROM v_loan_overview ORDER BY loan_date DESC LIMIT %s",
        params=(limit,),
    )


def load_available_books() -> pd.DataFrame:
    return safe_query(
        """
        SELECT b.book_id, b.title, b.author, b.isbn, b.category, b.shelf_location
        FROM books AS b
        LEFT JOIN loans AS l
            ON b.book_id = l.book_id
           AND l.return_date IS NULL
        WHERE b.is_active = TRUE
          AND l.loan_id IS NULL
        ORDER BY b.title
        """
    )


def show_overview():
    st.header("Dashboard")

    count_books, count_borrowers, count_open_loans = load_counts()

    col1, col2, col3 = st.columns(3)
    col1.metric("Aktive Bücher", count_books)
    col2.metric("Aktive Personen", count_borrowers)
    col3.metric("Offene Ausleihen", count_open_loans)

    with st.container():
        st.subheader("Schnelle Übersichten")
        tabs = st.tabs(["Verfügbare Bücher", "Offene Ausleihen", "Letzte Historie"])

        with tabs[0]:
            available = load_available_books()
            if available.empty:
                st.info("Keine verfügbaren Bücher gefunden.")
            else:
                st.dataframe(available)

        with tabs[1]:
            open_loans = load_open_loans()
            if open_loans.empty:
                st.info("Keine offenen Ausleihen.")
            else:
                st.dataframe(open_loans)

        with tabs[2]:
            history = load_loan_history(20)
            if history.empty:
                st.info("Keine historischen Ausleihen vorhanden.")
            else:
                st.dataframe(history)


def book_management():
    st.header("Bücher verwalten")

    with st.expander("Neues Buch erfassen"):
        with st.form("new_book_form"):
            title = st.text_input("Titel", max_chars=255)
            author = st.text_input("Autor / Autorin", max_chars=255)
            isbn = st.text_input("ISBN")
            category = st.text_input("Kategorie")
            shelf_location = st.text_input("Regal / Standort")
            notes = st.text_area("Notizen", height=120)
            active = st.checkbox("Buch aktiv verwenden", value=True)
            submitted = st.form_submit_button("Buch hinzufügen")

            if submitted:
                if not title or not author:
                    st.warning("Titel und Autor/in sind erforderlich.")
                else:
                    execute_statement(
                        """
                        INSERT INTO books (
                            title,
                            author,
                            isbn,
                            category,
                            shelf_location,
                            notes,
                            is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        params=(
                            title,
                            author,
                            isbn if isbn else None,
                            category if category else None,
                            shelf_location if shelf_location else None,
                            notes if notes else None,
                            1 if active else 0,
                        ),
                    )
                    st.success("Buch wurde hinzugefügt.")
                    st.experimental_rerun()

    books = load_books(active_only=False)
    if books.empty:
        st.info("Es sind noch keine Bücher in der Datenbank vorhanden.")
        return

    st.subheader("Bücherliste")
    st.dataframe(books)

    with st.expander("Buchdaten bearbeiten"):
        selection = st.selectbox(
            "Buch auswählen",
            options=books["book_id"],
            format_func=lambda book_id: f"{books.loc[books['book_id'] == book_id, 'title'].iloc[0]}"
        )
        record = books[books["book_id"] == selection].iloc[0]

        with st.form("edit_book_form"):
            title = st.text_input("Titel", value=record["title"])
            author = st.text_input("Autor / Autorin", value=record["author"])
            isbn = st.text_input("ISBN", value=record["isbn"] or "")
            category = st.text_input("Kategorie", value=record["category"] or "")
            shelf_location = st.text_input("Regal / Standort", value=record["shelf_location"] or "")
            notes = st.text_area("Notizen", value=record["notes"] or "", height=120)
            active = st.checkbox("Buch aktiv verwenden", value=bool(record["is_active"]))
            update = st.form_submit_button("Änderungen speichern")
            delete = st.form_submit_button("Als inaktiv markieren")

            if update:
                execute_statement(
                    """
                    UPDATE books
                    SET title = %s,
                        author = %s,
                        isbn = %s,
                        category = %s,
                        shelf_location = %s,
                        notes = %s,
                        is_active = %s
                    WHERE book_id = %s
                    """,
                    params=(
                        title,
                        author,
                        isbn if isbn else None,
                        category if category else None,
                        shelf_location if shelf_location else None,
                        notes if notes else None,
                        1 if active else 0,
                        selection,
                    ),
                )
                st.success("Buchdaten wurden aktualisiert.")
                st.experimental_rerun()

            if delete:
                execute_statement(
                    "UPDATE books SET is_active = FALSE WHERE book_id = %s",
                    params=(selection,),
                )
                st.success("Buch wurde inaktiv gesetzt.")
                st.experimental_rerun()


def borrower_management():
    st.header("Personen verwalten")

    with st.expander("Neue Person erfassen"):
        with st.form("new_borrower_form"):
            name = st.text_input("Name", max_chars=150)
            email = st.text_input("E-Mail")
            phone = st.text_input("Telefon")
            relationship = st.text_input("Beziehung", help="z. B. Freund, Kollege, Familie")
            notes = st.text_area("Notizen", height=120)
            active = st.checkbox("Person aktiv verwenden", value=True)
            submitted = st.form_submit_button("Person hinzufügen")

            if submitted:
                if not name:
                    st.warning("Name ist erforderlich.")
                else:
                    execute_statement(
                        """
                        INSERT INTO borrowers (
                            name,
                            email,
                            phone,
                            relationship,
                            notes,
                            is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        params=(
                            name,
                            email if email else None,
                            phone if phone else None,
                            relationship if relationship else None,
                            notes if notes else None,
                            1 if active else 0,
                        ),
                    )
                    st.success("Person wurde hinzugefügt.")
                    st.experimental_rerun()

    borrowers = load_borrowers(active_only=False)
    if borrowers.empty:
        st.info("Es sind noch keine Personen in der Datenbank vorhanden.")
        return

    st.subheader("Personenliste")
    st.dataframe(borrowers)

    with st.expander("Person bearbeiten"):
        selection = st.selectbox(
            "Person auswählen",
            options=borrowers["borrower_id"],
            format_func=lambda borrower_id: f"{borrowers.loc[borrowers['borrower_id'] == borrower_id, 'name'].iloc[0]}"
        )
        record = borrowers[borrowers["borrower_id"] == selection].iloc[0]

        with st.form("edit_borrower_form"):
            name = st.text_input("Name", value=record["name"])
            email = st.text_input("E-Mail", value=record["email"] or "")
            phone = st.text_input("Telefon", value=record["phone"] or "")
            relationship = st.text_input("Beziehung", value=record["relationship"] or "")
            notes = st.text_area("Notizen", value=record["notes"] or "", height=120)
            active = st.checkbox("Person aktiv verwenden", value=bool(record["is_active"]))
            update = st.form_submit_button("Änderungen speichern")
            deactivate = st.form_submit_button("Als inaktiv markieren")

            if update:
                execute_statement(
                    """
                    UPDATE borrowers
                    SET name = %s,
                        email = %s,
                        phone = %s,
                        relationship = %s,
                        notes = %s,
                        is_active = %s
                    WHERE borrower_id = %s
                    """,
                    params=(
                        name,
                        email if email else None,
                        phone if phone else None,
                        relationship if relationship else None,
                        notes if notes else None,
                        1 if active else 0,
                        selection,
                    ),
                )
                st.success("Personendaten wurden aktualisiert.")
                st.experimental_rerun()

            if deactivate:
                execute_statement(
                    "UPDATE borrowers SET is_active = FALSE WHERE borrower_id = %s",
                    params=(selection,),
                )
                st.success("Person wurde inaktiv gesetzt.")
                st.experimental_rerun()


def loan_management():
    st.header("Ausleihen")

    available_books = load_available_books()
    active_borrowers = load_borrowers(active_only=True)

    with st.expander("Neue Ausleihe anlegen"):
        with st.form("loan_form"):
            if available_books.empty:
                st.warning("Es gibt aktuell keine verfügbaren Bücher für eine neue Ausleihe.")
            if active_borrowers.empty:
                st.warning("Es gibt aktuell keine aktiven Personen für eine neue Ausleihe.")

            book_id = st.selectbox(
                "Buch wählen",
                options=available_books["book_id"] if not available_books.empty else [],
                format_func=lambda book_id: f"{available_books.loc[available_books['book_id'] == book_id, 'title'].iloc[0]}"
                if not available_books.empty
                else "",
            ) if not available_books.empty else None

            borrower_id = st.selectbox(
                "Person wählen",
                options=active_borrowers["borrower_id"] if not active_borrowers.empty else [],
                format_func=lambda borrower_id: f"{active_borrowers.loc[active_borrowers['borrower_id'] == borrower_id, 'name'].iloc[0]}"
                if not active_borrowers.empty
                else "",
            ) if not active_borrowers.empty else None

            due_date = st.date_input("Fälligkeitsdatum", value=datetime.date.today() + datetime.timedelta(days=14))
            notes = st.text_area("Notizen zur Ausleihe", height=100)
            submitted = st.form_submit_button("Ausleihe speichern")

            if submitted:
                if book_id is None or borrower_id is None:
                    st.warning("Bitte ein Buch und eine Person auswählen.")
                else:
                    execute_statement(
                        """
                        INSERT INTO loans (
                            book_id,
                            borrower_id,
                            loan_date,
                            due_date,
                            notes
                        ) VALUES (%s, %s, %s, %s, %s)
                        """,
                        params=(
                            book_id,
                            borrower_id,
                            datetime.date.today(),
                            due_date,
                            notes if notes else None,
                        ),
                    )
                    st.success("Ausleihe wurde angelegt.")
                    st.experimental_rerun()

    with st.expander("Offene Ausleihen verwalten"):
        open_loans = load_open_loans()
        if open_loans.empty:
            st.info("Keine offenen Ausleihen vorhanden.")
        else:
            st.dataframe(open_loans)
            loan_choice = st.selectbox(
                "Ausleihe zurückgeben",
                options=open_loans["loan_id"],
                format_func=lambda loan_id: (
                    f"{open_loans.loc[open_loans['loan_id'] == loan_id, 'title'].iloc[0]}" +
                    f" → {open_loans.loc[open_loans['loan_id'] == loan_id, 'borrower_name'].iloc[0]}"
                ),
            )
            if st.button("Als zurückgegeben markieren"):
                execute_statement(
                    "UPDATE loans SET return_date = CURRENT_DATE WHERE loan_id = %s AND return_date IS NULL",
                    params=(loan_choice,),
                )
                st.success("Ausleihe wurde als zurückgegeben markiert.")
                st.experimental_rerun()


def database_help():
    st.header("Datenbank & Deployment")
    st.markdown(
        """
        **Verbindung**

        Diese App verwendet die Umgebungsvariablen:

        - `MYSQL_HOST`
        - `MYSQL_PORT`
        - `MYSQL_USER`
        - `MYSQL_PASSWORD`
        - `MYSQL_DATABASE`

        Für Coolify kannst du diese Werte in den Umgebungsvariablen der App setzen.
        """
    )

    st.subheader("Lokale Entwicklung")
    st.markdown(
        """
        - Starte `docker-compose up --build` im Projektverzeichnis.
        - Die Datenbank wird automatisch mit `sql/import.sql` initialisiert.
        - `http://localhost:8501` öffnet die App.
        """
    )

    st.subheader("Schema neu erstellen")
    st.markdown(
        """
        Wenn du die Datenbank manuell neu einrichten möchtest, benutze das Hilfs-Skript:

        ```bash
        python python/create_schema.py --seed
        ```
        """
    )


def main():
    st.set_page_config(
        page_title="Liane's Library",
        page_icon="📚",
        layout="wide",
    )

    inject_styles()

    st.title("Liane's Library")
    st.caption("Moderne Bibliotheksverwaltung für Bücher, Personen und Ausleihen.")

    st.sidebar.header("Datenbank")
    st.sidebar.write(SAFE_CONFIG)
    if st.sidebar.button("Verbindung testen"):
        try:
            if test_connection():
                st.sidebar.success("Datenbankverbindung erfolgreich")
        except Exception as err:
            st.sidebar.error(f"Verbindung fehlgeschlagen: {err}")

    try:
        test_connection()
        connected = True
    except Exception as err:
        connected = False
        st.error(
            "Datenbank nicht erreichbar. Prüfe, ob MySQL läuft und die Umgebungsvariablen korrekt gesetzt sind."
        )
        st.error(err)

    if connected:
        missing_schema = not schema_exists()
        if missing_schema:
            st.warning("Das Datenbankschema ist noch nicht angelegt. Bitte initialisiere es, bevor du weiterarbeitest.")
            if st.button("Schema initialisieren"):
                try:
                    initialize_schema()
                    st.success("Datenbank-Schema wurde erstellt. Bitte Seite neu laden.")
                except Exception as err:
                    st.error(f"Schema-Initialisierung fehlgeschlagen: {err}")

        tabs = st.tabs(["Übersicht", "Bücher", "Personen", "Ausleihen", "Datenbank"])

        with tabs[0]:
            show_overview()
        with tabs[1]:
            book_management()
        with tabs[2]:
            borrower_management()
        with tabs[3]:
            loan_management()
        with tabs[4]:
            database_help()
    else:
        st.error(
            "Datenbank nicht erreichbar. Prüfe, ob MySQL läuft und die Umgebungsvariablen korrekt gesetzt sind."
        )
        database_help()


if __name__ == "__main__":
    main()
