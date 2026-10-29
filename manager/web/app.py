"""Alpha web local del Hockey Manager (Flask + Jinja).

La lógica sigue en manager/src. Esta capa solo orquesta GameState y MatchEngine.
"""

from __future__ import annotations

import html
import os
import random
import uuid
from datetime import date, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, Response, abort, flash, redirect, render_template, request, send_from_directory, session, url_for
from src.calendar import league_table
from src.cup import cup_next_user_fixture, cup_round_fixtures, cup_status_text
from src.daily import add_player_chat, next_match_date, simulate_days
from src.competitions import COMPETITIONS, competition, playable_competitions
from src.data_loader import load_clubs, load_teams
from src.international import load_all_teams
from src.ehl import ehl_next_date, ehl_status_text, simulate_ehl_round
from src.finance import financial_summary
from src.market import (
    STAFF_LABELS,
    accept_incoming_offer,
    asking_price,
    fire_staff,
    generate_incoming_offers,
    hire_staff,
    make_transfer_offer,
    market_players,
    market_window,
    market_window_text,
    reject_incoming_offer,
    renew_contract,
    scout_range,
    staff_candidates,
)
from src.models import FORMATION_SLOTS
from src.news import news_feed
from src.persistence import backfill_state, list_saves, load_game, save_game
from src.press import answer_press, mark_press_done, press_context, press_questions
from src.ratings import league_label, scout_stars, stars_bar, stars_text, tier
from src.runtime import project_root
from src.season import (
    advance_to_next_season,
    ensure_week_training,
    finish_live_round,
    make_lineup,
    new_game,
    play_round,
    prepare_live_round,
    season_summary,
    simulate_cup_remaining,
    simulate_cup_round,
)
from src.training import (
    DAYS,
    PLAN_PRESETS,
    SESSION_ORDER,
    SESSION_TYPES,
    apply_training_plan,
    auto_plan,
    format_plan,
    plan_name,
)
from src.youth import CATEGORY_AGES, CATEGORY_LABELS, YOUTH_CATEGORIES, promote_youth, release_youth

PROJECT_ROOT = project_root()
BASE = PROJECT_ROOT / "manager"
PHOTOS = PROJECT_ROOT / "jugadores"
WEB_DB = Path(os.environ.get("HOCKEY_WEB_DB", BASE / "saves" / "web.db"))
DESKTOP_MODE = os.environ.get("HOCKEY_DESKTOP") == "1"
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("HOCKEY_WEB_SECRET", "hockey-manager-alpha-local")

GAMES: dict[str, object] = {}
LIVE: dict[str, object] = {}


def get_state():
    gid = session.get("game_id")
    if not gid:
        return None
    state = GAMES.get(gid)
    if state is None:
        name = session.get("save_name")
        if not name:
            return None
        try:
            state = load_game(name, WEB_DB)
        except Exception:
            return None
        GAMES[gid] = state
    backfill_state(state)
    return state


def save_state(state):
    name = session.get("save_name")
    if not name:
        name = f"web-{session.get('game_id', uuid.uuid4().hex)}"
        session["save_name"] = name
    save_game(state, name, WEB_DB)


DEFAULT_UI_PREFS = {"text_size": "normal", "compact": False, "confirm_exit": True}


def ui_prefs():
    stored = session.get("ui_prefs", {})
    return {**DEFAULT_UI_PREFS, **stored}


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if get_state() is None:
            flash("Primero crea o carga una partida.", "warning")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)

    return wrapper


LINE_LAYOUTS = {
    "4-3-3": [1, 4, 3, 3],
    "3-4-3": [1, 3, 4, 3],
    "3-3-3-1": [1, 3, 4, 1, 2],
    "4-4-2": [1, 4, 4, 2],
    "5-3-2": [1, 5, 3, 2],
    "3-2-1-4": [1, 3, 2, 1, 4],
}
ROW_LABELS = {
    4: ["Portería", "Defensa", "Medio", "Ataque"],
    5: ["Portería", "Defensa", "Medio", "Mediapunta", "Ataque"],
}
SLOT_GROUP = {"POR": "Portero", "CEN": "Defensa", "LAT": "Defensa", "MED": "Medio", "DEL": "Delantero"}


def lineup_rows(team, line):
    slots = FORMATION_SLOTS.get(team.tactics.formation, FORMATION_SLOTS["4-3-3"])
    counts = LINE_LAYOUTS.get(team.tactics.formation, [1, 4, 3, 3])
    labels = ROW_LABELS.get(len(counts), ROW_LABELS[4])
    rows = []
    cursor = 0
    for count, label in zip(counts, labels):
        row = []
        for _ in range(count):
            if cursor >= len(slots):
                break
            code = slots[cursor]
            player = line[cursor] if cursor < len(line) else None
            row.append(
                {
                    "index": cursor,
                    "code": code,
                    "player": player,
                    "group": SLOT_GROUP.get(code, ""),
                    "mismatch": bool(player and player.position_group != SLOT_GROUP.get(code, player.position_group)),
                }
            )
            cursor += 1
        rows.append({"label": label, "slots": row})
    return rows


def team_form(state, team_id):
    played = [f for f in state.fixtures if f.phase == "regular" and f.played and team_id in (f.home_id, f.away_id)]
    played.sort(key=lambda f: f.round)
    out = []
    for f in played[-5:]:
        gf = f.home_goals if f.home_id == team_id else f.away_goals
        ga = f.away_goals if f.home_id == team_id else f.home_goals
        out.append("V" if gf > ga else ("E" if gf == ga else "D"))
    return " ".join(out) if out else "—"


def state_context(state):
    team = state.user_team
    table = state.table()
    pos = next((i for i, t in enumerate(table, 1) if t.id == team.id), 0)
    return {
        "state": state,
        "team": team,
        "table": table,
        "positions": {t.id: i for i, t in enumerate(table, 1)},
        "position": pos,
        "competition": state.competition,
        "competition_name": competition(state.competition).name,
        "competition_short": competition(state.competition).short_name,
        "competition_country": competition(state.competition).country,
        "finance": financial_summary(team),
        "cup_status": cup_status_text(state),
        "market_status": market_window_text(state),
        "next_fixture": state.next_user_fixture(),
        "ehl_next": ehl_next_date(state),
        "ehl_status": ehl_status_text(state),
        "live_active": session.get("game_id") in LIVE,
    }


def fixture_label(fixture):
    if fixture is None:
        return "Sin partido"
    labels = {
        "cup_qf": "Copa del Rey · Cuartos",
        "cup_sf": "Copa del Rey · Semifinal",
        "cup_final": "Copa del Rey · Final",
        "cup_third": "Copa del Rey · Tercer puesto",
        "promotion_group": "Fase de ascenso · Grupos",
        "promotion_final": "Fase de ascenso · Fase final",
    }
    return labels.get(fixture.phase, f"Jornada {fixture.round}")


def fmt_money(n):
    return f"{int(round(n or 0)):,}".replace(",", ".") + " €"


def fmt_date(iso):
    try:
        d = date.fromisoformat(iso)
        return d.strftime("%d/%m/%Y")
    except Exception:
        return iso


app.jinja_env.filters["money"] = fmt_money
app.jinja_env.filters["fdate"] = fmt_date
app.jinja_env.globals["fixture_label"] = fixture_label
app.jinja_env.globals["stars_text"] = stars_text
app.jinja_env.globals["stars_bar"] = stars_bar
app.jinja_env.globals["player_tier"] = tier
app.jinja_env.globals["league_label"] = league_label
app.jinja_env.globals["scout_stars"] = scout_stars


def photo_src(player):
    if getattr(player, "photo", ""):
        return url_for("player_photo", filename=player.photo)
    if getattr(player, "photo_remote", ""):
        return player.photo_remote
    return url_for("static", filename="avatar.svg")


def initials(name):
    parts = [p for p in str(name or "").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


def crest_src(team):
    tid = getattr(team, "id", team)
    for ext in ("png", "webp", "jpg", "jpeg", "svg"):
        if (BASE / "web" / "static" / "crests" / f"{tid}.{ext}").exists():
            return url_for("static", filename=f"crests/{tid}.{ext}")
    return url_for("team_crest", team_id=tid)


app.jinja_env.globals["photo_src"] = photo_src
app.jinja_env.globals["crest_src"] = crest_src
app.jinja_env.globals["initials"] = initials


@app.route("/crest/<team_id>.svg")
def team_crest(team_id):
    state = get_state()
    team = state.teams.get(team_id) if state else None
    if team is not None:
        name = team.name
    else:
        from src.international import club_catalog

        club = club_catalog().get(team_id)
        if not club:
            abort(404)
        name = club["name"]
    letters = initials(name)
    palette = [("#1b4f9c", "#ffffff"), ("#b3202a", "#ffffff"), ("#1f7a4d", "#ffffff"), ("#f0a31a", "#111827"), ("#3c2a6d", "#ffffff")]
    idx = sum(ord(c) for c in team_id) % len(palette)
    bg, fg = palette[idx]
    safe_name = html.escape(name)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96"><rect width="96" height="96" rx="14" fill="{bg}"/><path d="M12 18h72v42c0 18-36 26-36 26S12 78 12 60z" fill="none" stroke="{fg}" stroke-width="4" opacity=".75"/><text x="48" y="58" text-anchor="middle" font-family="Arial,sans-serif" font-size="28" font-weight="700" fill="{fg}">{letters}</text><title>{safe_name}</title></svg>'''
    return Response(svg, mimetype="image/svg+xml")


LEGACY_UI_REDIRECTS = {
    "/main-menu": "/app/",
    "/new": "/app/new",
    "/load": "/app/load",
    "/options": "/app/options",
    "/dashboard": "/app/game",
    "/squad": "/app/game/squad",
    "/tactics": "/app/game/tactics",
    "/training": "/app/game/training",
    "/market": "/app/game/market",
    "/market/offers": "/app/game/market/offers",
    "/market/renew": "/app/game/market/renew",
    "/staff": "/app/game/staff",
    "/youth": "/app/game/youth",
    "/press": "/app/game/press",
    "/cup": "/app/game/cup",
    "/ehl": "/app/game/ehl",
    "/table": "/app/game/table",
    "/match": "/app/game/match",
    "/match/live": "/app/game/live",
    "/match/report": "/app/game/report",
    "/season/end": "/app/game/season-end",
    "/chat": "/app/game/chat",
    "/news": "/app/game/news",
}


@app.before_request
def legacy_browser_redirect():
    """Send browser navigations to the React app, while keeping old API-style
    test/legacy endpoints available for compatibility."""
    if request.method != "GET" or not request.path.startswith("/"):
        return None
    accept = request.headers.get("Accept", "")
    if not accept.startswith("text/html"):
        return None
    path = request.path
    if path in ("/", "/app") or path.startswith(("/app/", "/api/", "/static/", "/photo/", "/crest/")):
        return None
    target = LEGACY_UI_REDIRECTS.get(path)
    if target:
        return redirect(target)
    for prefix, new_prefix in (("/player/", "/app/game/player/"), ("/team/", "/app/game/team/"), ("/market/player/", "/app/game/market/player/")):
        if path.startswith(prefix):
            return redirect(new_prefix + path[len(prefix):])
    return None


@app.context_processor
def inject_globals():
    state = get_state()
    return {
        "current_state": state,
        "current_team": state.user_team if state else None,
        "current_table": state.table() if state else [],
        "ui_prefs": ui_prefs(),
        "live_active": bool(state and session.get("game_id") in LIVE),
        "desktop_mode": DESKTOP_MODE,
    }


@app.route("/photo/<path:filename>")
def player_photo(filename):
    try:
        return send_from_directory(PHOTOS, filename)
    except Exception:
        abort(404)


@app.route("/main-menu")
def main_menu():
    state = get_state()
    return render_template(
        "main_menu.html",
        saves=list_saves(WEB_DB)[:3],
        live_active=bool(state and session.get("game_id") in LIVE),
    )


@app.route("/exit-game", methods=["POST"])
def exit_game():
    state = get_state()
    if state:
        try:
            save_state(state)
        except Exception:
            pass
    gid = session.pop("game_id", None)
    session.pop("save_name", None)
    if gid:
        LIVE.pop(gid, None)
    flash("Partida guardada. Has vuelto al menú principal.", "success")
    return redirect(url_for("main_menu"))


@app.route("/options", methods=["GET", "POST"])
def options():
    if request.method == "POST" and request.form.get("reset"):
        session.pop("ui_prefs", None)
        flash("Opciones restablecidas.", "success")
        return redirect(url_for("options"))
    if request.method == "POST":
        session["ui_prefs"] = {
            "text_size": "large" if request.form.get("text_size") == "large" else "normal",
            "compact": bool(request.form.get("compact")),
            "confirm_exit": bool(request.form.get("confirm_exit")),
        }
        flash("Opciones guardadas.", "success")
        return redirect(url_for("options"))
    return render_template("options.html")


@app.route("/desktop/quit", methods=["POST"])
def desktop_quit():
    if not DESKTOP_MODE:
        abort(404)
    os._exit(0)


@app.route("/app")
@app.route("/app/")
@app.route("/app/<path:path>")
def react_app(path=""):
    """Serve the React SPA. Vite builds into web/static/react."""
    index = BASE / "web" / "static" / "react" / "index.html"
    if not index.exists():
        return (
            "La interfaz React todavía no está compilada. "
            "Ejecuta `cd manager/web/frontend && npm install && npm run build`.",
            503,
        )
    return send_from_directory(index.parent, "index.html")


@app.route("/")
def index():
    if (BASE / "web" / "static" / "react" / "index.html").exists():
        return redirect(url_for("react_app"))
    state = get_state()
    if state:
        if state.phase == "season_end":
            return redirect(url_for("season_end"))
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/new", methods=["GET", "POST"])
def new_game_page():
    teams, clubs, _ = load_all_teams()
    order = {c.code: i for i, c in enumerate(COMPETITIONS.values())}
    clubs_list = sorted(
        [t for t in teams.values() if t.league in order and t.league != "1A"],
        key=lambda t: (order.get(t.league, 99), t.name),
    )
    league_groups = []
    for meta in playable_competitions():
        group = [t for t in clubs_list if t.league == meta.code]
        if group:
            league_groups.append({"meta": meta, "teams": group})

    def difficulty(expectation):
        e = (expectation or "").lower()
        if "título" in e or "final four" in e:
            return "Muy alta"
        if "top 4" in e:
            return "Alta"
        if "top 6" in e or "consolidar" in e:
            return "Media"
        if "permanencia" in e or "salvación" in e:
            return "Baja"
        if "ascenso" in e:
            return "Alta"
        return "Media"

    club_cards = []
    for t in clubs_list:
        c = clubs.get(t.id, {})
        st = c.get("stadium", {})
        club_cards.append(
            {
                "team": t,
                "stadium": st.get("name", t.stadium_name),
                "expectation": t.board_expectation,
                "difficulty": difficulty(t.board_expectation),
            }
        )
    if request.method == "POST":
        club_id = request.form.get("club_id", "")
        manager = request.form.get("manager", "Entrenador").strip() or "Entrenador"
        seed_raw = request.form.get("seed", "").strip()
        seed = int(seed_raw) if seed_raw.isdigit() else None
        if club_id not in teams or teams[club_id].league == "1A" or teams[club_id].league not in COMPETITIONS:
            flash("Elige un club de una liga jugable.", "danger")
            return redirect(url_for("new_game_page"))
        state = new_game(club_id, manager, seed)
        old_gid = session.get("game_id")
        if old_gid:
            LIVE.pop(old_gid, None)
        gid = uuid.uuid4().hex
        GAMES[gid] = state
        session["game_id"] = gid
        session["save_name"] = f"{state.user_team.name} · {state.season} · {gid[:4]}"
        save_state(state)
        flash(f"Partida creada con {state.user_team.name}.", "success")
        return redirect(url_for("dashboard"))
    return render_template(
        "new_game.html", clubs=clubs_list, club_cards=club_cards, clubs_by_id=clubs, league_groups=league_groups
    )


@app.route("/load", methods=["GET", "POST"])
def load_page():
    saves = list_saves(WEB_DB)
    if request.method == "POST":
        name = request.form.get("name", "")
        try:
            state = load_game(name, WEB_DB)
        except Exception as exc:
            flash(f"No se pudo cargar: {exc}", "danger")
            return redirect(url_for("load_page"))
        old_gid = session.get("game_id")
        if old_gid:
            LIVE.pop(old_gid, None)
        gid = uuid.uuid4().hex
        GAMES[gid] = state
        session["game_id"] = gid
        session["save_name"] = name
        flash(f"Partida cargada: {state.user_team.name}.", "success")
        return redirect(url_for("season_end") if state.phase == "season_end" else url_for("dashboard"))
    return render_template("load.html", saves=saves)


@app.route("/save", methods=["POST"])
@login_required
def save_page():
    state = get_state()
    name = request.form.get("name", "").strip()
    if name:
        session["save_name"] = name
    save_state(state)
    flash("Partida guardada.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    state = get_state()
    if state.phase == "season_end":
        return redirect(url_for("season_end"))
    ctx = state_context(state)
    ctx["inbox"] = state.inbox[-4:]
    ctx["news"] = news_feed(state, 4)
    ctx["key_players"] = sorted(state.user_team.players, key=lambda p: p.overall, reverse=True)[:3]
    ctx["live_ctx"] = LIVE.get(session.get("game_id"))
    ctx["daily_events"] = list(reversed(state.daily_events[-6:]))
    ctx["pending_chats"] = [m for m in state.chat_messages if not m.get("answered")][-2:]
    ctx["next_match_date"] = next_match_date(state)
    return render_template("dashboard.html", **ctx)


@app.route("/simulate", methods=["POST"])
@login_required
def simulate_calendar():
    state = get_state()
    if session.get("game_id") in LIVE:
        flash("Termina primero el partido en directo.", "warning")
        return redirect(url_for("match_live"))
    mode = request.form.get("mode", "day")
    target = request.form.get("target_date", "").strip()
    if mode == "next_match":
        match_day = next_match_date(state)
        if not match_day:
            flash("No queda ningún partido pendiente.", "warning")
            return redirect(url_for("dashboard"))
        result = simulate_days(state, target_date=match_day, stop_at_match=True)
    elif mode == "date":
        if not target:
            flash("Elige una fecha.", "warning")
            return redirect(url_for("dashboard"))
        try:
            result = simulate_days(state, target_date=target, stop_at_match=True)
        except ValueError:
            flash("Fecha no válida.", "danger")
            return redirect(url_for("dashboard"))
    else:
        result = simulate_days(state, days=1, stop_at_match=True)
    if not result.get("ok"):
        flash(result.get("message", "No se pudo avanzar."), "warning")
        return redirect(url_for("dashboard"))
    save_state(state)
    if result.get("stopped_at_match"):
        flash(f"Hoy hay partido: {state.date}. Prepara el once y decide cómo jugarlo.", "warning")
        return redirect(url_for("match_page"))
    flash(f"Calendario avanzado {result['days']} día(s). Hoy es {state.date}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/chat")
@login_required
def chat():
    state = get_state()
    ctx = state_context(state)
    ctx["messages"] = list(reversed(state.chat_messages[-30:]))
    ctx["players_by_id"] = {p.id: p for p in state.user_team.players}
    return render_template("chat.html", **ctx)


@app.route("/chat/<message_id>", methods=["POST"])
@login_required
def chat_answer(message_id):
    state = get_state()
    message = next((m for m in state.chat_messages if m.get("id") == message_id), None)
    if not message or message.get("answered"):
        flash("Esa conversación ya no está disponible.", "warning")
        return redirect(url_for("chat"))
    try:
        choice = int(request.form.get("option", "0"))
    except ValueError:
        choice = 0
    options = message.get("options", [])
    if not options:
        flash("La conversación no tiene opciones.", "danger")
        return redirect(url_for("chat"))
    option = options[max(0, min(choice, len(options) - 1))]
    player = next((p for p in state.user_team.players if p.id == message.get("player_id")), None)
    effects = option.get("effects", {})
    if player:
        if "morale" in effects:
            player.morale = max(1, min(20, player.morale + int(effects["morale"])))
        if "form" in effects:
            player.form = max(1.0, min(10.0, player.form + float(effects["form"])))
        if "relationship" in effects:
            player.relationship = max(0, min(100, player.relationship + int(effects["relationship"])))
        if "suspension" in effects:
            player.suspension = max(0, player.suspension + int(effects["suspension"]))
            if player.suspension:
                player.absence_note = effects.get("note", player.absence_note or "Sanción")
        if "absence_note" in effects:
            player.absence_note = effects["absence_note"]
    if "cohesion" in effects:
        state.user_team.cohesion = max(1, min(20, state.user_team.cohesion + int(effects["cohesion"])))
    if "manager_rating" in effects:
        state.user_team.manager_rating = max(
            0, min(100, state.user_team.manager_rating + int(effects["manager_rating"]))
        )
    if "board" in effects:
        state.user_team.board_confidence = max(0, min(100, state.user_team.board_confidence + int(effects["board"])))
    if "fan" in effects:
        state.user_team.fan_confidence = max(0, min(100, state.user_team.fan_confidence + int(effects["fan"])))
    if "fine" in effects:
        state.user_team.budget -= int(effects["fine"])
    message["answered"] = True
    message["answer"] = option.get("label", "")
    message["response"] = option.get("response", "")
    save_state(state)
    flash("Conversación registrada.", "success")
    return redirect(url_for("chat"))


@app.route("/chat/new", methods=["POST"])
@login_required
def chat_new():
    state = get_state()
    rng = random.Random(state.seed + len(state.chat_messages) * 31)
    player = rng.choice(state.user_team.available_players or state.user_team.players)
    add_player_chat(state, date.fromisoformat(state.date), player, kind="mood")
    save_state(state)
    flash("Has abierto una conversación con el vestuario.", "success")
    return redirect(url_for("chat"))


@app.route("/news")
@login_required
def news():
    state = get_state()
    ctx = state_context(state)
    ctx["news"] = news_feed(state, 12)
    ctx["daily_events"] = list(reversed(state.daily_events[-20:]))
    return render_template("news.html", **ctx)


@app.route("/squad")
@login_required
def squad():
    ctx = state_context(get_state())
    ctx["players"] = sorted(ctx["team"].players, key=lambda p: (p.subposition, -p.overall))
    groups = []
    for group in ("Portero", "Defensa", "Medio", "Delantero"):
        members = [p for p in ctx["players"] if p.position_group == group]
        if members:
            groups.append((group, members))
    ctx["groups"] = groups
    return render_template("squad.html", **ctx)


@app.route("/player/<player_id>")
@login_required
def player_detail(player_id):
    state = get_state()
    owner_team = next((t for t in state.teams.values() if any(p.id == player_id for p in t.players)), None)
    player = next((p for p in owner_team.players if p.id == player_id), None) if owner_team else None
    if not player:
        player = next((p for p in state.free_agents if p.id == player_id), None)
    if not player:
        flash("Jugador no encontrado.", "danger")
        return redirect(url_for("squad"))
    ctx = state_context(state)
    ctx["player"] = player
    ctx["owner_team"] = owner_team
    ctx["owner_name"] = owner_team.name if owner_team else "Agente libre"
    ctx["back_url"] = url_for("team_detail", team_id=owner_team.id) if owner_team else url_for("market")
    return render_template("player.html", **ctx)


@app.route("/team/<team_id>")
@login_required
def team_detail(team_id):
    state = get_state()
    selected = state.teams.get(team_id)
    if not selected:
        flash("Equipo no encontrado.", "danger")
        return redirect(url_for("table"))
    clubs, _ = load_clubs()
    from src.international import club_catalog

    clubs.update(club_catalog())
    club = clubs.get(team_id, {})
    if state.competition == selected.league:
        table = state.table()
    else:
        table = sorted(
            [t for t in state.teams.values() if t.league == selected.league],
            key=lambda t: (-t.points, -(t.goals_for - t.goals_against), -t.goals_for, t.name),
        )
    position = next((i for i, t in enumerate(table, 1) if t.id == selected.id), 0)
    team_group = ""
    if selected.league == "DHB" and state.dhb_groups:
        team_group = next((g for g, ids in state.dhb_groups.items() if selected.id in ids), "")
    fixtures = sorted(
        [f for f in state.fixtures if selected.id in (f.home_id, f.away_id)], key=lambda f: (f.date, f.round)
    )
    played = [f for f in fixtures if f.played][-5:]
    upcoming = [f for f in fixtures if not f.played][:5]
    probable_line, probable_bench = selected.auto_lineup()
    is_user_team = selected.id == state.club_id
    team_staff = [member for member in selected.staff if member.role != "head_coach"]
    team_coach = next((member for member in selected.staff if member.role == "head_coach"), None)
    ctx = state_context(state)
    ctx.update(
        {
            "selected_team": selected,
            "club": club,
            "team_position": position,
            "team_group": team_group,
            "team_table": table,
            "team_fixtures": fixtures,
            "team_played": played,
            "team_upcoming": upcoming,
            "probable_line": probable_line,
            "probable_bench": probable_bench,
            "probable_rows": lineup_rows(selected, probable_line),
            "probable_formation": selected.tactics.formation,
            "team_players": sorted(selected.players, key=lambda p: (p.position_group, -p.overall)),
            "team_staff": team_staff,
            "team_coach": team_coach,
            "is_user_team": is_user_team,
            "staff_labels": STAFF_LABELS,
        }
    )
    return render_template("team.html", **ctx)


@app.route("/tactics", methods=["GET", "POST"])
@login_required
def tactics():
    state = get_state()
    team = state.user_team
    if request.method == "POST":
        old_formation = team.tactics.formation
        for field in ("formation", "mentality", "press", "block", "width", "tempo", "passing", "pc_routine"):
            value = request.form.get(field)
            if value:
                setattr(team.tactics, field, value)
        if team.tactics.formation != old_formation:
            state.manual_lineup = []
            flash("Formación cambiada. Once autoalineado.", "success")
        elif request.form.get("auto"):
            state.manual_lineup = []
            flash("Autoalineación activada.", "success")
        else:
            slots = FORMATION_SLOTS.get(team.tactics.formation, FORMATION_SLOTS["4-3-3"])
            selected = [request.form.get(f"slot_{i}", "") for i in range(len(slots))]
            selected = [x for x in selected if x]
            if len(selected) == 11 and len(set(selected)) == 11:
                state.manual_lineup = selected
                flash("Once guardado.", "success")
            else:
                flash("El once debe tener 11 jugadores distintos. Se mantiene el anterior.", "danger")
        save_state(state)
        return redirect(url_for("tactics"))
    ctx = state_context(state)
    line, bench = make_lineup(team, state.manual_lineup or None)
    slots = FORMATION_SLOTS.get(team.tactics.formation, FORMATION_SLOTS["4-3-3"])
    slot_options = []
    for i, slot in enumerate(slots):
        candidates = sorted(team.available_players, key=lambda p: p.selection_score(slot), reverse=True)[:14]
        if i < len(line) and line[i] not in candidates:
            candidates.append(line[i])
        slot_options.append(candidates)
    slot_rows = lineup_rows(team, line)
    ctx.update(
        {
            "line": line,
            "bench": bench,
            "slots": slots,
            "slot_rows": slot_rows,
            "available": sorted(team.available_players, key=lambda p: (p.subposition, -p.overall)),
            "slot_options": slot_options,
            "formations": list(FORMATION_SLOTS),
            "selected": set(state.manual_lineup),
        }
    )
    return render_template("tactics.html", **ctx)


@app.route("/training", methods=["GET", "POST"])
@login_required
def training():
    state = get_state()
    team = state.user_team
    if request.method == "POST" and not state.week_trained:
        action = request.form.get("action", "auto")
        if action == "recovery":
            plan = list(PLAN_PRESETS["recuperacion"])
            delegated = False
        elif action == "edit":
            plan = [request.form.get(f"session{i}", "recuperacion") for i in range(5)]
            plan = [p if p in SESSION_TYPES else "recuperacion" for p in plan]
            delegated = False
        else:
            plan = auto_plan(team, _opponent(state), random.Random(state.seed + state.round * 53 + 11))
            delegated = True
        report = apply_training_plan(
            team, plan, _opponent(state), random.Random(state.seed + state.round * 53 + 17), delegated=delegated
        )
        state.weekly_plan = plan
        state.training_report = report
        state.week_trained = True
        save_state(state)
        flash("Entrenamiento semanal aplicado.", "success")
        return redirect(url_for("training"))
    ctx = state_context(state)
    default_plan = auto_plan(team, _opponent(state), random.Random(state.seed + state.round * 53 + 11))
    ctx.update(
        {
            "sessions": SESSION_TYPES,
            "session_order": SESSION_ORDER,
            "days": DAYS,
            "default_plan": default_plan,
            "plan_name": plan_name,
            "opponent": _opponent(state),
        }
    )
    return render_template("training.html", **ctx)


def _opponent(state):
    fx = state.next_user_fixture()
    if not fx:
        return None
    oid = fx.away_id if fx.home_id == state.club_id else fx.home_id
    return state.teams.get(oid)


@app.route("/market")
@login_required
def market():
    state = get_state()
    ctx = state_context(state)
    raw_max = request.args.get("max_value", "").strip()
    max_value = int(raw_max) if raw_max.isdigit() else None
    position = request.args.get("position", "")
    club_id = request.args.get("club_id", "")
    query = request.args.get("q", "").strip()
    players = market_players(state, limit=2000, max_value=max_value, position=position or None)
    owners = {p.id: t.name for t in state.teams.values() for p in t.players}
    owner_teams = {p.id: t for t in state.teams.values() for p in t.players}
    for p in state.free_agents:
        owners[p.id] = "Agente libre"
    if club_id:
        players = [p for p in players if owner_teams.get(p.id) and owner_teams[p.id].id == club_id]
    else:
        players = players[:200]
    if query:
        needle = query.lower()
        players = [
            p
            for p in players
            if needle in p.name.lower() or needle in p.archetype.lower() or needle in owners.get(p.id, "").lower()
        ]
    all_teams = sorted(
        [t for t in state.teams.values() if t.league in ("DHA", "DHB") or t.league == state.competition],
        key=lambda t: (t.league, t.name),
    )
    ctx.update(
        {
            "players": players,
            "max_value": max_value,
            "position": position,
            "query": query,
            "club_id": club_id,
            "all_teams": all_teams,
            "asking_price": asking_price,
            "scout_range": scout_range,
            "window": market_window(state),
            "offers": state.transfer_offers,
            "owners": owners,
            "owner_teams": owner_teams,
        }
    )
    return render_template("market.html", **ctx)


@app.route("/market/player/<player_id>", methods=["GET", "POST"])
@login_required
def market_player(player_id):
    state = get_state()
    player = next((p for p in state.user_team.players if p.id == player_id), None)
    if player:
        flash("Ese jugador ya es tuyo.", "warning")
        return redirect(url_for("market"))
    player = next((p for t in state.teams.values() for p in t.players if p.id == player_id), None)
    if not player:
        player = next((p for p in state.free_agents if p.id == player_id), None)
    if not player:
        flash("Jugador no encontrado.", "danger")
        return redirect(url_for("market"))
    if request.method == "POST":
        fee = int(request.form.get("fee", 0) or 0)
        salary = int(request.form.get("salary", 0) or 0)
        years = int(request.form.get("years", 3) or 3)
        result = make_transfer_offer(state, player.id, fee, salary, years)
        flash(result["message"], "success" if result.get("ok") else "danger")
        if result.get("ok"):
            save_state(state)
        return redirect(url_for("market"))
    ctx = state_context(state)
    owner_team = next((t for t in state.teams.values() if any(p.id == player.id for p in t.players)), None)
    owner = owner_team.name if owner_team else "Agente libre"
    scout = scout_range(player, state.user_team.staff_rating("scout"))
    try:
        low, high = [int(part) for part in scout.split("-")]
    except ValueError:
        low, high = int(player.overall), int(player.overall)
    ctx.update(
        {
            "player": player,
            "owner": owner,
            "owner_team": owner_team,
            "asking": asking_price(player),
            "scout": scout,
            "scout_star_range": scout_stars(low, high, player.league),
            "window": market_window(state),
        }
    )
    return render_template("market_player.html", **ctx)


@app.route("/market/offers", methods=["GET", "POST"])
@login_required
def market_offers():
    state = get_state()
    offers = generate_incoming_offers(state)
    if request.method == "POST":
        offer_id = request.form.get("offer_id", "")
        action = request.form.get("action", "")
        if action == "accept":
            result = accept_incoming_offer(state, offer_id)
            flash(result["message"], "success" if result.get("ok") else "danger")
        else:
            reject_incoming_offer(state, offer_id)
            flash("Oferta rechazada.", "warning")
        save_state(state)
        return redirect(url_for("market_offers"))
    ctx = state_context(state)
    ctx["offers"] = offers
    return render_template("market_offers.html", **ctx)


@app.route("/market/renew")
@login_required
def market_renew():
    ctx = state_context(get_state())
    ctx["players"] = sorted(ctx["team"].players, key=lambda p: (p.contract_until, -p.overall))
    return render_template("market_renew.html", **ctx)


@app.route("/market/renew/<player_id>", methods=["POST"])
@login_required
def market_renew_player(player_id):
    state = get_state()
    salary = int(request.form.get("salary", 0) or 0)
    years = int(request.form.get("years", 3) or 3)
    result = renew_contract(state, player_id, salary, years)
    flash(result["message"], "success" if result.get("ok") else "danger")
    if result.get("ok"):
        save_state(state)
    return redirect(url_for("market_renew"))


@app.route("/staff")
@login_required
def staff():
    state = get_state()
    ctx = state_context(state)
    ctx["staff_labels"] = STAFF_LABELS
    hireable = (
        "assistant",
        "fitness_coach",
        "gk_coach",
        "performance_analyst",
        "scout",
        "physio",
        "technical_director",
    )
    ctx["free_roles"] = [r for r in hireable if not any(m.role == r for m in state.user_team.staff)]
    return render_template("staff.html", **ctx)


@app.route("/staff/hire/<role>", methods=["GET", "POST"])
@login_required
def staff_hire(role):
    state = get_state()
    if role not in STAFF_LABELS:
        flash("Rol no válido.", "danger")
        return redirect(url_for("staff"))
    if any(m.role == role for m in state.user_team.staff):
        flash("Ese rol ya está cubierto.", "warning")
        return redirect(url_for("staff"))
    rng = random.Random(state.seed * 1000 + state.round * 61 + len(state.user_team.staff))
    candidates = staff_candidates(state.user_team, role, rng)
    if request.method == "POST":
        idx = int(request.form.get("candidate", -1))
        if 0 <= idx < len(candidates):
            result = hire_staff(state, candidates[idx])
            flash(result["message"], "success" if result.get("ok") else "danger")
            if result.get("ok"):
                save_state(state)
            return redirect(url_for("staff"))
    ctx = state_context(state)
    ctx.update({"role": role, "candidates": candidates, "staff_labels": STAFF_LABELS})
    return render_template("staff_hire.html", **ctx)


@app.route("/staff/fire/<role>", methods=["POST"])
@login_required
def staff_fire(role):
    state = get_state()
    result = fire_staff(state, role)
    flash(result["message"], "success" if result.get("ok") else "danger")
    if result.get("ok"):
        save_state(state)
    return redirect(url_for("staff"))


@app.route("/youth")
@login_required
def youth():
    state = get_state()
    ctx = state_context(state)
    groups = []
    for category in YOUTH_CATEGORIES:
        members = [p for p in state.user_team.youth if p.youth_category == category]
        if members:
            groups.append((category, CATEGORY_LABELS[category], members))
    ctx["youth_groups"] = groups
    ctx["category_ages"] = CATEGORY_AGES
    return render_template("youth.html", **ctx)


@app.route("/youth/promote/<player_id>", methods=["POST"])
@login_required
def youth_promote(player_id):
    state = get_state()
    ok, msg = promote_youth(state.user_team, player_id)
    flash(msg, "success" if ok else "danger")
    if ok:
        save_state(state)
    return redirect(url_for("youth"))


@app.route("/youth/release/<player_id>", methods=["POST"])
@login_required
def youth_release(player_id):
    state = get_state()
    ok, msg = release_youth(state.user_team, player_id)
    flash(msg, "success" if ok else "danger")
    if ok:
        save_state(state)
    return redirect(url_for("youth"))


@app.route("/press", methods=["GET", "POST"])
@login_required
def press():
    state = get_state()
    if request.method == "POST":
        questions = press_questions(state)
        for q in questions:
            raw = request.form.get(f"answer_{q['id']}", "0")
            try:
                idx = int(raw)
            except ValueError:
                idx = 0
            answer_press(state, q["id"], idx)
        mark_press_done(state)
        save_state(state)
        flash("Rueda de prensa completada.", "success")
        return redirect(url_for("press"))
    ctx = state_context(state)
    ctx["questions"] = press_questions(state)
    ctx["press_context"] = press_context(state)
    ctx["done"] = state.press_done_round == state.round
    return render_template("press.html", **ctx)


@app.route("/cup", methods=["GET", "POST"])
@login_required
def cup():
    state = get_state()
    if state.competition not in ("DHA", "DHB"):
        flash("La Copa del Rey solo existe en las ligas españolas.", "warning")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        action = request.form.get("action", "round")
        if action == "all":
            simulate_cup_remaining(state)
        else:
            simulate_cup_round(state, state.manual_lineup or None)
        save_state(state)
        flash("Copa actualizada.", "success")
        return redirect(url_for("cup"))
    ctx = state_context(state)
    ctx.update({"fixtures": cup_round_fixtures(state), "next_cup": cup_next_user_fixture(state)})
    return render_template("cup.html", **ctx)


@app.route("/ehl", methods=["GET", "POST"])
@login_required
def ehl():
    state = get_state()
    if state.competition not in ("DHA", "DHB"):
        flash("La EHL se gestiona desde las ligas europeas españolas.", "warning")
        return redirect(url_for("dashboard"))
    if request.method == "POST" and state.ehl.get("active"):
        simulate_ehl_round(state)
        save_state(state)
        flash("Ronda de EHL simulada.", "success")
        return redirect(url_for("ehl"))
    ctx = state_context(state)
    ctx["ehl"] = state.ehl
    return render_template("ehl.html", **ctx)


@app.route("/table")
@login_required
def table():
    ctx = state_context(get_state())
    regular = [f for f in ctx["state"].fixtures if f.phase == "regular"]
    ctx["fixtures"] = sorted(regular, key=lambda f: (f.round, f.date))
    return render_template("table.html", **ctx)


@app.route("/match")
@login_required
def match_page():
    state = get_state()
    gid = session.get("game_id")
    if gid in LIVE:
        return redirect(url_for("match_live"))
    fx = state.next_user_fixture()
    if not fx:
        return redirect(url_for("season_end") if state.phase == "season_end" else url_for("dashboard"))
    home, away = state.teams[fx.home_id], state.teams[fx.away_id]
    user = state.user_team
    line, bench = make_lineup(user, state.manual_lineup or None)
    travel = []
    if fx.away_id == user.id:
        from src.data_loader import load_clubs
        from src.logistics import travel_options

        _, cities = load_clubs()
        travel = travel_options(user, home, cities, squad_size=18)
    ctx = state_context(state)

    def top_scorer(t):
        return max(t.players, key=lambda p: (p.season_goals, p.overall), default=None)

    def absences(t):
        return [p for p in t.players if p.injury or p.suspension]

    ctx.update(
        {
            "fixture": fx,
            "is_cup": fx.phase.startswith("cup_"),
            "press_context": press_context(state),
            "home": home,
            "away": away,
            "line": line,
            "bench": bench,
            "travel": travel,
            "home_top": top_scorer(home),
            "away_top": top_scorer(away),
            "home_absences": absences(home),
            "away_absences": absences(away),
            "home_form": team_form(state, home.id),
            "away_form": team_form(state, away.id),
            "slot_rows": lineup_rows(user, line),
        }
    )
    return render_template("match_preview.html", **ctx)


@app.route("/match/quick", methods=["POST"])
@login_required
def match_quick():
    state = get_state()
    travel_id = request.form.get("travel") or None
    next_fixture = state.next_user_fixture()
    if next_fixture and next_fixture.phase.startswith("cup_"):
        payload = simulate_cup_round(state, state.manual_lineup or None)
        if payload:
            state.date = (date.fromisoformat(next_fixture.date) + timedelta(days=1)).isoformat()
            save_state(state)
            return redirect(url_for("match_report"))
        flash("No se pudo simular la eliminatoria de Copa.", "danger")
        return redirect(url_for("match_page"))
    payload = play_round(state, state.manual_lineup or None, travel_id)
    if not payload:
        flash("No se pudo simular el partido.", "danger")
        return redirect(url_for("dashboard"))
    save_state(state)
    return redirect(url_for("match_report"))


@app.route("/match/live/start", methods=["POST"])
@login_required
def match_live_start():
    state = get_state()
    gid = session.get("game_id")
    if gid in LIVE:
        return redirect(url_for("match_live"))
    next_fixture = state.next_user_fixture()
    if next_fixture and next_fixture.phase.startswith("cup_"):
        flash("La Copa del Rey se juega en simulación rápida en esta versión.", "warning")
        return redirect(url_for("match_page"))
    travel_id = request.form.get("travel") or None
    try:
        ctx = prepare_live_round(state, state.manual_lineup or None, travel_id)
    except Exception as exc:
        flash(f"No se pudo iniciar el directo: {exc}", "danger")
        return redirect(url_for("match_page"))
    LIVE[gid] = ctx
    return redirect(url_for("match_live"))


@app.route("/match/live")
@login_required
def match_live():
    state = get_state()
    gid = session.get("game_id")
    ctx = LIVE.get(gid)
    if not ctx:
        flash("No hay partido en directo.", "warning")
        return redirect(url_for("match_page"))
    engine = ctx.engine
    ctx_state = state_context(state)
    events = [
        e
        for e in engine.events
        if e.get("type")
        in (
            "goal",
            "pc",
            "stroke",
            "save",
            "card",
            "injury",
            "substitution",
            "chance",
            "circle_entry",
            "talk",
            "tactic",
        )
    ]
    ctx_state.update(
        {
            "engine": engine,
            "live": ctx,
            "fixture": ctx.fixture,
            "events": events[-40:],
            "user_side": ctx.user_side,
            "home": state.teams[ctx.fixture.home_id],
            "away": state.teams[ctx.fixture.away_id],
            "line": engine._lineup(ctx.user_side),
            "bench": engine._bench(ctx.user_side),
            "player_rows": engine.player_live_rows(ctx.user_side),
            "players_by_id": {p.id: p for p in state.user_team.players},
        }
    )
    return render_template("match_live.html", **ctx_state)


@app.route("/match/live/advance", methods=["POST"])
@login_required
def match_live_advance():
    state = get_state()
    gid = session.get("game_id")
    ctx = LIVE.get(gid)
    if not ctx:
        return redirect(url_for("match_page"))
    mode = request.form.get("mode", "quarter")
    engine = ctx.engine
    if mode == "moment":
        engine.advance_moment()
    elif mode == "rest":
        while not engine.finished:
            engine.advance_quarter()
    else:
        engine.advance_quarter()
    return redirect(url_for("match_live"))


@app.route("/match/live/tactics", methods=["POST"])
@login_required
def match_live_tactics():
    state = get_state()
    gid = session.get("game_id")
    ctx = LIVE.get(gid)
    if not ctx:
        return redirect(url_for("match_page"))
    for field in ("mentality", "press", "block", "width", "tempo", "passing", "pc_routine"):
        value = request.form.get(field)
        if value:
            setattr(state.user_team.tactics, field, value)
    return redirect(url_for("match_live"))


@app.route("/match/live/sub", methods=["POST"])
@login_required
def match_live_sub():
    state = get_state()
    gid = session.get("game_id")
    ctx = LIVE.get(gid)
    if not ctx:
        return redirect(url_for("match_page"))
    out_id = request.form.get("out_id", "")
    in_id = request.form.get("in_id", "")
    ok, msg = ctx.engine.manual_substitute(ctx.user_side, out_id, in_id, coaching=True)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("match_live"))


@app.route("/match/live/finish", methods=["POST"])
@login_required
def match_live_finish():
    state = get_state()
    gid = session.get("game_id")
    ctx = LIVE.get(gid)
    if not ctx:
        return redirect(url_for("match_page"))
    if not ctx.engine.finished:
        ctx.engine.simulate()
    payload = finish_live_round(state, ctx)
    LIVE.pop(gid, None)
    save_state(state)
    return redirect(url_for("match_report"))


@app.route("/match/report")
@login_required
def match_report():
    state = get_state()
    payload = state.last_result
    if not payload:
        flash("No hay parte de partido.", "warning")
        return redirect(url_for("dashboard"))
    ctx = state_context(state)
    ctx["p"] = payload
    return render_template("match_report.html", **ctx)


@app.route("/season/end")
@login_required
def season_end():
    state = get_state()
    if state.phase != "season_end":
        return redirect(url_for("dashboard"))
    ctx = state_context(state)
    ctx["summary"] = season_summary(state)
    return render_template("season_end.html", **ctx)


@app.route("/season/continue", methods=["POST"])
@login_required
def season_continue():
    state = get_state()
    if state.phase != "season_end":
        return redirect(url_for("dashboard"))
    advance_to_next_season(state)
    save_state(state)
    flash(f"Nueva temporada: {state.season} · {state.competition}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/new-season")
@login_required
def new_season_redirect():
    return redirect(url_for("season_end"))


from web.api import api as api_blueprint  # noqa: E402  (registered after all routes)

app.register_blueprint(api_blueprint)


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOCKEY_HOST", "127.0.0.1"),
        port=int(os.environ.get("HOCKEY_PORT", os.environ.get("PORT", "5000"))),
        debug=False,
        threaded=True,
        use_reloader=False,
    )
