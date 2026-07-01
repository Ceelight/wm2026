"""
Führt ausstehende Datenbank-Migrationen durch.
Sicher mehrfach ausführbar (idempotent).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import engine
from sqlalchemy import text

migrations = [
    ("users.tips_public",
     "ALTER TABLE users ADD COLUMN tips_public BOOLEAN NOT NULL DEFAULT 1"),
    ("champion_tips", """
        CREATE TABLE IF NOT EXISTS champion_tips (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            team VARCHAR(64) NOT NULL,
            points INTEGER DEFAULT 0
        )"""),
    ("top_scorer_tips", """
        CREATE TABLE IF NOT EXISTS top_scorer_tips (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            player VARCHAR(128) NOT NULL,
            points INTEGER DEFAULT 0
        )"""),
    ("notifications", """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            message VARCHAR(256) NOT NULL,
            created_at DATETIME,
            read BOOLEAN NOT NULL DEFAULT 0
        )"""),
]

with engine.connect() as conn:
    for name, sql in migrations:
        try:
            conn.execute(text(sql))
            print(f"✓ {name}")
        except Exception as e:
            print(f"  {name}: bereits vorhanden ({e})")
    conn.commit()

    # Rundenname korrigieren: "Runde der 32" hieß fachlich korrekt "Sechzehntelfinale"
    result = conn.execute(text("UPDATE matches SET round = 'Sechzehntelfinale' WHERE round = 'Runde der 32'"))
    conn.commit()
    if result.rowcount:
        print(f"✓ {result.rowcount} Spiele von 'Runde der 32' zu 'Sechzehntelfinale' umbenannt")

print("Migration abgeschlossen.")
