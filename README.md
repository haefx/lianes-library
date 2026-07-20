# Liane's Library

Dieses Projekt enthält eine einfache Bibliotheksdatenbank mit MySQL und eine Streamlit-Oberfläche für lokale Entwicklung und Hosting.

## Was enthalten ist

- `docker-compose.yml` für lokale Entwicklung mit MySQL und Streamlit
- `Dockerfile` für Deployment (z. B. Coolify)
- `sql/import.sql` für Schema und Views
- `sql/testdata.sql` für Beispielinhalte
- `web/app.py` als Streamlit-App
- `python/db.py` für DB-Verbindung und Abfragen
- `python/create_schema.py` für manuelle DB-Erstellung ohne Docker

## Lokale Entwicklung mit Docker

1. Starte Docker Desktop.
2. Öffne das Projektverzeichnis.
3. Starte den Stack:

```bash
docker-compose up --build
```

4. Öffne `http://localhost:8501`.

## Deployment mit Coolify

1. Push das Repo zu GitHub.
2. Verbinde dein GitHub-Repository mit Coolify.
3. Nutze den enthaltenen `Dockerfile` als Build-Container.
4. Setze in Coolify die Umgebungsvariablen:
   - `MYSQL_HOST`
   - `MYSQL_PORT`
   - `MYSQL_USER`
   - `MYSQL_PASSWORD`
   - `MYSQL_DATABASE`

Wenn Coolify eine eigene MySQL-Instanz anbietet, trage die dortigen Verbindungsdaten ein.

## Manuelle Datenbank-Erstellung (ohne Docker)

1. Installiere MySQL lokal.
2. Erstelle einen Benutzer und eine Datenbank.
3. Setze Umgebungsvariablen oder passe `python/create_schema.py` an.
4. Führe aus:

```bash
python python/create_schema.py --seed
```

## Hinweise

- Nutze `EXECUTE_DATABASE_COMMANDS = False` nur im Notebook, wenn du nicht willst, dass SQL ausgeführt wird.
- Für Produktion solltest du sensible Passwörter als Umgebungsvariablen speichern.
