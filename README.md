# Liane's Library

Kleine Bibliotheksverwaltung für private Buchsammlungen – wer hat sich was
ausgeliehen, was ist noch da, was ist überfällig. Entstanden ist das Projekt
im Rahmen meiner Weiterbildung als Übung, um Python, SQL und ein einfaches
Web-Deployment einmal komplett von der Datenbank bis zur Oberfläche selbst
durchzuziehen.

Die Anwendung ist bewusst schlank gehalten: ein Streamlit-Frontend, eine
MySQL-Datenbank, dazwischen ein kleines DB-Modul. Kein Framework-Overkill,
dafür lässt sich jeder Teil noch gut nachvollziehen.

## Was die App kann

- **Dashboard** – Kennzahlen auf einen Blick (aktive Bücher, aktive Personen,
  offene Ausleihen) plus Schnellübersichten für verfügbare Bücher, offene
  Ausleihen und die letzten Aktivitäten
- **Bücher verwalten** – Bücher anlegen, bearbeiten und (statt hart zu
  löschen) als inaktiv markieren
- **Personen verwalten** – Ausleiher:innen mit Kontaktdaten und Notiz erfassen
  und pflegen
- **Ausleihen** – Bücher gegen Personen ausleihen, Fälligkeitsdatum setzen,
  Rückgaben erfassen
- **Einstellungen** – Verbindungsstatus zur Datenbank prüfen und das Schema
  bei Bedarf neu initialisieren

## Projektstruktur

- `environment.yml`: lokale Conda-Umgebung
- `requirements.txt`: gemeinsame Python-Abhängigkeiten für Conda und Docker
- `docker-compose.yml`: lokale MySQL-Datenbank und optional der komplette Stack
- `Dockerfile`: Production-Laufzeit für Coolify
- `sql/import.sql`: Datenbankschema und Views
- `sql/testdata.sql`: Beispieldaten für lokale Tests
- `web/app.py`: Streamlit-Anwendung
- `python/db.py`: Datenbankverbindung und Abfragen
- `python/create_schema.py`: Hilfsskript, um das Schema manuell neu anzulegen
- `python/*.ipynb`: Notebooks, in denen ich einzelne SQL-Abfragen und
  Pandas-Auswertungen ausprobiert habe, bevor sie in `db.py` gewandert sind

## Datenmodell

Drei Tabellen bilden den Kern ab:

- `books` – Titel, Autor:in, ISBN, Kategorie, Standort, Notizen, `is_active`
- `borrowers` – Name, Kontaktdaten, Beziehung zur Person, `is_active`
- `loans` – verknüpft Buch und Person mit Ausleih-, Fällig- und
  Rückgabedatum

Dazu zwei Views, die in der App direkt abgefragt werden:

- `v_open_loans` – aktuell offene Ausleihen inkl. Buch- und Personendaten
- `v_loan_overview` – vollständige Ausleihhistorie für die Übersicht

Bücher und Personen werden nie gelöscht, sondern über `is_active`
deaktiviert – so bleibt die Ausleihhistorie auch nach einer "Löschung"
nachvollziehbar.

## Lokal mit Conda üben

### 1. Conda-Umgebung erstellen

Öffne Anaconda Prompt, Miniconda Prompt oder ein Terminal mit verfügbarem
`conda` im Projektverzeichnis:

```bash
conda env create --file environment.yml
conda activate lianeslib
```

Die Umgebung verwendet Python 3.12 und installiert die Pakete aus
`requirements.txt`. `ipykernel` ist zusätzlich enthalten, damit die Umgebung
auch in Jupyter und VS Code als Kernel ausgewählt werden kann.

### 2. Nur MySQL mit Docker starten

Die Python-Anwendung läuft in Conda. Docker stellt lokal lediglich die
MySQL-Datenbank bereit:

```bash
docker compose up -d db
```

Die Standardwerte in `python/db.py` passen zur lokalen Datenbank aus
`docker-compose.yml`:

```text
Host: localhost
Port: 3306
Datenbank: lianes_library
Benutzer: library_user
Passwort: library_password
```

### 3. Streamlit aus Conda starten

```bash
streamlit run web/app.py
```

Die Anwendung ist anschließend unter `http://localhost:8501` erreichbar.

### 4. Umgebung später aktualisieren

Nach Änderungen an `environment.yml` oder `requirements.txt`:

```bash
conda env update --file environment.yml --prune
```

### 5. Lokale Dienste beenden

```bash
docker compose stop db
conda deactivate
```

`docker compose stop db` erhält die Daten im Docker-Volume. Mit
`docker compose down` werden die Container entfernt, das benannte Daten-Volume
bleibt jedoch ebenfalls bestehen. `docker compose down --volumes` würde auch
die lokale Datenbank löschen.

## Optional: komplett lokal mit Docker

Die bisherige Variante funktioniert weiterhin unverändert:

```bash
docker compose up --build
```

Dabei laufen Streamlit und MySQL jeweils in einem Container.

## Production mit Coolify

Das Production-Deployment bleibt Docker-basiert. Coolify baut den vorhandenen
`Dockerfile`; Conda und `environment.yml` werden dafür nicht benötigt.

In Coolify müssen folgende Umgebungsvariablen gesetzt sein:

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

Falls zusätzlich `MYSQL_URL` gesetzt wird, muss die URL dieselbe Datenbank wie
`MYSQL_DATABASE` enthalten. Zugangsdaten gehören ausschließlich in Coolify oder
eine lokale, von Git ignorierte `.env`-Datei.

## Conda und Docker in diesem Projekt

| Umgebung | Python/Streamlit | MySQL | Zweck |
|---|---|---|---|
| Lokal mit Conda | Conda | Docker | Lernen, Debugging, Notebooks |
| Lokal komplett mit Docker | Docker | Docker | Production-nahe Tests |
| Coolify | Docker | Coolify/MySQL | Production |

## Was ich dabei gelernt habe / offene Punkte

- Streamlit eignet sich gut, um ein CRUD-Interface schnell aufzubauen, ohne
  sich vorher mit einem separaten Frontend beschäftigen zu müssen
- Views (`v_open_loans`, `v_loan_overview`) statt komplexer Joins direkt in
  Python zu pflegen, hält `db.py` deutlich übersichtlicher
- Soft-Deletes über `is_active` statt echter `DELETE`-Statements, um die
  Historie nicht zu verlieren
- Noch offen: eine echte Nutzerverwaltung/Login gibt es aktuell nicht – für
  den privaten Gebrauch reicht das, für mehrere Haushalte bräuchte es das
  noch
