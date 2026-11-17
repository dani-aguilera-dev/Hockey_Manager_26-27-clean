"""API de core."""

from __future__ import annotations

import uuid

from flask import Blueprint, request, session
from src.competitions import COMPETITIONS, competition
from src.daily import next_match_date, simulate_days
from src.data_validation import validate_state
from src.persistence import delete_save as delete_saved_game
from src.persistence import load_game
from src.persistence import rename_save as rename_saved_game
from web.api.common import (
    _catalog,
    _competition,
    _error,
    _fixture,
    _new_state,
    _ok,
    _save,
    _saves_payload,
    _state,
    _state_payload,
    _team_summary,
    _web,
)

api = Blueprint("api_core", __name__, url_prefix="/api")

@api.get("/health")
def health():
    return _ok({"service": "hockey-manager", "version": "react-1"})


@api.get("/menu")
def menu():
    web = _web()
    state = web.get_state()
    current = None
    if state is not None:
        current = {
            "team": _team_summary(state.user_team),
            "competition": _competition(competition(state.competition)),
            "season": state.season,
            "round": state.round,
            "date": state.date,
            "save_name": session.get("save_name", ""),
            "live_active": session.get("game_id") in web.LIVE,
        }
    return _ok({"current": current, "saves": _saves_payload()})


@api.get("/new-game")
def new_game_catalog():
    return _ok(_catalog())


@api.post("/new-game")
def create_game():
    payload = request.get_json(silent=True) or request.form
    club_id = str(payload.get("club_id", "")).strip()
    manager = str(payload.get("manager", "Entrenador")).strip() or "Entrenador"
    seed = str(payload.get("seed", "")).strip()
    if not club_id:
        return _error("Elige un club.", 400, "club_required")
    try:
        state = _new_state(club_id, manager, seed)
    except ValueError as exc:
        return _error(str(exc), 400, "invalid_club")
    return _ok(_state_payload(state), "Partida creada.")


@api.get("/load")
def load_catalog():
    return _ok({"saves": _saves_payload()})


@api.post("/load")
def load_save():
    web = _web()
    payload = request.get_json(silent=True) or request.form
    name = str(payload.get("name", "")).strip()
    if not name:
        return _error("Indica una partida.", 400, "save_required")
    try:
        state = load_game(name, web.WEB_DB)
    except Exception as exc:
        return _error(f"No se pudo cargar: {exc}", 404, "load_failed")
    old_gid = session.get("game_id")
    if old_gid:
        web.LIVE.pop(old_gid, None)
    gid = uuid.uuid4().hex
    web.GAMES[gid] = state
    session["game_id"] = gid
    session["save_name"] = name
    return _ok(_state_payload(state), "Partida cargada.")


@api.post("/save")
def save_game():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    name = str(payload.get("name", "")).strip()
    if name:
        session["save_name"] = name
    _save(state)
    return _ok(_state_payload(state), "Partida guardada.")


@api.delete("/saves")
def delete_save_route():
    web = _web()
    payload = request.get_json(silent=True) or request.form
    name = str(payload.get("name", "")).strip()
    if not name:
        return _error("Indica la partida que quieres eliminar.", 400, "save_required")
    try:
        deleted = delete_saved_game(name, web.WEB_DB)
    except Exception as exc:
        return _error(f"No se pudo eliminar: {exc}", 400, "delete_failed")
    if not deleted:
        return _error("No existe esa partida.", 404, "save_not_found")
    if session.get("save_name") == name:
        session.pop("save_name", None)
    return _ok({"saves": _saves_payload()}, "Partida eliminada.")


@api.patch("/saves")
def rename_save_route():
    web = _web()
    payload = request.get_json(silent=True) or request.form
    name = str(payload.get("name", "")).strip()
    new_name = str(payload.get("new_name", "")).strip()
    if not name or not new_name:
        return _error("Indica la partida y el nombre nuevo.", 400, "save_required")
    try:
        renamed = rename_saved_game(name, new_name, web.WEB_DB)
    except KeyError:
        return _error("No existe esa partida.", 404, "save_not_found")
    except ValueError as exc:
        return _error(str(exc), 409, "save_name_conflict")
    if session.get("save_name") == name:
        session["save_name"] = renamed
    return _ok({"saves": _saves_payload()}, "Partida renombrada.")


@api.post("/exit")
def exit_game():
    web = _web()
    state = web.get_state()
    if state:
        try:
            _save(state)
        except Exception:
            pass
    gid = session.pop("game_id", None)
    session.pop("save_name", None)
    if gid:
        web.LIVE.pop(gid, None)
    return _ok({"saves": _saves_payload()}, "Partida guardada. Has vuelto al menú.")


@api.get("/state")
def game_state():
    state, err = _state()
    if err:
        return err
    return _ok(_state_payload(state))


@api.post("/simulate")
def simulate():
    state, err = _state()
    if err:
        return err
    web = _web()
    if session.get("game_id") in web.LIVE:
        return _error("Termina primero el partido en directo.", 409, "live_active")
    payload = request.get_json(silent=True) or request.form
    mode = payload.get("mode", "day")
    target = str(payload.get("target_date", "")).strip()
    if mode == "next_match":
        match_day = next_match_date(state)
        if not match_day:
            return _error("No queda ningún partido pendiente.", 409, "no_match")
        result = simulate_days(state, target_date=match_day, stop_at_match=True, stop_at_decision=True)
    elif mode == "date":
        if not target:
            return _error("Elige una fecha.", 400, "date_required")
        try:
            result = simulate_days(state, target_date=target, stop_at_match=True, stop_at_decision=True)
        except ValueError:
            return _error("Fecha no válida.", 400, "invalid_date")
    else:
        result = simulate_days(state, days=1, stop_at_match=True, stop_at_decision=True)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo avanzar."), 409, "simulate_failed")
    _save(state)
    data = _state_payload(state)
    data["simulation"] = result
    message = f"Calendario avanzado {result['days']} día(s)."
    if result.get("stopped_at_decision"):
        message += " Hay una decisión pendiente."
    return _ok(data, message)


@api.get("/data-validation")
def data_validation():
    state, err = _state()
    if err:
        return err
    return _ok(validate_state(state))


@api.get("/table")
def table():
    state, err = _state()
    if err:
        return err
    code = str(request.args.get("league") or state.competition)
    meta = competition(code)
    teams = [t for t in state.teams.values() if t.league == code]
    if not teams:
        return _error("Esa liga no está disponible.", 404, "league_not_found")
    rows = sorted(teams, key=lambda t: (-t.points, -(t.goals_for - t.goals_against), -t.goals_for, t.name))
    fixtures = state.league_fixtures.get(code, [])
    if not fixtures and code == state.competition:
        fixtures = state.fixtures
    regular = [f for f in fixtures if f.phase == "regular"]
    leagues = [
        {
            "code": item.code,
            "name": item.name,
            "short_name": item.short_name,
            "country": item.country,
            "teams": len([t for t in state.teams.values() if t.league == item.code]),
        }
        for item in COMPETITIONS.values()
        if any(t.league == item.code for t in state.teams.values())
    ]
    return _ok(
        {
            "competition": _competition(meta),
            "table": [_team_summary(t, i) for i, t in enumerate(rows, 1)],
            "fixtures": [_fixture(f, state) for f in sorted(regular, key=lambda f: (f.round, f.date))],
            "leagues": leagues,
        }
    )


@api.get("/options")
def get_options():
    web = _web()
    return _ok({"prefs": web.ui_prefs()})


@api.post("/options")
def set_options():
    web = _web()
    payload = request.get_json(silent=True) or request.form
    if payload.get("reset"):
        session.pop("ui_prefs", None)
        return _ok({"prefs": web.ui_prefs()}, "Opciones restablecidas.")
    session["ui_prefs"] = {
        "text_size": "large" if payload.get("text_size") == "large" else "normal",
        "compact": bool(payload.get("compact")),
        "confirm_exit": bool(payload.get("confirm_exit")),
    }
    return _ok({"prefs": web.ui_prefs()}, "Opciones guardadas.")
