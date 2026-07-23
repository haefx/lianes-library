-- =========================================================
-- LIANE'S LIBRARY
-- Beispieldaten für lokale Tests
-- =========================================================

USE lianes_library;


-- ---------------------------------------------------------
-- BÜCHER
-- ---------------------------------------------------------

INSERT INTO books (title, author, isbn, category, shelf_location, notes)
VALUES
    ('Die Vermessung der Welt', 'Daniel Kehlmann', '978-3-498-03528-3', 'Roman', 'Regal 1, Fach A', 'Von Tante Erika geschenkt bekommen'),
    ('Der Vorleser', 'Bernhard Schlink', '978-3-257-22953-1', 'Roman', 'Regal 1, Fach A', NULL),
    ('Sofies Welt', 'Jostein Gaarder', '978-3-423-12455-6', 'Sachbuch', 'Regal 2, Fach B', 'Philosophiegeschichte für Einsteiger'),
    ('Der Schwarm', 'Frank Schätzing', '978-3-462-03462-3', 'Thriller', 'Regal 2, Fach C', NULL),
    ('Tschick', 'Wolfgang Herrndorf', '978-3-499-25784-3', 'Jugendbuch', 'Regal 3, Fach A', 'Klassenlektüre der 9. Klasse');


-- ---------------------------------------------------------
-- PERSONEN
-- ---------------------------------------------------------

INSERT INTO borrowers (name, email, phone, relationship, notes)
VALUES
    ('Anna Bergmann', 'anna.bergmann@example.com', '0170 1234567', 'Freundin', NULL),
    ('Markus Weber', 'markus.weber@example.com', '0151 2345678', 'Kollege', 'Arbeitet im selben Büro'),
    ('Sabine Hoffmann', 'sabine.hoffmann@example.com', '0160 3456789', 'Familie', 'Cousine'),
    ('Thomas Krüger', NULL, '0176 4567890', 'Nachbar', NULL),
    ('Julia Lehmann', 'julia.lehmann@example.com', NULL, 'Freundin', 'Aus dem Lesekreis');


-- ---------------------------------------------------------
-- AUSLEIHEN
-- ---------------------------------------------------------

INSERT INTO loans (book_id, borrower_id, loan_date, due_date, return_date, notes)
VALUES
    (1, 1, '2026-06-01', '2026-06-22', '2026-06-20', NULL),
    (2, 2, '2026-06-15', '2026-07-06', NULL, 'Wollte es fürs Wochenende'),
    (4, 3, '2026-07-01', '2026-07-15', NULL, NULL),
    (5, 4, '2026-05-10', '2026-05-24', '2026-05-23', 'Für die Nichte ausgeliehen'),
    (3, 5, '2026-07-10', '2026-07-24', NULL, 'Erste Ausleihe an Julia');
