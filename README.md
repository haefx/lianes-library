# Liane's Library

Eine Bibliotheksverwaltung mit Streamlit und MySQL. Für das Production-Deployment
auf Coolify wird Docker verwendet. Lokal kann die Anwendung zum Lernen in einer
Conda-Umgebung ausgeführt werden.

## Projektstruktur

- `environment.yml`: lokale Conda-Umgebung
- `requirements.txt`: gemeinsame Python-Abhängigkeiten für Conda und Docker
- `docker-compose.yml`: lokale MySQL-Datenbank und optional der komplette Stack
- `Dockerfile`: unveränderte Production-Laufzeit für Coolify
- `sql/import.sql`: Datenbankschema und Views
- `web/app.py`: Streamlit-Anwendung
- `python/db.py`: Datenbankverbindung und Abfragen

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
