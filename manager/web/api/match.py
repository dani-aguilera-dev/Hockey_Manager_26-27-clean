"""API de match."""

from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, request, session
from src.analysis import analysis_overview
from src.competitions import competition
from src.friendlies import cancel_friendly, friendlies_payload, play_friendly, schedule_friendly
from src.match_plans import create_match_plan, delete_match_plan, match_plans_overview, update_match_plan
from src.models import FORMATION_SLOTS
from src.press import press_context
from src.season import finish_live_round, make_lineup, play_round, prepare_live_round, simulate_cup_round
from web.api.common import (
    _competition,
    _error,
    _fixture,
    _live_payload,
    _ok,
    _player,
    _save,
    _slot_rows,
    _state,
    _state_payload,
    _tactics_payload,
    _team_summary,
    _travel_options,
    _web,
)

api = Blueprint("api_match", __name__, url_prefix="/api")

@api.get("/tactics")
def tactics():
    state, err = _state()
    if err:
        return err
    return _ok(_tactics_payload(state))


@api.post("/tactics")
def save_tactics():
    state, err = _state()
    if err:
        return err
    team = state.user_team
    payload = request.get_json(silent=True) or request.form
    old_formation = team.tactics.formation
    for field in (
        "formation",
        "mentality",
        "press",
        "block",
        "width",
        "tempo",
        "passing",
        "pc_routine",
        "defensive_system",
        "attack_system",
        "outlet",
        "press_trigger",
    ):
        value = payload.get(field)
        if value:
            setattr(team.tactics, field, value)
    if team.tactics.defensive_system == "zona_baja":
        team.tactics.block = "bajo"
    elif team.tactics.defensive_system in ("zona_media", "individual_mixta"):
        team.tactics.block = "medio"
    elif team.tactics.defensive_system in ("zona_alta", "individual_todo_campo"):
        team.tactics.block = "alto"
    specialist_fields = (
        "pc_injector_id",
        "pc_stopper_id",
        "pc_flicker_id",
        "pc_deflector_id",
        "pc_rebounder_id",
        "pc_first_runner_id",
        "pc_goalkeeper_id",
        "stroke_taker_id",
        "stroke_goalkeeper_id",
        "free_hit_taker_id",
    )
    for field in specialist_fields:
        value = str(payload.get(field, "") or "")
        if value and not any(player.id == value for player in team.players):
            value = ""
        setattr(team.tactics, field, value)
    if team.tactics.formation != old_formation:
        state.manual_lineup = []
        message = "Formación cambiada. Once autoalineado."
    elif payload.get("auto"):
        state.manual_lineup = []
        message = "Autoalineación activada."
    else:
        slots = FORMATION_SLOTS.get(team.tactics.formation, FORMATION_SLOTS["4-3-3"])
        selected = [payload.get(f"slot_{i}", "") for i in range(len(slots))]
        selected = [x for x in selected if x]
        if len(selected) == 11 and len(set(selected)) == 11:
            state.manual_lineup = selected
            message = "Once guardado."
        else:
            return _error("El once debe tener 11 jugadores distintos.", 400, "invalid_lineup")
    _save(state)
    data = _tactics_payload(state)
    data["state"] = _state_payload(state)
    return _ok(data, message)


@api.get("/analysis")
def analysis():
    state, err = _state()
    if err:
        return err
    return _ok(analysis_overview(state, str(request.args.get("fixture_id", ""))))


@api.get("/match-plans")
def match_plans():
    state, err = _state()
    if err:
        return err
    return _ok(match_plans_overview(state))


@api.post("/match-plans")
def match_plans_create():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    instructions = payload.get("instructions", {})
    if not isinstance(instructions, dict):
        instructions = {}
    try:
        from_minute = int(payload.get("from_minute", 45) or 45)
    except (TypeError, ValueError):
        from_minute = 45
    result = create_match_plan(
        state,
        str(payload.get("name", "")),
        str(payload.get("situation", "leading") or "leading"),
        from_minute,
        instructions,
        bool(payload.get("enabled", True)),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo crear el plan."), 409, "match_plan_failed")
    _save(state)
    return _ok(
        {"result": result, "match_plans": match_plans_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.post("/match-plans/<plan_id>")
def match_plans_update(plan_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    instructions = payload.get("instructions", {})
    if not isinstance(instructions, dict):
        instructions = {}
    try:
        from_minute = int(payload.get("from_minute", 45) or 45)
    except (TypeError, ValueError):
        from_minute = 45
    result = update_match_plan(
        state,
        plan_id,
        str(payload.get("name", "")),
        str(payload.get("situation", "leading") or "leading"),
        from_minute,
        instructions,
        bool(payload.get("enabled", True)),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo actualizar el plan."), 409, "match_plan_failed")
    _save(state)
    return _ok(
        {"result": result, "match_plans": match_plans_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.delete("/match-plans/<plan_id>")
def match_plans_delete(plan_id: str):
    state, err = _state()
    if err:
        return err
    result = delete_match_plan(state, plan_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo eliminar el plan."), 409, "match_plan_failed")
    _save(state)
    return _ok(
        {"result": result, "match_plans": match_plans_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/calendar")
def calendar():
    state, err = _state()
    if err:
        return err
    official = sorted(
        [fixture for fixture in state.fixtures if fixture.phase in ("regular", "cup", "promotion")],
        key=lambda fixture: (fixture.date, fixture.round, fixture.id),
    )
    friendly_payload = friendlies_payload(state)
    pending_friendlies = [item for item in friendly_payload["items"] if not item["played"]]
    return _ok(
        {
            "friendlies": friendly_payload,
            "fixtures": [_fixture(fixture, state) for fixture in official],
            "next_fixture": _fixture(state.next_user_fixture(), state) if state.next_user_fixture() else None,
            "next_friendly": pending_friendlies[0] if pending_friendlies else None,
            "today": state.date,
            "season": state.season,
            "competition": _competition(competition(state.competition)),
        }
    )


@api.post("/friendlies")
def friendly_create():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = schedule_friendly(
        state,
        str(payload.get("opponent_id", "")),
        str(payload.get("date", "")),
        home=str(payload.get("home", "1")) not in ("0", "false", "False", ""),
        notes=str(payload.get("notes", "")),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo programar el amistoso."), 409, "friendly_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.post("/friendlies/<friendly_id>/play")
def friendly_play(friendly_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    lineup = payload.get("lineup") if isinstance(payload, dict) else None
    result = play_friendly(state, friendly_id, lineup if isinstance(lineup, list) else None)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo jugar el amistoso."), 409, "friendly_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.delete("/friendlies/<friendly_id>")
def friendly_delete(friendly_id: str):
    state, err = _state()
    if err:
        return err
    result = cancel_friendly(state, friendly_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo cancelar el amistoso."), 409, "friendly_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.get("/match")
def match_preview():
    state, err = _state()
    if err:
        return err
    web = _web()
    gid = session.get("game_id")
    if gid in web.LIVE:
        return _ok({"live": True})
    fx = state.next_user_fixture()
    if not fx:
        return _error("No hay partido pendiente.", 409, "no_match")
    home, away = state.teams[fx.home_id], state.teams[fx.away_id]
    user = state.user_team
    line, bench = make_lineup(user, state.manual_lineup or None)
    travel = _travel_options(state, fx)

    def top_scorer(t):
        return max(t.players, key=lambda p: (p.season_goals, p.overall), default=None)

    def absences(t):
        return [p for p in t.players if p.injury or p.suspension]

    return _ok(
        {
            "live": False,
            "fixture": _fixture(fx, state),
            "is_cup": fx.phase.startswith("cup_"),
            "home": _team_summary(home),
            "away": _team_summary(away),
            "line": [_player(p, user) for p in line],
            "bench": [_player(p, user) for p in bench],
            "travel": travel,
            "home_top": _player(top_scorer(home), home) if top_scorer(home) else None,
            "away_top": _player(top_scorer(away), away) if top_scorer(away) else None,
            "home_absences": [_player(p, home) for p in absences(home)],
            "away_absences": [_player(p, away) for p in absences(away)],
            "home_form": web.team_form(state, home.id),
            "away_form": web.team_form(state, away.id),
            "slot_rows": _slot_rows(web.lineup_rows(user, line)),
            "press_context": press_context(state),
        }
    )


@api.post("/match/live/start")
def match_live_start():
    state, err = _state()
    if err:
        return err
    web = _web()
    gid = session.get("game_id")
    if gid in web.LIVE:
        return _ok(_live_payload(state, web.LIVE[gid]))
    next_fixture = state.next_user_fixture()
    if next_fixture and next_fixture.phase.startswith("cup_"):
        return _error("La Copa del Rey se juega en simulación rápida.", 400, "cup_quick_only")
    payload = request.get_json(silent=True) or request.form
    travel_id = payload.get("travel") or None
    try:
        ctx = prepare_live_round(state, state.manual_lineup or None, travel_id)
    except Exception as exc:
        return _error(f"No se pudo iniciar el directo: {exc}", 409, "live_start_failed")
    web.LIVE[gid] = ctx
    return _ok(_live_payload(state, ctx), "Partido en directo iniciado.")


@api.get("/match/live")
def match_live():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    return _ok(_live_payload(state, ctx))


@api.post("/match/live/advance")
def match_live_advance():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    payload = request.get_json(silent=True) or request.form
    mode = payload.get("mode", "quarter")
    engine = ctx.engine
    if mode == "moment":
        engine.advance_moment()
    elif mode == "rest":
        while not engine.finished:
            engine.advance_quarter()
    else:
        engine.advance_quarter()
    return _ok(_live_payload(state, ctx))


@api.post("/match/live/tactics")
def match_live_tactics():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    payload = request.get_json(silent=True) or request.form
    for field in ("mentality", "press", "block", "width", "tempo", "passing", "pc_routine"):
        value = payload.get(field)
        if value:
            setattr(state.user_team.tactics, field, value)
    return _ok(_live_payload(state, ctx), "Táctica actualizada.")


@api.post("/match/live/sub")
def match_live_sub():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    payload = request.get_json(silent=True) or request.form
    ok, message = ctx.engine.manual_substitute(ctx.user_side, payload.get("out_id", ""), payload.get("in_id", ""), coaching=True)
    if not ok:
        return _error(message, 409, "sub_failed")
    return _ok(_live_payload(state, ctx), message)


@api.post("/match/live/review")
def match_live_review():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    payload = request.get_json(silent=True) or request.form
    decision = str(payload.get("decision", "") or "")
    result = ctx.engine.review_decision(ctx.user_side, decision)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo revisar la decisión."), 409, "review_failed")
    return _ok(_live_payload(state, ctx), result.get("message", "Revisión completada."))


@api.post("/match/live/protest")
def match_live_protest():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    payload = request.get_json(silent=True) or request.form
    result = ctx.engine.protest_decision(ctx.user_side, str(payload.get("tone", "respetuosa") or "respetuosa"))
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo protestar."), 409, "protest_failed")
    return _ok(_live_payload(state, ctx), result.get("message", "Protesta registrada."))


@api.post("/match/live/finish")
def match_live_finish():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    if not ctx.engine.finished:
        ctx.engine.simulate()
    payload = finish_live_round(state, ctx)
    web.LIVE.pop(session.get("game_id"), None)
    _save(state)
    return _ok({"report": payload, "state": _state_payload(state)}, "Partido finalizado.")


@api.post("/match/quick")
def match_quick():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    travel_id = payload.get("travel") or None
    next_fixture = state.next_user_fixture()
    if next_fixture and next_fixture.phase.startswith("cup_"):
        result = simulate_cup_round(state, state.manual_lineup or None)
        if result:
            state.date = (date.fromisoformat(next_fixture.date) + timedelta(days=1)).isoformat()
            _save(state)
            return _ok({"report": state.last_result, "state": _state_payload(state)}, "Eliminatoria de Copa simulada.")
        return _error("No se pudo simular la eliminatoria de Copa.", 409, "cup_sim_failed")
    result = play_round(state, state.manual_lineup or None, travel_id)
    if not result:
        return _error("No se pudo simular el partido.", 409, "match_sim_failed")
    _save(state)
    return _ok({"report": result, "state": _state_payload(state)}, "Partido simulado.")


@api.get("/match/report")
def match_report():
    state, err = _state()
    if err:
        return err
    if not state.last_result:
        return _error("No hay parte de partido.", 404, "no_report")
    return _ok({"report": state.last_result, "state": _state_payload(state)})
