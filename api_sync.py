"""
Synchronisation mit football-data.org API.
Importiert alle WM-Spiele und aktualisiert Ergebnisse.
"""
import json
import logging
import urllib.request
from datetime import datetime

logger = logging.getLogger(__name__)

API_URL = "https://api.football-data.org/v4/competitions/WC/matches"

# Englische Teamnamen → Deutsch
TEAM_NAMES = {
    "Mexico": "Mexiko",
    "South Africa": "Südafrika",
    "South Korea": "Südkorea",
    "Czechia": "Tschechien",
    "Canada": "Kanada",
    "Bosnia-Herzegovina": "Bosnien-Herzeg.",
    "Qatar": "Katar",
    "Switzerland": "Schweiz",
    "Brazil": "Brasilien",
    "Morocco": "Marokko",
    "Haiti": "Haiti",
    "Scotland": "Schottland",
    "United States": "USA",
    "Paraguay": "Paraguay",
    "Australia": "Australien",
    "Turkey": "Türkei",
    "Germany": "Deutschland",
    "Curaçao": "Curaçao",
    "Ivory Coast": "Elfenbeinküste",
    "Ecuador": "Ecuador",
    "Netherlands": "Niederlande",
    "Japan": "Japan",
    "Sweden": "Schweden",
    "Tunisia": "Tunesien",
    "Spain": "Spanien",
    "Cape Verde Islands": "Kap Verde",
    "Saudi Arabia": "Saudi-Arabien",
    "Uruguay": "Uruguay",
    "Belgium": "Belgien",
    "Egypt": "Ägypten",
    "Iran": "Iran",
    "New Zealand": "Neuseeland",
    "France": "Frankreich",
    "Senegal": "Senegal",
    "Iraq": "Irak",
    "Norway": "Norwegen",
    "Argentina": "Argentinien",
    "Algeria": "Algerien",
    "Austria": "Österreich",
    "Jordan": "Jordanien",
    "Portugal": "Portugal",
    "Congo DR": "DR Kongo",
    "Uzbekistan": "Usbekistan",
    "Colombia": "Kolumbien",
    "England": "England",
    "Croatia": "Kroatien",
    "Ghana": "Ghana",
    "Panama": "Panama",
}

STAGE_NAMES = {
    "GROUP_STAGE": None,   # handled separately using group letter
    "LAST_32": "Sechzehntelfinale",
    "LAST_16": "Achtelfinale",
    "QUARTER_FINALS": "Viertelfinale",
    "SEMI_FINALS": "Halbfinale",
    "THIRD_PLACE": "Spiel um Platz 3",
    "FINAL": "Finale",
}

STATUS_MAP = {
    "SCHEDULED": "scheduled",
    "TIMED": "scheduled",
    "IN_PLAY": "live",
    "PAUSED": "live",
    "FINISHED": "finished",
    "SUSPENDED": "scheduled",
    "POSTPONED": "scheduled",
    "CANCELLED": "scheduled",
    "AWARDED": "finished",
}


def german(name: str) -> str:
    return TEAM_NAMES.get(name, name) if name else "TBD"


def round_name(stage: str, group: str | None) -> str:
    if stage == "GROUP_STAGE" and group:
        letter = group.replace("GROUP_", "")
        return f"Gruppe {letter}"
    return STAGE_NAMES.get(stage, stage)


def fetch_matches_from_api(token: str) -> list[dict]:
    if not token:
        raise ValueError("Kein API-Token konfiguriert. Bitte in der Admin-UI unter Einstellungen eintragen.")
    req = urllib.request.Request(API_URL, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    return data["matches"]


def sync_matches(db, token: str = ""):
    """Importiert/aktualisiert alle Spiele aus der API in die Datenbank."""
    from models import Match
    try:
        api_matches = fetch_matches_from_api(token)
    except Exception as e:
        logger.error("API-Abruf fehlgeschlagen: %s", e)
        return 0

    updated = 0
    for i, m in enumerate(api_matches, 1):
        api_id = m["id"]
        match = db.query(Match).filter_by(api_id=api_id).first()

        team1 = german(m["homeTeam"].get("name") or m["homeTeam"].get("shortName"))
        team2 = german(m["awayTeam"].get("name") or m["awayTeam"].get("shortName"))
        score1 = m["score"]["fullTime"]["home"]
        score2 = m["score"]["fullTime"]["away"]
        status = STATUS_MAP.get(m["status"], "scheduled")
        kickoff = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).replace(tzinfo=None)
        rnd = round_name(m["stage"], m.get("group"))

        if match is None:
            match = Match(
                match_number=i,
                api_id=api_id,
                round=rnd,
                team1=team1,
                team2=team2,
                kickoff_utc=kickoff,
                score1=score1,
                score2=score2,
                status=status,
            )
            db.add(match)
        else:
            match.team1 = team1
            match.team2 = team2
            match.kickoff_utc = kickoff
            match.score1 = score1
            match.score2 = score2
            match.status = status
            match.round = rnd

        updated += 1

    db.commit()
    logger.info("API-Sync: %d Spiele aktualisiert", updated)
    return updated


def sync_and_recalc(db_factory, calc_fn, get_token_fn=None):
    """Komplett-Sync: Ergebnisse holen + Punkte neu berechnen."""
    db = db_factory()
    try:
        token = get_token_fn(db) if get_token_fn else ""
        n = sync_matches(db, token)
        calc_fn(db)
        logger.info("Punkte neu berechnet nach API-Sync (%d Spiele)", n)
    except Exception as e:
        logger.error("Sync-Fehler: %s", e)
    finally:
        db.close()
