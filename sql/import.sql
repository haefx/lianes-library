-- =========================================================
-- LIANE'S LIBRARY
-- Datenbankschema für MySQL 8.0
-- =========================================================


-- ---------------------------------------------------------
-- 1. DATENBANK ERSTELLEN
-- ---------------------------------------------------------

CREATE DATABASE IF NOT EXISTS lianes_library
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE lianes_library;


-- ---------------------------------------------------------
-- 2. TABELLE: BOOKS
-- Enthält alle Bücher aus Lianes Sammlung
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS books
(
    book_id INT UNSIGNED NOT NULL AUTO_INCREMENT,

    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,

    isbn VARCHAR(20) NULL,
    category VARCHAR(100) NULL,
    shelf_location VARCHAR(100) NULL,
    notes TEXT NULL,

    -- Soft Delete:
    -- 1 = Buch ist aktiv
    -- 0 = Buch wurde deaktiviert
    is_active TINYINT(1) NOT NULL DEFAULT 1,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_books
        PRIMARY KEY (book_id),

    CONSTRAINT uq_books_isbn
        UNIQUE (isbn),

    CONSTRAINT chk_books_title
        CHECK (CHAR_LENGTH(TRIM(title)) > 0),

    CONSTRAINT chk_books_author
        CHECK (CHAR_LENGTH(TRIM(author)) > 0),

    CONSTRAINT chk_books_is_active
        CHECK (is_active IN (0, 1)),

    INDEX idx_books_title (title),
    INDEX idx_books_author (author),
    INDEX idx_books_category (category),
    INDEX idx_books_is_active (is_active)
)
ENGINE = InnoDB;


-- ---------------------------------------------------------
-- 3. TABELLE: BORROWERS
-- Enthält alle Personen, die Bücher ausleihen
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS borrowers
(
    borrower_id INT UNSIGNED NOT NULL AUTO_INCREMENT,

    name VARCHAR(150) NOT NULL,

    email VARCHAR(254) NULL,
    phone VARCHAR(30) NULL,

    -- Beispiele:
    -- Friend, Colleague, Family, Acquaintance
    relationship VARCHAR(50) NULL,

    notes TEXT NULL,

    -- Soft Delete:
    -- 1 = Person ist aktiv
    -- 0 = Person wurde deaktiviert
    is_active TINYINT(1) NOT NULL DEFAULT 1,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_borrowers
        PRIMARY KEY (borrower_id),

    CONSTRAINT uq_borrowers_email
        UNIQUE (email),

    CONSTRAINT chk_borrowers_name
        CHECK (CHAR_LENGTH(TRIM(name)) > 0),

    CONSTRAINT chk_borrowers_is_active
        CHECK (is_active IN (0, 1)),

    INDEX idx_borrowers_name (name),
    INDEX idx_borrowers_is_active (is_active)
)
ENGINE = InnoDB;


-- ---------------------------------------------------------
-- 4. TABELLE: LOANS
-- Verknüpft Bücher und Personen miteinander
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS loans
(
    loan_id INT UNSIGNED NOT NULL AUTO_INCREMENT,

    book_id INT UNSIGNED NOT NULL,
    borrower_id INT UNSIGNED NOT NULL,

    loan_date DATE NOT NULL DEFAULT (CURRENT_DATE),

    -- Darf NULL sein, falls kein festes Rückgabedatum vereinbart wurde
    due_date DATE NULL,

    -- NULL bedeutet: Das Buch wurde noch nicht zurückgegeben
    return_date DATE NULL,

    notes TEXT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    /*
        Technische Hilfsspalte:

        Solange return_date NULL ist, enthält die Spalte die book_id.
        Nach der Rückgabe wird sie automatisch NULL.

        Durch den UNIQUE-Index kann dasselbe Buch nicht gleichzeitig
        in zwei offenen Ausleihen vorkommen.
    */
    open_loan_book_id INT UNSIGNED
        GENERATED ALWAYS AS
        (
            CASE
                WHEN return_date IS NULL THEN book_id
                ELSE NULL
            END
        ) STORED,

    CONSTRAINT pk_loans
        PRIMARY KEY (loan_id),

    -- ON UPDATE CASCADE ist hier nicht möglich: book_id ist Basis der
    -- berechneten Spalte open_loan_book_id, und MySQL erlaubt für
    -- Fremdschlüssel auf solchen Basisspalten nur RESTRICT/NO ACTION.
    CONSTRAINT fk_loans_book
        FOREIGN KEY (book_id)
        REFERENCES books (book_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_loans_borrower
        FOREIGN KEY (borrower_id)
        REFERENCES borrowers (borrower_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_loans_due_date
        CHECK (
            due_date IS NULL
            OR due_date >= loan_date
        ),

    CONSTRAINT chk_loans_return_date
        CHECK (
            return_date IS NULL
            OR return_date >= loan_date
        ),

    CONSTRAINT uq_loans_one_open_loan_per_book
        UNIQUE (open_loan_book_id),

    INDEX idx_loans_book_id (book_id),
    INDEX idx_loans_borrower_id (borrower_id),
    INDEX idx_loans_loan_date (loan_date),
    INDEX idx_loans_due_date (due_date),
    INDEX idx_loans_return_date (return_date)
)
ENGINE = InnoDB;


-- ---------------------------------------------------------
-- 5. VIEW: KOMPLETTE AUSLEIHÜBERSICHT
-- Vereinfacht die spätere Anzeige in Streamlit
-- ---------------------------------------------------------

CREATE OR REPLACE VIEW v_loan_overview AS

SELECT
    l.loan_id,

    b.book_id,
    b.title,
    b.author,
    b.isbn,
    b.category,
    b.shelf_location,

    br.borrower_id,
    br.name AS borrower_name,
    br.email AS borrower_email,
    br.phone AS borrower_phone,
    br.relationship,

    l.loan_date,
    l.due_date,
    l.return_date,
    l.notes AS loan_notes,

    CASE
        WHEN l.return_date IS NOT NULL
            THEN 'Returned'

        WHEN l.due_date IS NOT NULL
             AND l.due_date < CURRENT_DATE
            THEN 'Overdue'

        ELSE 'Loaned'
    END AS loan_status

FROM loans AS l

INNER JOIN books AS b
    ON l.book_id = b.book_id

INNER JOIN borrowers AS br
    ON l.borrower_id = br.borrower_id;


-- ---------------------------------------------------------
-- 6. VIEW: NUR AKTUELL AUSGELIEHENE BÜCHER
-- ---------------------------------------------------------

CREATE OR REPLACE VIEW v_open_loans AS

SELECT
    loan_id,
    book_id,
    title,
    author,
    borrower_id,
    borrower_name,
    borrower_email,
    borrower_phone,
    loan_date,
    due_date,
    loan_status

FROM v_loan_overview

WHERE return_date IS NULL;