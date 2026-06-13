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
from models import User, Match, Tip, Setting

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
    if score1 is None or score2 is None:
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


# ---------------------------------------------------------------------------
# Template helper
# ---------------------------------------------------------------------------
def base_ctx(user: User, extra: dict = None) -> dict:
    lang = user.language if user else "de"
    ctx = {
        "user": user,
        "lang": lang,
        "t": lambda key: t(lang, key),
        "now": datetime.utcnow(),
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

    # Group stage rounds for tab display
    def round_sort_key(r):
        if r.startswith("Gruppe "):
            return (0, r[-1])  # Gruppe A → (0, "A"), Gruppe B → (0, "B"), ...
        return ({
            "Runde der 32":     (1, ""),
            "Achtelfinale":     (2, ""),
            "Viertelfinale":    (3, ""),
            "Halbfinale":       (4, ""),
            "Spiel um Platz 3": (5, ""),
            "Finale":           (6, ""),
        }.get(r, (9, r)))

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

    return templates.TemplateResponse(request, "dashboard.html", base_ctx(user, {
        "matches": matches,
        "my_tips": my_tips,
        "rounds": rounds,
        "group_tables": group_tables,
        "now": now,
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
# Routes – Leaderboard
# ---------------------------------------------------------------------------
@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(require_user)):
    all_users = db.query(User).order_by(User.username).all()

    board = []
    for u in all_users:
        total = sum(tip.points for tip in u.tips)
        board.append({"user": u, "total": total})
    board.sort(key=lambda x: x["total"], reverse=True)

    # Add rank (shared rank for equal points)
    for i, entry in enumerate(board):
        if i == 0 or entry["total"] < board[i - 1]["total"]:
            entry["rank"] = i + 1
        else:
            entry["rank"] = board[i - 1]["rank"]

    return templates.TemplateResponse(request, "leaderboard.html", base_ctx(user, {
        "board": board,
    }))


# ---------------------------------------------------------------------------
# Routes – View other user's tips
# ---------------------------------------------------------------------------
@app.get("/tips/{target_user_id}", response_class=HTMLResponse)
async def view_user_tips(target_user_id: int, request: Request,
                         db: Session = Depends(get_db), user: User = Depends(require_user)):
    target = db.query(User).get(target_user_id)
    if not target:
        raise HTTPException(404)
    matches = db.query(Match).order_by(Match.kickoff_utc).all()
    their_tips = {tip.match_id: tip for tip in db.query(Tip).filter_by(user_id=target_user_id).all()}
    my_tips = {tip.match_id: tip for tip in db.query(Tip).filter_by(user_id=user.id).all()}
    now = datetime.utcnow()
    return templates.TemplateResponse(request, "other_tips.html", base_ctx(user, {
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
    return templates.TemplateResponse(request, "settings.html", base_ctx(user, {"msg": None, "error": None}))


@app.post("/settings")
async def save_settings(request: Request, language: str = Form(...),
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
    db.commit()
    if not msg and not error:
        msg = t(lang, "settings_saved")

    return templates.TemplateResponse(request, "settings.html", base_ctx(user, {
        "msg": msg, "error": error,
    }))


# ---------------------------------------------------------------------------
# Routes – Admin: Users
# ---------------------------------------------------------------------------
@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(require_admin)):
    users = db.query(User).order_by(User.username).all()
    return templates.TemplateResponse(request, "admin/users.html", base_ctx(user, {
        "users": users, "msg": None, "error": None,
    }))


@app.post("/admin/users/create")
async def create_user(request: Request, username: str = Form(...), password: str = Form(...),
                      role: str = Form("player"), language: str = Form("de"),
                      db: Session = Depends(get_db), user: User = Depends(require_admin)):
    users = db.query(User).order_by(User.username).all()
    lang = user.language

    if db.query(User).filter_by(username=username).first():
        return templates.TemplateResponse(request, "admin/users.html", base_ctx(user, {
            "users": users,
            "msg": None,
            "error": t(lang, "username_taken"),
        }))

    pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user = User(username=username, password_hash=pw, role=role, language=language)
    db.add(new_user)
    db.commit()
    users = db.query(User).order_by(User.username).all()
    return templates.TemplateResponse(request, "admin/users.html", base_ctx(user, {
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
    matches = db.query(Match).order_by(Match.match_number).all()
    return templates.TemplateResponse(request, "admin/matches.html", base_ctx(user, {
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
@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db),
                         user: User = Depends(require_admin)):
    token = get_api_token(db)
    return templates.TemplateResponse(request, "admin/settings.html", base_ctx(user, {
        "api_token": token, "msg": None,
    }))


@app.post("/admin/settings")
async def save_admin_settings(request: Request, api_token: str = Form(""),
                               db: Session = Depends(get_db),
                               user: User = Depends(require_admin)):
    setting = db.query(Setting).filter_by(key="api_token").first()
    if setting:
        setting.value = api_token.strip()
    else:
        db.add(Setting(key="api_token", value=api_token.strip()))
    db.commit()
    return templates.TemplateResponse(request, "admin/settings.html", base_ctx(user, {
        "api_token": api_token.strip(), "msg": "Einstellungen gespeichert.",
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
