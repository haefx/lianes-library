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
    seed_sample_data_if_empty,
    test_connection,
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --navy: #0f172a;
            --slate: #475569;
            --muted: #64748b;
            --line: #e2e8f0;
            --surface: #f8fafc;
            --canvas: #e9eef6;
            --primary: #4f46e5;
            --primary-dark: #4338ca;
        }

        html, body, .stApp {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 86% 4%, rgba(99, 102, 241, 0.12), transparent 28rem),
                var(--canvas) !important;
            color: var(--navy) !important;
        }

        [data-testid="stHeader"] {
            background: rgba(233, 238, 246, 0.84) !important;
            backdrop-filter: blur(16px);
        }

        [data-testid="stMain"] {
            background: transparent !important;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1280px;
            padding: 3.5rem 2.25rem 4rem !important;
        }

        [data-testid="stMain"] h1,
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3,
        [data-testid="stMain"] h4 {
            color: var(--navy) !important;
            letter-spacing: -0.025em;
        }

        [data-testid="stMain"] p,
        [data-testid="stMain"] span,
        [data-testid="stMain"] label,
        [data-testid="stMain"] li,
        [data-testid="stWidgetLabel"] {
            color: var(--slate) !important;
        }

        .dashboard-hero {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.75rem;
        }

        .dashboard-logo {
            display: grid;
            place-items: center;
            width: 3.25rem;
            height: 3.25rem;
            flex: 0 0 3.25rem;
            border-radius: 1rem;
            color: #fff;
            font-size: 1.45rem;
            background: linear-gradient(135deg, #6366f1, #4338ca);
            box-shadow: 0 14px 30px rgba(79, 70, 229, 0.24);
        }

        .dashboard-hero h1 {
            margin: 0 !important;
            font-size: clamp(1.8rem, 3vw, 2.45rem) !important;
            font-weight: 760 !important;
        }

        .dashboard-hero p {
            margin: 0.25rem 0 0 !important;
            color: var(--muted) !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #111827 0%, #0f172a 100%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
        }

        [data-testid="stSidebarContent"] {
            padding: 2rem 1.25rem !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {
            color: #e5e7eb !important;
        }

        .sidebar-brand {
            padding: 0.25rem 0 1.35rem;
            margin-bottom: 1.25rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.09);
        }

        .sidebar-brand strong {
            display: block;
            color: #fff;
            font-size: 1.05rem;
        }

        .sidebar-brand small,
        .db-status small {
            color: #94a3b8;
        }

        .db-status {
            padding: 1rem;
            margin: 0.5rem 0 1rem;
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 0.9rem;
            background: rgba(255, 255, 255, 0.05);
        }

        .db-status strong {
            display: block;
            margin-bottom: 0.25rem;
            color: #f8fafc;
        }

        [data-testid="stTabs"] {
            padding: 0.4rem;
            border: 1px solid var(--line);
            border-radius: 1rem;
            background: rgba(248, 250, 252, 0.94);
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        }

        [data-baseweb="tab-list"] {
            gap: 0.3rem;
            padding: 0.1rem;
        }

        button[role="tab"] {
            min-height: 2.65rem !important;
            padding: 0.65rem 1rem !important;
            border-radius: 0.7rem !important;
            background: transparent !important;
            border: 0 !important;
        }

        button[role="tab"] * {
            color: var(--slate) !important;
            font-weight: 600 !important;
        }

        button[role="tab"]:hover {
            background: #eef2ff !important;
        }

        button[role="tab"][aria-selected="true"] {
            background: var(--navy) !important;
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.14);
        }

        button[role="tab"][aria-selected="true"] * {
            color: #ffffff !important;
        }

        [data-testid="stMetric"] {
            position: relative;
            min-height: 8.5rem;
            padding: 1.35rem 1.4rem !important;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 1rem;
            background: var(--surface);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.055);
        }

        [data-testid="stMetric"]::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: linear-gradient(#6366f1, #818cf8);
        }

        [data-testid="stMetricLabel"] *,
        [data-testid="stMetricLabel"] {
            color: var(--muted) !important;
            font-weight: 600 !important;
        }

        [data-testid="stMetricValue"] *,
        [data-testid="stMetricValue"] {
            color: var(--navy) !important;
            font-weight: 740 !important;
        }

        [data-testid="stExpander"],
        [data-testid="stForm"],
        .stDataFrame {
            border: 1px solid var(--line) !important;
            border-radius: 1rem !important;
            background: var(--surface) !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 0.85rem !important;
            border-width: 1px !important;
        }

        [data-testid="stAlert"] * {
            color: inherit !important;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"] > div,
        [data-testid="stDateInput"] input {
            min-height: 2.8rem;
            color: var(--navy) !important;
            background: #f8fafc !important;
            border-color: #cbd5e1 !important;
            border-radius: 0.7rem !important;
        }

        .stButton > button,
        [data-testid="stFormSubmitButton"] > button {
            min-height: 2.75rem;
            padding: 0.65rem 1.15rem !important;
            color: #ffffff !important;
            border: 0 !important;
            border-radius: 0.75rem !important;
            background: linear-gradient(135deg, #6366f1, var(--primary-dark)) !important;
            box-shadow: 0 8px 18px rgba(79, 70, 229, 0.22);
            transition: transform 150ms ease, box-shadow 150ms ease !important;
        }

        .stButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 11px 24px rgba(79, 70, 229, 0.28);
        }

        .stButton > button *,
        [data-testid="stFormSubmitButton"] > button * {
            color: #ffffff !important;
            font-weight: 650 !important;
        }

        [data-testid="stDataFrame"] {
            overflow: hidden;
            border-radius: 0.9rem;
        }

        hr {
            border-color: var(--line) !important;
        }

        ::selection {
            color: var(--navy);
            background: #c7d2fe;
        }

        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"] {
                padding: 2rem 1rem 3rem !important;
            }

            .dashboard-hero {
                align-items: flex-start;
            }
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
        tabs = st.tabs(["Verfügbare Bücher", "Offene Ausleihen", "Letzte Aktivitäten"])

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
                    st.rerun()

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
                st.rerun()

            if delete:
                execute_statement(
                    "UPDATE books SET is_active = FALSE WHERE book_id = %s",
                    params=(selection,),
                )
                st.success("Buch wurde inaktiv gesetzt.")
                st.rerun()


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
                    st.rerun()

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
                st.rerun()

            if deactivate:
                execute_statement(
                    "UPDATE borrowers SET is_active = FALSE WHERE borrower_id = %s",
                    params=(selection,),
                )
                st.success("Person wurde inaktiv gesetzt.")
                st.rerun()


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
                    st.rerun()

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
                st.rerun()


def database_help():
    st.header("Datenbank")
    st.markdown(
        """
        **Verbindung**

        Diese App verwendet die Umgebungsvariablen:

        - `MYSQL_HOST`
        - `MYSQL_PORT`
        - `MYSQL_USER`
        - `MYSQL_PASSWORD`
        - `MYSQL_DATABASE`

        Ohne gesetzte Umgebungsvariablen greift die App auf `localhost:3306`,
        Benutzer `library_user` und Datenbank `lianes_library` zurück.
        """
    )

    st.subheader("Lokale Einrichtung")
    st.markdown(
        """
        - `sql/import.sql` in MySQL Workbench (oder einem anderen SQL-Client)
          gegen deine lokale MySQL-Instanz ausführen.
        - Optional `sql/testdata.sql` für Beispieldaten ausführen.
        - `http://localhost:8501` öffnet die App, sobald `streamlit run web/app.py`
          in der aktivierten Conda-Umgebung läuft.
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

    st.markdown(
        """
        <div class="dashboard-hero">
            <div class="dashboard-logo">◫</div>
            <div>
                <h1>Liane's Library</h1>
                <p>Bibliothek, Personen und Ausleihen zentral verwalten</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <strong>Liane's Library</strong>
            <small>Administration Dashboard</small>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.subheader("Datenbank")
    st.sidebar.markdown(
        f"""
        <div class="db-status">
            <strong>{SAFE_CONFIG['database']}</strong>
            <small>{SAFE_CONFIG['host']}:{SAFE_CONFIG['port']} · {SAFE_CONFIG['user']}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Verbindung testen", use_container_width=True):
        try:
            if test_connection():
                st.sidebar.success("Datenbankverbindung erfolgreich")
        except Exception as err:
            message = str(err)
            st.sidebar.error(f"Verbindung fehlgeschlagen: {message}")
            if "1045" in message or "Access denied" in message:
                st.sidebar.error(
                    "Authentifizierungsfehler: Prüfe MYSQL_USER, MYSQL_PASSWORD und Benutzerrechte."
                )

    try:
        test_connection()
        connected = True
    except Exception as err:
        connected = False
        message = str(err)
        st.error(
            "Datenbank nicht erreichbar. Prüfe, ob MySQL läuft und die Umgebungsvariablen korrekt gesetzt sind."
        )
        st.error(message)
        if "1044" in message or "1045" in message or "Access denied" in message:
            st.error(
                "Der angegebene MySQL-Benutzer hat keine ausreichenden Rechte. "
                "Verwende einen Benutzer mit Zugriff auf die Datenbank oder korrigiere die Rechte."
            )

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
            database_help()
            return

        try:
            if seed_sample_data_if_empty():
                st.toast("Beispieldaten wurden angelegt.", icon="✅")
        except Exception as err:
            st.warning(f"Beispieldaten konnten nicht angelegt werden: {err}")

        tabs = st.tabs(["Übersicht", "Bücher", "Personen", "Ausleihen", "Einstellungen"])

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
