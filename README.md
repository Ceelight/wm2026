# WM 2026 Tippspiel

Eine selbst gehostete Tippspiel-Webapp für die Fußball-Weltmeisterschaft 2026. Spielpaarungen und Ergebnisse werden automatisch über die [football-data.org](https://www.football-data.org/) API synchronisiert.

## Features

- Tipp-Abgabe bis zum Anpfiff jedes Spiels
- Automatische Punkteberechnung nach Spielende
- Rangliste mit geteilten Rängen bei Gleichstand
- Gruppenphase-Vorschau (eigene Tipp-Tabelle)
- Admin-UI: Spielverwaltung, Benutzerverwaltung, API-Token-Konfiguration
- Mehrsprachig: Deutsch, Englisch, Spanisch

## Punkteregeln

| Szenario | Punkte |
|---|---|
| Exaktes Ergebnis | 3 |
| Unentschieden getippt, Ergebnis Unentschieden (nicht exakt) | 2 |
| Richtiger Sieger, gleiche Tordifferenz | 2 |
| Richtiger Sieger | 1 |
| Falscher Sieger | 0 |

## Voraussetzungen

- Python 3.11+
- Ein kostenloser API-Schlüssel von [football-data.org](https://www.football-data.org/client/register)

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/ceelight/wm2026.git
cd wm2026
```

### 2. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 3. Umgebungsvariablen setzen

```bash
export SECRET_KEY="dein-zufaelliger-geheimer-schluessel"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="sicheres-passwort"
# Optional: eigene Datenbankdatei
# export DATABASE_URL="sqlite:///./wm2026.db"
```

`SECRET_KEY` wird für die Session-Signierung verwendet. Generiere einen zufälligen Wert, z. B.:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. App starten

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Die App ist dann unter `http://localhost:8000` erreichbar.

### 5. API-Token konfigurieren

1. Im Browser als Admin einloggen
2. **Admin → Einstellungen** aufrufen
3. Den football-data.org API-Token eintragen und speichern
4. Über **Admin → Spielverwaltung → API-Sync** die Spieldaten importieren

## Als Systemdienst betreiben (systemd)

Eine Beispiel-Unit-Datei liegt unter `wm2026.service`. Passe `User`, `WorkingDirectory` und die Umgebungsvariablen an:

```ini
[Service]
User=deinuser
WorkingDirectory=/opt/wm2026
Environment=SECRET_KEY=...
Environment=ADMIN_USERNAME=admin
Environment=ADMIN_PASSWORD=...
ExecStart=/home/deinuser/.local/bin/uvicorn app:app --host 0.0.0.0 --port 8000
```

```bash
sudo cp wm2026.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wm2026
```

## Umgebungsvariablen im Überblick

| Variable | Pflicht | Beschreibung |
|---|---|---|
| `SECRET_KEY` | Empfohlen | Session-Signierungsschlüssel |
| `ADMIN_USERNAME` | Optional | Benutzername des ersten Admins (Standard: `admin`) |
| `ADMIN_PASSWORD` | Ja* | Passwort des ersten Admins (* nur beim ersten Start) |
| `DATABASE_URL` | Optional | SQLAlchemy-Datenbank-URL (Standard: `sqlite:///./wm2026.db`) |

## Lizenz

MIT
