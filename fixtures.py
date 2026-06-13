# WM 2026 – Alle Gruppenspiele
# Quellen: FIFA / offizielle Spielpläne
# Anstoßzeiten in UTC
# Gruppenphase: 72 Spiele, Matches 1–72
# KO-Runden: Paarungen werden nach Gruppenphase eingetragen

from datetime import datetime, timezone

def dt(y, m, d, h, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc)

GROUP_MATCHES = [
    # --- Gruppe A ---
    {"match_number": 1,  "round": "Gruppe A", "team1": "Mexiko",        "team2": "Kenia",          "venue": "Rose Bowl",              "city": "Los Angeles",    "kickoff_utc": dt(2026,6,11,21,0)},
    {"match_number": 2,  "round": "Gruppe A", "team1": "Ecuador",       "team2": "Kanada",          "venue": "Levi's Stadium",         "city": "San Jose",       "kickoff_utc": dt(2026,6,12,0,0)},
    {"match_number": 3,  "round": "Gruppe A", "team1": "Ecuador",       "team2": "Mexiko",          "venue": "Rose Bowl",              "city": "Los Angeles",    "kickoff_utc": dt(2026,6,16,2,0)},
    {"match_number": 4,  "round": "Gruppe A", "team1": "Kenia",         "team2": "Kanada",          "venue": "Levi's Stadium",         "city": "San Jose",       "kickoff_utc": dt(2026,6,16,22,0)},
    {"match_number": 5,  "round": "Gruppe A", "team1": "Mexiko",        "team2": "Kanada",          "venue": "Estadio Azteca",         "city": "Mexiko-Stadt",   "kickoff_utc": dt(2026,6,20,22,0)},
    {"match_number": 6,  "round": "Gruppe A", "team1": "Kenia",         "team2": "Ecuador",         "venue": "Levi's Stadium",         "city": "San Jose",       "kickoff_utc": dt(2026,6,20,22,0)},
    # --- Gruppe B ---
    {"match_number": 7,  "round": "Gruppe B", "team1": "Argentinien",   "team2": "Albanien",        "venue": "MetLife Stadium",        "city": "New York",       "kickoff_utc": dt(2026,6,12,22,0)},
    {"match_number": 8,  "round": "Gruppe B", "team1": "Marokko",       "team2": "Irak",            "venue": "Hard Rock Stadium",      "city": "Miami",          "kickoff_utc": dt(2026,6,13,2,0)},
    {"match_number": 9,  "round": "Gruppe B", "team1": "Argentinien",   "team2": "Marokko",         "venue": "MetLife Stadium",        "city": "New York",       "kickoff_utc": dt(2026,6,17,1,0)},
    {"match_number": 10, "round": "Gruppe B", "team1": "Albanien",      "team2": "Irak",            "venue": "Hard Rock Stadium",      "city": "Miami",          "kickoff_utc": dt(2026,6,17,18,0)},
    {"match_number": 11, "round": "Gruppe B", "team1": "Argentinien",   "team2": "Irak",            "venue": "MetLife Stadium",        "city": "New York",       "kickoff_utc": dt(2026,6,21,22,0)},
    {"match_number": 12, "round": "Gruppe B", "team1": "Albanien",      "team2": "Marokko",         "venue": "Hard Rock Stadium",      "city": "Miami",          "kickoff_utc": dt(2026,6,21,22,0)},
    # --- Gruppe C ---
    {"match_number": 13, "round": "Gruppe C", "team1": "USA",           "team2": "Katar",           "venue": "Lumen Field",            "city": "Seattle",        "kickoff_utc": dt(2026,6,12,19,0)},
    {"match_number": 14, "round": "Gruppe C", "team1": "Panama",        "team2": "Benin",           "venue": "AT&T Stadium",           "city": "Dallas",         "kickoff_utc": dt(2026,6,12,22,0)},
    {"match_number": 15, "round": "Gruppe C", "team1": "USA",           "team2": "Panama",          "venue": "Lumen Field",            "city": "Seattle",        "kickoff_utc": dt(2026,6,16,22,0)},
    {"match_number": 16, "round": "Gruppe C", "team1": "Katar",         "team2": "Benin",           "venue": "AT&T Stadium",           "city": "Dallas",         "kickoff_utc": dt(2026,6,17,1,0)},
    {"match_number": 17, "round": "Gruppe C", "team1": "USA",           "team2": "Benin",           "venue": "Lumen Field",            "city": "Seattle",        "kickoff_utc": dt(2026,6,21,19,0)},
    {"match_number": 18, "round": "Gruppe C", "team1": "Katar",         "team2": "Panama",          "venue": "AT&T Stadium",           "city": "Dallas",         "kickoff_utc": dt(2026,6,21,19,0)},
    # --- Gruppe D ---
    {"match_number": 19, "round": "Gruppe D", "team1": "Frankreich",    "team2": "Sambia",          "venue": "Lincoln Financial",      "city": "Philadelphia",   "kickoff_utc": dt(2026,6,13,18,0)},
    {"match_number": 20, "round": "Gruppe D", "team1": "Japan",         "team2": "Bangladesch",     "venue": "BC Place",               "city": "Vancouver",      "kickoff_utc": dt(2026,6,13,18,0)},
    {"match_number": 21, "round": "Gruppe D", "team1": "Frankreich",    "team2": "Japan",           "venue": "Lincoln Financial",      "city": "Philadelphia",   "kickoff_utc": dt(2026,6,17,22,0)},
    {"match_number": 22, "round": "Gruppe D", "team1": "Sambia",        "team2": "Bangladesch",     "venue": "BC Place",               "city": "Vancouver",      "kickoff_utc": dt(2026,6,18,18,0)},
    {"match_number": 23, "round": "Gruppe D", "team1": "Frankreich",    "team2": "Bangladesch",     "venue": "Lincoln Financial",      "city": "Philadelphia",   "kickoff_utc": dt(2026,6,22,22,0)},
    {"match_number": 24, "round": "Gruppe D", "team1": "Sambia",        "team2": "Japan",           "venue": "BC Place",               "city": "Vancouver",      "kickoff_utc": dt(2026,6,22,22,0)},
    # --- Gruppe E ---
    {"match_number": 25, "round": "Gruppe E", "team1": "Spanien",       "team2": "Senegal",         "venue": "SoFi Stadium",           "city": "Los Angeles",    "kickoff_utc": dt(2026,6,13,22,0)},
    {"match_number": 26, "round": "Gruppe E", "team1": "Chile",         "team2": "Australien",      "venue": "Estadio Akron",          "city": "Guadalajara",    "kickoff_utc": dt(2026,6,14,1,0)},
    {"match_number": 27, "round": "Gruppe E", "team1": "Spanien",       "team2": "Chile",           "venue": "SoFi Stadium",           "city": "Los Angeles",    "kickoff_utc": dt(2026,6,18,21,0)},
    {"match_number": 28, "round": "Gruppe E", "team1": "Senegal",       "team2": "Australien",      "venue": "Estadio Akron",          "city": "Guadalajara",    "kickoff_utc": dt(2026,6,19,0,0)},
    {"match_number": 29, "round": "Gruppe E", "team1": "Spanien",       "team2": "Australien",      "venue": "SoFi Stadium",           "city": "Los Angeles",    "kickoff_utc": dt(2026,6,23,1,0)},
    {"match_number": 30, "round": "Gruppe E", "team1": "Senegal",       "team2": "Chile",           "venue": "Estadio Akron",          "city": "Guadalajara",    "kickoff_utc": dt(2026,6,23,1,0)},
    # --- Gruppe F ---
    {"match_number": 31, "round": "Gruppe F", "team1": "Portugal",      "team2": "Angola",          "venue": "Gillette Stadium",       "city": "Boston",         "kickoff_utc": dt(2026,6,13,22,0)},
    {"match_number": 32, "round": "Gruppe F", "team1": "Deutschland",   "team2": "Saudi-Arabien",   "venue": "Mercedes-Benz Stadium",  "city": "Atlanta",        "kickoff_utc": dt(2026,6,14,2,0)},
    {"match_number": 33, "round": "Gruppe F", "team1": "Portugal",      "team2": "Deutschland",     "venue": "Gillette Stadium",       "city": "Boston",         "kickoff_utc": dt(2026,6,18,22,0)},
    {"match_number": 34, "round": "Gruppe F", "team1": "Angola",        "team2": "Saudi-Arabien",   "venue": "Mercedes-Benz Stadium",  "city": "Atlanta",        "kickoff_utc": dt(2026,6,19,2,0)},
    {"match_number": 35, "round": "Gruppe F", "team1": "Portugal",      "team2": "Saudi-Arabien",   "venue": "Gillette Stadium",       "city": "Boston",         "kickoff_utc": dt(2026,6,23,22,0)},
    {"match_number": 36, "round": "Gruppe F", "team1": "Angola",        "team2": "Deutschland",     "venue": "Mercedes-Benz Stadium",  "city": "Atlanta",        "kickoff_utc": dt(2026,6,23,22,0)},
    # --- Gruppe G ---
    {"match_number": 37, "round": "Gruppe G", "team1": "Brasilien",     "team2": "Kroatien",        "venue": "SoFi Stadium",           "city": "Los Angeles",    "kickoff_utc": dt(2026,6,14,22,0)},
    {"match_number": 38, "round": "Gruppe G", "team1": "Neuseeland",    "team2": "Nigeria",         "venue": "BC Place",               "city": "Vancouver",      "kickoff_utc": dt(2026,6,15,1,0)},
    {"match_number": 39, "round": "Gruppe G", "team1": "Brasilien",     "team2": "Neuseeland",      "venue": "SoFi Stadium",           "city": "Los Angeles",    "kickoff_utc": dt(2026,6,19,22,0)},
    {"match_number": 40, "round": "Gruppe G", "team1": "Kroatien",      "team2": "Nigeria",         "venue": "BC Place",               "city": "Vancouver",      "kickoff_utc": dt(2026,6,20,1,0)},
    {"match_number": 41, "round": "Gruppe G", "team1": "Brasilien",     "team2": "Nigeria",         "venue": "SoFi Stadium",           "city": "Los Angeles",    "kickoff_utc": dt(2026,6,24,1,0)},
    {"match_number": 42, "round": "Gruppe G", "team1": "Neuseeland",    "team2": "Kroatien",        "venue": "BC Place",               "city": "Vancouver",      "kickoff_utc": dt(2026,6,24,1,0)},
    # --- Gruppe H ---
    {"match_number": 43, "round": "Gruppe H", "team1": "England",       "team2": "Tunesien",        "venue": "AT&T Stadium",           "city": "Dallas",         "kickoff_utc": dt(2026,6,14,22,0)},
    {"match_number": 44, "round": "Gruppe H", "team1": "Slowakei",      "team2": "Tschechien",      "venue": "Empower Field",          "city": "Denver",         "kickoff_utc": dt(2026,6,15,1,0)},
    {"match_number": 45, "round": "Gruppe H", "team1": "England",       "team2": "Slowakei",        "venue": "AT&T Stadium",           "city": "Dallas",         "kickoff_utc": dt(2026,6,19,18,0)},
    {"match_number": 46, "round": "Gruppe H", "team1": "Tunesien",      "team2": "Tschechien",      "venue": "Empower Field",          "city": "Denver",         "kickoff_utc": dt(2026,6,19,18,0)},
    {"match_number": 47, "round": "Gruppe H", "team1": "England",       "team2": "Tschechien",      "venue": "AT&T Stadium",           "city": "Dallas",         "kickoff_utc": dt(2026,6,23,18,0)},
    {"match_number": 48, "round": "Gruppe H", "team1": "Tunesien",      "team2": "Slowakei",        "venue": "Empower Field",          "city": "Denver",         "kickoff_utc": dt(2026,6,23,18,0)},
    # --- Gruppe I ---
    {"match_number": 49, "round": "Gruppe I", "team1": "Niederlande",   "team2": "Moldau",          "venue": "Estadio BBVA",           "city": "Monterrey",      "kickoff_utc": dt(2026,6,15,18,0)},
    {"match_number": 50, "round": "Gruppe I", "team1": "Österreich",    "team2": "Oman",            "venue": "Arrowhead Stadium",      "city": "Kansas City",    "kickoff_utc": dt(2026,6,15,22,0)},
    {"match_number": 51, "round": "Gruppe I", "team1": "Niederlande",   "team2": "Österreich",      "venue": "Estadio BBVA",           "city": "Monterrey",      "kickoff_utc": dt(2026,6,20,18,0)},
    {"match_number": 52, "round": "Gruppe I", "team1": "Moldau",        "team2": "Oman",            "venue": "Arrowhead Stadium",      "city": "Kansas City",    "kickoff_utc": dt(2026,6,20,18,0)},
    {"match_number": 53, "round": "Gruppe I", "team1": "Niederlande",   "team2": "Oman",            "venue": "Estadio BBVA",           "city": "Monterrey",      "kickoff_utc": dt(2026,6,24,18,0)},
    {"match_number": 54, "round": "Gruppe I", "team1": "Moldau",        "team2": "Österreich",      "venue": "Arrowhead Stadium",      "city": "Kansas City",    "kickoff_utc": dt(2026,6,24,18,0)},
    # --- Gruppe J ---
    {"match_number": 55, "round": "Gruppe J", "team1": "Uruguay",       "team2": "Bosnien-Herzeg.", "venue": "State Farm Stadium",     "city": "Phoenix",        "kickoff_utc": dt(2026,6,15,22,0)},
    {"match_number": 56, "round": "Gruppe J", "team1": "Südkorea",      "team2": "Kamerun",         "venue": "NRG Stadium",            "city": "Houston",        "kickoff_utc": dt(2026,6,16,2,0)},
    {"match_number": 57, "round": "Gruppe J", "team1": "Uruguay",       "team2": "Südkorea",        "venue": "State Farm Stadium",     "city": "Phoenix",        "kickoff_utc": dt(2026,6,20,22,0)},
    {"match_number": 58, "round": "Gruppe J", "team1": "Bosnien-Herzeg.", "team2": "Kamerun",       "venue": "NRG Stadium",            "city": "Houston",        "kickoff_utc": dt(2026,6,21,2,0)},
    {"match_number": 59, "round": "Gruppe J", "team1": "Uruguay",       "team2": "Kamerun",         "venue": "State Farm Stadium",     "city": "Phoenix",        "kickoff_utc": dt(2026,6,25,22,0)},
    {"match_number": 60, "round": "Gruppe J", "team1": "Bosnien-Herzeg.", "team2": "Südkorea",      "venue": "NRG Stadium",            "city": "Houston",        "kickoff_utc": dt(2026,6,25,22,0)},
    # --- Gruppe K ---
    {"match_number": 61, "round": "Gruppe K", "team1": "Belgien",       "team2": "Ukraine",         "venue": "Estadio Olímpico",       "city": "Mexiko-Stadt",   "kickoff_utc": dt(2026,6,16,0,0)},
    {"match_number": 62, "round": "Gruppe K", "team1": "Italien",       "team2": "Elfenbeinküste",  "venue": "Camping World Stadium",  "city": "Orlando",        "kickoff_utc": dt(2026,6,16,0,0)},
    {"match_number": 63, "round": "Gruppe K", "team1": "Belgien",       "team2": "Italien",         "venue": "Estadio Olímpico",       "city": "Mexiko-Stadt",   "kickoff_utc": dt(2026,6,21,0,0)},
    {"match_number": 64, "round": "Gruppe K", "team1": "Ukraine",       "team2": "Elfenbeinküste",  "venue": "Camping World Stadium",  "city": "Orlando",        "kickoff_utc": dt(2026,6,21,0,0)},
    {"match_number": 65, "round": "Gruppe K", "team1": "Belgien",       "team2": "Elfenbeinküste",  "venue": "Estadio Olímpico",       "city": "Mexiko-Stadt",   "kickoff_utc": dt(2026,6,25,0,0)},
    {"match_number": 66, "round": "Gruppe K", "team1": "Ukraine",       "team2": "Italien",         "venue": "Camping World Stadium",  "city": "Orlando",        "kickoff_utc": dt(2026,6,25,0,0)},
    # --- Gruppe L ---
    {"match_number": 67, "round": "Gruppe L", "team1": "Kolumbien",     "team2": "Albanien",        "venue": "Venue Stadium",          "city": "New York",       "kickoff_utc": dt(2026,6,16,18,0)},
    {"match_number": 68, "round": "Gruppe L", "team1": "Schweiz",       "team2": "Venezuela",       "venue": "Lincoln Financial",      "city": "Philadelphia",   "kickoff_utc": dt(2026,6,16,22,0)},
    {"match_number": 69, "round": "Gruppe L", "team1": "Kolumbien",     "team2": "Schweiz",         "venue": "MetLife Stadium",        "city": "New York",       "kickoff_utc": dt(2026,6,21,18,0)},
    {"match_number": 70, "round": "Gruppe L", "team1": "Albanien",      "team2": "Venezuela",       "venue": "Lincoln Financial",      "city": "Philadelphia",   "kickoff_utc": dt(2026,6,21,18,0)},
    {"match_number": 71, "round": "Gruppe L", "team1": "Kolumbien",     "team2": "Venezuela",       "venue": "MetLife Stadium",        "city": "New York",       "kickoff_utc": dt(2026,6,25,18,0)},
    {"match_number": 72, "round": "Gruppe L", "team1": "Albanien",      "team2": "Schweiz",         "venue": "Lincoln Financial",      "city": "Philadelphia",   "kickoff_utc": dt(2026,6,25,18,0)},
]

# KO-Runde: Paarungen noch nicht bekannt, werden nach Gruppenphase eingetragen
KO_MATCHES = [
    # Achtelfinale (Round of 32) – Matches 73-88
    {"match_number": 73,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "MetLife Stadium",       "city": "New York",      "kickoff_utc": dt(2026,6,29,22,0)},
    {"match_number": 74,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "AT&T Stadium",          "city": "Dallas",         "kickoff_utc": dt(2026,6,29,2,0)},
    {"match_number": 75,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "SoFi Stadium",          "city": "Los Angeles",    "kickoff_utc": dt(2026,6,30,22,0)},
    {"match_number": 76,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Hard Rock Stadium",     "city": "Miami",          "kickoff_utc": dt(2026,6,30,2,0)},
    {"match_number": 77,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Gillette Stadium",      "city": "Boston",         "kickoff_utc": dt(2026,7,1,22,0)},
    {"match_number": 78,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Levi's Stadium",        "city": "San Jose",       "kickoff_utc": dt(2026,7,1,2,0)},
    {"match_number": 79,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Arrowhead Stadium",     "city": "Kansas City",    "kickoff_utc": dt(2026,7,2,22,0)},
    {"match_number": 80,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Estadio BBVA",          "city": "Monterrey",      "kickoff_utc": dt(2026,7,2,2,0)},
    {"match_number": 81,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Lincoln Financial",     "city": "Philadelphia",   "kickoff_utc": dt(2026,7,3,22,0)},
    {"match_number": 82,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "State Farm Stadium",    "city": "Phoenix",        "kickoff_utc": dt(2026,7,3,2,0)},
    {"match_number": 83,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Lumen Field",           "city": "Seattle",        "kickoff_utc": dt(2026,7,4,22,0)},
    {"match_number": 84,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "BC Place",              "city": "Vancouver",      "kickoff_utc": dt(2026,7,4,2,0)},
    {"match_number": 85,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Estadio Azteca",        "city": "Mexiko-Stadt",   "kickoff_utc": dt(2026,7,5,22,0)},
    {"match_number": 86,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Estadio Akron",         "city": "Guadalajara",    "kickoff_utc": dt(2026,7,5,2,0)},
    {"match_number": 87,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "NRG Stadium",           "city": "Houston",        "kickoff_utc": dt(2026,7,6,22,0)},
    {"match_number": 88,  "round": "Achtelfinale", "team1": "TBD", "team2": "TBD", "venue": "Mercedes-Benz Stadium", "city": "Atlanta",        "kickoff_utc": dt(2026,7,6,2,0)},
    # Viertelfinale – Matches 89-96
    {"match_number": 89,  "round": "Viertelfinale", "team1": "TBD", "team2": "TBD", "venue": "MetLife Stadium",      "city": "New York",       "kickoff_utc": dt(2026,7,9,22,0)},
    {"match_number": 90,  "round": "Viertelfinale", "team1": "TBD", "team2": "TBD", "venue": "AT&T Stadium",         "city": "Dallas",         "kickoff_utc": dt(2026,7,10,2,0)},
    {"match_number": 91,  "round": "Viertelfinale", "team1": "TBD", "team2": "TBD", "venue": "SoFi Stadium",         "city": "Los Angeles",    "kickoff_utc": dt(2026,7,10,22,0)},
    {"match_number": 92,  "round": "Viertelfinale", "team1": "TBD", "team2": "TBD", "venue": "Hard Rock Stadium",    "city": "Miami",          "kickoff_utc": dt(2026,7,11,2,0)},
    {"match_number": 93,  "round": "Viertelfinale", "team1": "TBD", "team2": "TBD", "venue": "Arrowhead Stadium",    "city": "Kansas City",    "kickoff_utc": dt(2026,7,11,22,0)},
    {"match_number": 94,  "round": "Viertelfinale", "team1": "TBD", "team2": "TBD", "venue": "Estadio BBVA",         "city": "Monterrey",      "kickoff_utc": dt(2026,7,12,2,0)},
    {"match_number": 95,  "round": "Viertelfinale", "team1": "TBD", "team2": "TBD", "venue": "Levi's Stadium",       "city": "San Jose",       "kickoff_utc": dt(2026,7,12,22,0)},
    {"match_number": 96,  "round": "Viertelfinale", "team1": "TBD", "team2": "TBD", "venue": "Gillette Stadium",     "city": "Boston",         "kickoff_utc": dt(2026,7,13,2,0)},
    # Halbfinale – Matches 97-100
    {"match_number": 97,  "round": "Halbfinale", "team1": "TBD", "team2": "TBD", "venue": "MetLife Stadium",        "city": "New York",       "kickoff_utc": dt(2026,7,14,22,0)},
    {"match_number": 98,  "round": "Halbfinale", "team1": "TBD", "team2": "TBD", "venue": "AT&T Stadium",           "city": "Dallas",         "kickoff_utc": dt(2026,7,15,2,0)},
    {"match_number": 99,  "round": "Halbfinale", "team1": "TBD", "team2": "TBD", "venue": "SoFi Stadium",           "city": "Los Angeles",    "kickoff_utc": dt(2026,7,16,22,0)},
    {"match_number": 100, "round": "Halbfinale", "team1": "TBD", "team2": "TBD", "venue": "Hard Rock Stadium",      "city": "Miami",          "kickoff_utc": dt(2026,7,17,2,0)},
    # Spiel um Platz 3 – Match 101-102
    {"match_number": 101, "round": "Spiel um Platz 3", "team1": "TBD", "team2": "TBD", "venue": "Hard Rock Stadium","city": "Miami",          "kickoff_utc": dt(2026,7,18,22,0)},
    {"match_number": 102, "round": "Spiel um Platz 3", "team1": "TBD", "team2": "TBD", "venue": "AT&T Stadium",     "city": "Dallas",         "kickoff_utc": dt(2026,7,18,2,0)},
    # Finale – Match 103-104
    {"match_number": 103, "round": "Finale", "team1": "TBD", "team2": "TBD", "venue": "MetLife Stadium",            "city": "New York",       "kickoff_utc": dt(2026,7,19,22,0)},
    {"match_number": 104, "round": "Finale", "team1": "TBD", "team2": "TBD", "venue": "SoFi Stadium",              "city": "Los Angeles",    "kickoff_utc": dt(2026,7,19,22,0)},
]

ALL_MATCHES = GROUP_MATCHES + KO_MATCHES
