import json
import logging
import os
import bcrypt
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, Form, Depends, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature
from sqlalchemy.orm import Session

from api_sync import sync_and_recalc
from database import get_db, init_db, SessionLocal
from models import User, Match, Tip, Setting, ChampionTip, TopScorerTip, Notification

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

SECRET_KEY = os.environ.get("SECRET_KEY", "wm2026-super-secret-key-change-me")
COOKIE_NAME = "session"
serializer = URLSafeTimedSerializer(SECRET_KEY)

LOCALES_DIR = BASE_DIR / "locales"
_translations: dict[str, dict] = {}

def load_translations():
    for lang in ("de", "en", "es"):
        path = LOCALES_DIR / f"{lang}.json"
        with open(path, encoding="utf-8") as f:
            _translations[lang] = json.load(f)

load_translations()
templates.env.globals["enumerate"] = enumerate

def fmt_mesz(dt: datetime) -> str:
    return (dt + timedelta(hours=2)).strftime('%d.%m. %H:%M')

templates.env.filters["fmt_mesz"] = fmt_mesz


def t(lang: str, key: str) -> str:
    return _translations.get(lang, _translations["de"]).get(key, key)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def create_session(user_id: int) -> str:
    return serializer.dumps({"uid": user_id})


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=60 * 60 * 24 * 14)  # 14 days
        return db.query(User).get(data["uid"])
    except BadSignature:
        return None


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return user


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = require_user(request, db)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


# ---------------------------------------------------------------------------
# Points calculation
# ---------------------------------------------------------------------------
def calc_points(tip1: int, tip2: int, score1: int, score2: int) -> int:
    if score1 is None or score2 is None or tip1 is None or tip2 is None:
        return 0
    # Exact result
    if tip1 == score1 and tip2 == score2:
        return 3
    tip_winner = (1 if tip1 > tip2 else -1 if tip1 < tip2 else 0)
    real_winner = (1 if score1 > score2 else -1 if score1 < score2 else 0)
    if tip_winner != real_winner:
        return 0
    # Draw tipped and result is draw, but not exact score
    if tip_winner == 0 and real_winner == 0:
        return 2
    # Same winner (non-draw): same goal difference = 2, otherwise = 1
    if tip1 - tip2 == score1 - score2:
        return 2
    return 1


KO_ROUND_ORDER = [
    "Sechzehntelfinale",
    "Achtelfinale",
    "Viertelfinale",
    "Halbfinale",
    "Spiel um Platz 3",
    "Finale",
]

ROUND_LOCALE_KEYS = {
    "Sechzehntelfinale": "round_of_32",
    "Achtelfinale": "round_of_16",
    "Viertelfinale": "quarterfinals",
    "Halbfinale": "semifinals",
    "Spiel um Platz 3": "third_place",
    "Finale": "final",
}


def round_sort_key(r: str):
    if r.startswith("Gruppe "):
        return (0, r[-1])  # Gruppe A → (0, "A"), Gruppe B → (0, "B"), ...
    if r in KO_ROUND_ORDER:
        return (KO_ROUND_ORDER.index(r) + 1, "")
    return (9, r)


def translate_round(lang: str, round_str: str) -> str:
    """Übersetzt einen in der DB gespeicherten Runden-String (z. B. 'Gruppe A', 'Achtelfinale')
    in die Anzeigesprache des Users."""
    if round_str.startswith("Gruppe "):
        letter = round_str[len("Gruppe "):]
        return f"{t(lang, 'group')} {letter}"
    key = ROUND_LOCALE_KEYS.get(round_str)
    return t(lang, key) if key else round_str


def group_phase_over(db: Session) -> bool:
    """True sobald das erste KO-Spiel angepfiffen wurde."""
    first_ko = (
        db.query(Match)
        .filter(~Match.round.startswith("Gruppe "))
        .order_by(Match.kickoff_utc)
        .first()
    )
    if first_ko is None:
        return False
    return datetime.utcnow() >= first_ko.kickoff_utc


def get_champion(db: Session) -> Optional[str]:
    """Gibt den Weltmeister zurück (Sieger des Finales), oder None."""
    final = db.query(Match).filter_by(round="Finale").first()
    if not final or final.status != "finished" or final.score1 is None:
        return None
    if final.score1 > final.score2:
        return final.team1
    if final.score2 > final.score1:
        return final.team2
    return None


def award_champion_points(db: Session):
    champion = get_champion(db)
    if not champion:
        return
    for ct in db.query(ChampionTip).all():
        ct.points = 10 if ct.team == champion else 0
    db.commit()


def get_top_scorer(db: Session) -> Optional[str]:
    setting = db.query(Setting).filter_by(key="top_scorer").first()
    return setting.value if setting and setting.value else None


def award_scorer_points(db: Session):
    scorer = get_top_scorer(db)
    if not scorer:
        return
    for st in db.query(TopScorerTip).all():
        st.points = 10 if st.player.strip().lower() == scorer.strip().lower() else 0
    db.commit()


def get_api_token(db: Session) -> str:
    setting = db.query(Setting).filter_by(key="api_token").first()
    return setting.value if setting else ""


def recalculate_all_points(db: Session):
    for tip in db.query(Tip).all():
        match = tip.match
        if match.status == "finished" and match.score1 is not None:
            tip.points = calc_points(tip.tip_score1, tip.tip_score2, match.score1, match.score2)
        else:
            tip.points = 0
    db.commit()
    award_champion_points(db)
    award_scorer_points(db)


def notify(db: Session, target_user: User, key: str, **kwargs):
    """Legt eine Benachrichtigung an, die dem User beim nächsten Seitenaufruf angezeigt wird."""
    msg = t(target_user.language, key).format(**kwargs)
    db.add(Notification(user_id=target_user.id, message=msg))
    db.commit()


# ---------------------------------------------------------------------------
# Template helper
# ---------------------------------------------------------------------------
def base_ctx(user: User, db: Session = None, extra: dict = None) -> dict:
    lang = user.language if user else "de"
    notifications = []
    if user and db:
        notifications = (
            db.query(Notification)
            .filter_by(user_id=user.id, read=False)
            .order_by(Notification.created_at)
            .all()
        )
        if notifications:
            for n in notifications:
                n.read = True
            db.commit()
    ctx = {
        "user": user,
        "lang": lang,
        "t": lambda key: t(lang, key),
        "tr_round": lambda r: translate_round(lang, r),
        "now": datetime.utcnow(),
        "notifications": notifications,
    }
    if extra:
        ctx.update(extra)
    return ctx


# ---------------------------------------------------------------------------
# Routes – Auth
# ---------------------------------------------------------------------------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {
        "error": None,
        "t": lambda key: t("de", key), "lang": "de",
    })


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...),
                db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username).first()
    if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        response = RedirectResponse("/", status_code=302)
        response.set_cookie(COOKIE_NAME, create_session(user.id), httponly=True, max_age=60*60*24*14)
        return response
    lang = user.language if user else "de"
    return templates.TemplateResponse(request, "login.html", {
        "error": True,
        "t": lambda key: t(lang, key), "lang": lang,
    })


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


# ---------------------------------------------------------------------------
# Routes – Dashboard
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db),
                    user: User = Depends(require_user)):
    matches = db.query(Match).order_by(Match.kickoff_utc).all()
    my_tips = {tip.match_id: tip for tip in db.query(Tip).filter_by(user_id=user.id).all()}
    now = datetime.utcnow()

    rounds = sorted(set(m.round for m in matches), key=round_sort_key)

    # Gruppentabellen basierend auf den Tipps des eingeloggten Users
    group_tables = {}
    for rnd in rounds:
        if not rnd.startswith("Gruppe "):
            continue
        group_matches = [m for m in matches if m.round == rnd]
        teams = {}
        for m in group_matches:
            for t in (m.team1, m.team2):
                if t not in teams:
                    teams[t] = {"team": t, "sp": 0, "s": 0, "u": 0, "n": 0,
                                "tore": 0, "gegentore": 0, "td": 0, "pts": 0}
        for m in group_matches:
            tip = my_tips.get(m.id)
            if not tip or tip.tip_score1 is None:
                continue
            g1, g2 = tip.tip_score1, tip.tip_score2
            t1, t2 = teams[m.team1], teams[m.team2]
            t1["sp"] += 1; t2["sp"] += 1
            t1["tore"] += g1; t1["gegentore"] += g2
            t2["tore"] += g2; t2["gegentore"] += g1
            if g1 > g2:
                t1["s"] += 1; t1["pts"] += 3; t2["n"] += 1
            elif g1 < g2:
                t2["s"] += 1; t2["pts"] += 3; t1["n"] += 1
            else:
                t1["u"] += 1; t1["pts"] += 1
                t2["u"] += 1; t2["pts"] += 1
        for t in teams.values():
            t["td"] = t["tore"] - t["gegentore"]
        group_tables[rnd] = sorted(
            teams.values(),
            key=lambda t: (-t["pts"], -t["td"], -t["tore"], t["team"])
        )

    # Nächstes Spiel (live oder nächstes anstehendes)
    next_match = None
    live = [m for m in matches if m.status == "live"]
    if live:
        next_match = live[0]
    else:
        upcoming = [m for m in matches if m.status == "scheduled" and m.kickoff_utc > now]
        if upcoming:
            next_match = upcoming[0]

    # Weltmeister-Tipp
    all_teams = sorted({t for m in matches for t in (m.team1, m.team2) if t != "TBD"})
    champion_tip = db.query(ChampionTip).filter_by(user_id=user.id).first()
    scorer_tip = db.query(TopScorerTip).filter_by(user_id=user.id).first()
    gp_over = group_phase_over(db)
    champion = get_champion(db)
    top_scorer = get_top_scorer(db)

    # Nach der Gruppenphase: standardmäßig nur die aktuelle KO-Runde anzeigen.
    # Alte Runden bleiben über die Runden-Auswahl weiterhin einsehbar.
    default_round = "all"
    if gp_over:
        ko_rounds = [r for r in rounds if not r.startswith("Gruppe ")]
        if ko_rounds:
            default_round = ko_rounds[-1]
            for r in ko_rounds:
                round_matches = [m for m in matches if m.round == r]
                if any(m.status != "finished" for m in round_matches):
                    default_round = r
                    break

    return templates.TemplateResponse(request, "dashboard.html", base_ctx(user, db, {
        "matches": matches,
        "my_tips": my_tips,
        "rounds": rounds,
        "group_tables": group_tables,
        "now": now,
        "next_match": next_match,
        "all_teams": all_teams,
        "champion_tip": champion_tip,
        "scorer_tip": scorer_tip,
        "group_phase_over": gp_over,
        "champion": champion,
        "top_scorer": top_scorer,
        "default_round": default_round,
    }))


# ---------------------------------------------------------------------------
# Routes – Tips
# ---------------------------------------------------------------------------
@app.post("/tip/{match_id}")
async def save_tip(match_id: int, tip_score1: Optional[int] = Form(None),
                   tip_score2: Optional[int] = Form(None),
                   db: Session = Depends(get_db), user: User = Depends(require_user)):
    match = db.query(Match).get(match_id)
    if not match:
        raise HTTPException(404)
    now = datetime.utcnow()
    kickoff = match.kickoff_utc
    if kickoff.tzinfo is not None:
        kickoff = kickoff.replace(tzinfo=None)
    if now >= kickoff and not match.tips_open:
        return Response("locked", status_code=403)

    tip = db.query(Tip).filter_by(user_id=user.id, match_id=match_id).first()
    if tip is None:
        tip = Tip(user_id=user.id, match_id=match_id)
        db.add(tip)
    tip.tip_score1 = tip_score1
    tip.tip_score2 = tip_score2
    tip.updated_at = datetime.utcnow()
    db.commit()
    return Response("ok", status_code=200)


# ---------------------------------------------------------------------------
# Routes – Champion tip
# ---------------------------------------------------------------------------
@app.post("/scorer-tip")
async def save_scorer_tip(player: str = Form(...), redirect: str = Form("/"),
                           db: Session = Depends(get_db), user: User = Depends(require_user)):
    if group_phase_over(db):
        return Response("locked", status_code=403)
    player = player.strip()
    if not player:
        return RedirectResponse(redirect, status_code=302)
    st = db.query(TopScorerTip).filter_by(user_id=user.id).first()
    if st:
        st.player = player
    else:
        st = TopScorerTip(user_id=user.id, player=player)
        db.add(st)
    db.commit()
    return RedirectResponse(redirect, status_code=302)


@app.post("/champion-tip")
async def save_champion_tip(team: str = Form(...), redirect: str = Form("/"),
                             db: Session = Depends(get_db), user: User = Depends(require_user)):
    if group_phase_over(db):
        return Response("locked", status_code=403)
    ct = db.query(ChampionTip).filter_by(user_id=user.id).first()
    if ct:
        ct.team = team
    else:
        ct = ChampionTip(user_id=user.id, team=team)
        db.add(ct)
    db.commit()
    return RedirectResponse(redirect, status_code=302)


# ---------------------------------------------------------------------------
# Routes – Sondertipps
# ---------------------------------------------------------------------------
@app.get("/sondertipps", response_class=HTMLResponse)
async def sondertipps(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(require_user)):
    matches = db.query(Match).all()
    all_teams = sorted({t for m in matches for t in (m.team1, m.team2) if t != "TBD"})
    champion_tip = db.query(ChampionTip).filter_by(user_id=user.id).first()
    scorer_tip = db.query(TopScorerTip).filter_by(user_id=user.id).first()
    gp_over = group_phase_over(db)
    champion = get_champion(db)
    top_scorer = get_top_scorer(db)
    return templates.TemplateResponse(request, "sondertipps.html", base_ctx(user, db, {
        "all_teams": all_teams,
        "champion_tip": champion_tip,
        "scorer_tip": scorer_tip,
        "group_phase_over": gp_over,
        "champion": champion,
        "top_scorer": top_scorer,
    }))


# ---------------------------------------------------------------------------
# Routes – Leaderboard
# ---------------------------------------------------------------------------
@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(require_user)):
    all_users = db.query(User).order_by(User.username).all()

    board = []
    for u in all_users:
        total = sum(tip.points for tip in u.tips)
        if u.champion_tip:
            total += u.champion_tip.points
        if u.scorer_tip:
            total += u.scorer_tip.points
        board.append({"user": u, "total": total})
    board.sort(key=lambda x: x["total"], reverse=True)

    # Add rank (shared rank for equal points)
    for i, entry in enumerate(board):
        if i == 0 or entry["total"] < board[i - 1]["total"]:
            entry["rank"] = i + 1
        else:
            entry["rank"] = board[i - 1]["rank"]

    return templates.TemplateResponse(request, "leaderboard.html", base_ctx(user, db, {
        "board": board,
    }))


# ---------------------------------------------------------------------------
# Routes – Match detail (all tips for one match)
# ---------------------------------------------------------------------------
@app.get("/match/{match_id}", response_class=HTMLResponse)
async def match_detail(match_id: int, request: Request,
                       db: Session = Depends(get_db), user: User = Depends(require_user)):
    match = db.query(Match).get(match_id)
    if not match:
        raise HTTPException(404)
    now = datetime.utcnow()
    kickoff = match.kickoff_utc
    locked = now >= kickoff and not match.tips_open

    all_users = db.query(User).order_by(User.username).all()
    tips_by_user = {t.user_id: t for t in db.query(Tip).filter_by(match_id=match_id).all()}
    my_tip = tips_by_user.get(user.id)

    rows = []
    for u in all_users:
        tip = tips_by_user.get(u.id)
        visible = u.tips_public or u.id == user.id or user.role == "admin"
        rows.append({"user": u, "tip": tip if visible else None, "hidden": not visible})

    return templates.TemplateResponse(request, "match_detail.html", base_ctx(user, db, {
        "match": match,
        "rows": rows,
        "my_tip": my_tip,
        "locked": locked,
    }))


# ---------------------------------------------------------------------------
# Routes – Admin: Tipps aller Spieler nachträglich ändern
# ---------------------------------------------------------------------------
@app.post("/admin/tip/{match_id}/{target_user_id}")
async def admin_edit_tip(match_id: int, target_user_id: int,
                         tip_score1: Optional[int] = Form(None),
                         tip_score2: Optional[int] = Form(None),
                         db: Session = Depends(get_db), user: User = Depends(require_admin)):
    match = db.query(Match).get(match_id)
    target = db.query(User).get(target_user_id)
    if not match or not target:
        raise HTTPException(404)

    tip = db.query(Tip).filter_by(user_id=target_user_id, match_id=match_id).first()
    if tip is None:
        tip = Tip(user_id=target_user_id, match_id=match_id)
        db.add(tip)
    tip.tip_score1 = tip_score1
    tip.tip_score2 = tip_score2
    tip.updated_at = datetime.utcnow()
    if match.status == "finished" and match.score1 is not None and tip_score1 is not None and tip_score2 is not None:
        tip.points = calc_points(tip_score1, tip_score2, match.score1, match.score2)
    else:
        tip.points = 0
    db.commit()

    notify(db, target, "notify_tip_changed", match=f"{match.team1} vs {match.team2}")
    return RedirectResponse(f"/match/{match_id}", status_code=302)


@app.post("/admin/champion-tip/{target_user_id}")
async def admin_edit_champion_tip(target_user_id: int, team: str = Form(""),
                                   db: Session = Depends(get_db), user: User = Depends(require_admin)):
    target = db.query(User).get(target_user_id)
    if not target:
        raise HTTPException(404)
    team = team.strip()
    if not team:
        return RedirectResponse("/admin/settings", status_code=302)
    ct = db.query(ChampionTip).filter_by(user_id=target_user_id).first()
    if ct:
        ct.team = team
    else:
        ct = ChampionTip(user_id=target_user_id, team=team)
        db.add(ct)
    db.commit()
    award_champion_points(db)

    notify(db, target, "notify_champion_changed")
    return RedirectResponse("/admin/settings", status_code=302)


@app.post("/admin/scorer-tip/{target_user_id}")
async def admin_edit_scorer_tip(target_user_id: int, player: str = Form(""),
                                db: Session = Depends(get_db), user: User = Depends(require_admin)):
    target = db.query(User).get(target_user_id)
    if not target:
        raise HTTPException(404)
    player = player.strip()
    if not player:
        return RedirectResponse("/admin/settings", status_code=302)
    st = db.query(TopScorerTip).filter_by(user_id=target_user_id).first()
    if st:
        st.player = player
    else:
        st = TopScorerTip(user_id=target_user_id, player=player)
        db.add(st)
    db.commit()
    award_scorer_points(db)

    notify(db, target, "notify_scorer_changed")
    return RedirectResponse("/admin/settings", status_code=302)


# ---------------------------------------------------------------------------
# Routes – View other user's tips
# ---------------------------------------------------------------------------
@app.get("/tips/{target_user_id}", response_class=HTMLResponse)
async def view_user_tips(target_user_id: int, request: Request,
                         db: Session = Depends(get_db), user: User = Depends(require_user)):
    target = db.query(User).get(target_user_id)
    if not target:
        raise HTTPException(404)
    if not target.tips_public and target.id != user.id and user.role != "admin":
        return templates.TemplateResponse(request, "tips_private.html", base_ctx(user, db, {
            "target": target,
        }))
    matches = db.query(Match).order_by(Match.kickoff_utc).all()
    their_tips = {tip.match_id: tip for tip in db.query(Tip).filter_by(user_id=target_user_id).all()}
    my_tips = {tip.match_id: tip for tip in db.query(Tip).filter_by(user_id=user.id).all()}
    now = datetime.utcnow()
    return templates.TemplateResponse(request, "other_tips.html", base_ctx(user, db, {
        "target": target,
        "matches": matches,
        "their_tips": their_tips,
        "my_tips": my_tips,
        "now": now,
    }))


# ---------------------------------------------------------------------------
# Routes – Settings
# ---------------------------------------------------------------------------
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, user: User = Depends(require_user),
                         db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "settings.html", base_ctx(user, db, {"msg": None, "error": None}))


@app.post("/settings")
async def save_settings(request: Request, language: str = Form(...),
                        tips_public: str = Form("off"),
                        new_password: str = Form(""), confirm_password: str = Form(""),
                        user: User = Depends(require_user), db: Session = Depends(get_db)):
    lang = language if language in ("de", "en", "es") else "de"
    error = None
    msg = None

    if new_password:
        if new_password != confirm_password:
            error = t(lang, "password_mismatch")
        else:
            user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            msg = t(lang, "settings_saved")

    user.language = lang
    user.tips_public = (tips_public == "on")
    db.commit()
    if not msg and not error:
        msg = t(lang, "settings_saved")

    return templates.TemplateResponse(request, "settings.html", base_ctx(user, db, {
        "msg": msg, "error": error,
    }))


# ---------------------------------------------------------------------------
# Routes – Admin: Users
# ---------------------------------------------------------------------------
@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(require_admin)):
    users = db.query(User).order_by(User.username).all()
    return templates.TemplateResponse(request, "admin/users.html", base_ctx(user, db, {
        "users": users, "msg": None, "error": None,
    }))


@app.post("/admin/users/create")
async def create_user(request: Request, username: str = Form(...), password: str = Form(...),
                      role: str = Form("player"), language: str = Form("de"),
                      db: Session = Depends(get_db), user: User = Depends(require_admin)):
    users = db.query(User).order_by(User.username).all()
    lang = user.language

    if db.query(User).filter_by(username=username).first():
        return templates.TemplateResponse(request, "admin/users.html", base_ctx(user, db, {
            "users": users,
            "msg": None,
            "error": t(lang, "username_taken"),
        }))

    pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user = User(username=username, password_hash=pw, role=role, language=language)
    db.add(new_user)
    db.commit()
    users = db.query(User).order_by(User.username).all()
    return templates.TemplateResponse(request, "admin/users.html", base_ctx(user, db, {
        "users": users,
        "msg": t(lang, "user_created"),
        "error": None,
    }))


@app.post("/admin/users/{target_id}/delete")
async def delete_user(target_id: int, db: Session = Depends(get_db),
                      user: User = Depends(require_admin)):
    target = db.query(User).get(target_id)
    if target and target.id != user.id:
        db.delete(target)
        db.commit()
    return RedirectResponse("/admin/users", status_code=302)


@app.post("/admin/users/{target_id}/reset-password")
async def reset_password(target_id: int, new_password: str = Form(...),
                         db: Session = Depends(get_db), user: User = Depends(require_admin)):
    target = db.query(User).get(target_id)
    if target:
        target.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        db.commit()
    return RedirectResponse("/admin/users", status_code=302)


# ---------------------------------------------------------------------------
# Routes – Admin: Matches
# ---------------------------------------------------------------------------
@app.get("/admin/matches", response_class=HTMLResponse)
async def admin_matches(request: Request, db: Session = Depends(get_db),
                        user: User = Depends(require_admin)):
    # Nach Gruppe/Runde gruppiert, innerhalb der Runde chronologisch sortiert
    # (statt nach Anstoßzeit, da Gruppenspiele terminlich verschachtelt sind).
    matches = sorted(
        db.query(Match).all(),
        key=lambda m: (round_sort_key(m.round), m.kickoff_utc),
    )
    return templates.TemplateResponse(request, "admin/matches.html", base_ctx(user, db, {
        "matches": matches, "msg": None,
    }))


@app.post("/admin/matches/{match_id}/result")
async def set_result(match_id: int, score1: int = Form(...), score2: int = Form(...),
                     status: str = Form("finished"),
                     db: Session = Depends(get_db), user: User = Depends(require_admin)):
    match = db.query(Match).get(match_id)
    if match:
        match.score1 = score1
        match.score2 = score2
        match.status = status
        db.commit()
        # Recalculate points for this match
        for tip in db.query(Tip).filter_by(match_id=match_id).all():
            if status == "finished":
                tip.points = calc_points(tip.tip_score1, tip.tip_score2, score1, score2)
            else:
                tip.points = 0
        db.commit()
    return RedirectResponse("/admin/matches", status_code=302)


@app.post("/admin/matches/{match_id}/teams")
async def set_teams(match_id: int, team1: str = Form(...), team2: str = Form(...),
                    db: Session = Depends(get_db), user: User = Depends(require_admin)):
    match = db.query(Match).get(match_id)
    if match:
        match.team1 = team1
        match.team2 = team2
        db.commit()
    return RedirectResponse("/admin/matches", status_code=302)


@app.post("/admin/recalc")
async def admin_recalc(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    recalculate_all_points(db)
    return RedirectResponse("/admin/matches", status_code=302)


@app.post("/admin/matches/{match_id}/toggle-tips")
async def toggle_tips(match_id: int, db: Session = Depends(get_db),
                      user: User = Depends(require_admin)):
    match = db.query(Match).get(match_id)
    if match:
        match.tips_open = not match.tips_open
        db.commit()
    return RedirectResponse("/admin/matches", status_code=302)


@app.post("/admin/sync")
async def admin_sync(user: User = Depends(require_admin)):
    """Manueller API-Sync."""
    sync_and_recalc(SessionLocal, recalculate_all_points, get_api_token)
    return RedirectResponse("/admin/matches", status_code=302)


# ---------------------------------------------------------------------------
# Routes – Admin: Settings
# ---------------------------------------------------------------------------
def build_sondertipp_rows(db: Session):
    """Baut für alle User je eine Zeile für Weltmeister- und Torschützenkönig-Tipp,
    auch wenn noch kein Tipp abgegeben wurde (damit Admin ihn nachtragen kann)."""
    all_users = db.query(User).order_by(User.username).all()
    champion_by_user = {ct.user_id: ct for ct in db.query(ChampionTip).all()}
    scorer_by_user = {st.user_id: st for st in db.query(TopScorerTip).all()}
    champion_rows = [{"user": u, "tip": champion_by_user.get(u.id)} for u in all_users]
    scorer_rows = [{"user": u, "tip": scorer_by_user.get(u.id)} for u in all_users]
    return champion_rows, scorer_rows


@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db),
                         user: User = Depends(require_admin)):
    token = get_api_token(db)
    top_scorer = get_top_scorer(db)
    champion_rows, scorer_rows = build_sondertipp_rows(db)
    matches = db.query(Match).all()
    all_teams = sorted({t for m in matches for t in (m.team1, m.team2) if t != "TBD"})
    return templates.TemplateResponse(request, "admin/settings.html", base_ctx(user, db, {
        "api_token": token, "top_scorer": top_scorer,
        "scorer_rows": scorer_rows, "champion_rows": champion_rows,
        "all_teams": all_teams, "msg": None,
    }))


@app.post("/admin/settings")
async def save_admin_settings(request: Request, api_token: str = Form(""),
                               top_scorer: str = Form(""),
                               db: Session = Depends(get_db),
                               user: User = Depends(require_admin)):
    def upsert(key, val):
        s = db.query(Setting).filter_by(key=key).first()
        if s:
            s.value = val
        else:
            db.add(Setting(key=key, value=val))

    upsert("api_token", api_token.strip())
    upsert("top_scorer", top_scorer.strip())
    db.commit()
    if top_scorer.strip():
        award_scorer_points(db)
    champion_rows, scorer_rows = build_sondertipp_rows(db)
    matches = db.query(Match).all()
    all_teams = sorted({t for m in matches for t in (m.team1, m.team2) if t != "TBD"})
    return templates.TemplateResponse(request, "admin/settings.html", base_ctx(user, db, {
        "api_token": api_token.strip(),
        "top_scorer": top_scorer.strip(),
        "scorer_rows": scorer_rows,
        "champion_rows": champion_rows,
        "all_teams": all_teams,
        "msg": t(user.language, "settings_saved"),
    }))


# ---------------------------------------------------------------------------
# Startup + Scheduler
# ---------------------------------------------------------------------------
scheduler = BackgroundScheduler()


@app.on_event("startup")
async def startup():
    init_db()
    # Spiele beim Start aus der API laden
    sync_and_recalc(SessionLocal, recalculate_all_points, get_api_token)
    # Danach stündlich aktualisieren
    scheduler.add_job(
        sync_and_recalc,
        "interval",
        hours=1,
        args=[SessionLocal, recalculate_all_points, get_api_token],
        id="api_sync",
    )
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)
