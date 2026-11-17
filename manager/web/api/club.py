"""API de club."""

from __future__ import annotations

import random

from flask import Blueprint, request
from src.affiliates import (
    affiliate_overview,
    assign_mentor,
    end_affiliate,
    end_mentoring,
    mentoring_overview,
    request_affiliate,
)
from src.awards import awards_overview
from src.board import board_overview, request_board
from src.brands import (
    accept_brand_offer,
    accept_player_brand_offer,
    brand_summary,
    reject_brand_offer,
    reject_player_brand_offer,
)
from src.clauses import clauses_overview, set_clause
from src.commercial import (
    accept_sponsor_offer,
    commercial_summary,
    generate_sponsor_offers,
    reject_sponsor_offer,
    run_campaign,
    set_ticket_price,
)
from src.competitions import competition
from src.contracts import contracts_overview
from src.data_loader import load_clubs
from src.datahub import datahub_overview, set_instructions
from src.development import clear_development_plan, development_overview, set_development_plan
from src.facilities import facilities_overview, upgrade_facility
from src.finance import finance_overview, financial_summary
from src.history import history_overview
from src.international import club_catalog
from src.market import (
    STAFF_LABELS,
    asking_price,
    fire_staff,
    hire_staff,
    market_window,
    market_window_text,
    scout_range,
    staff_candidates,
)
from src.player_editor import edit_player, editor_payload, find_player
from src.responsibilities import responsibilities_overview, set_responsibility
from src.shortlist import is_shortlisted
from src.team_meeting import perform_team_meeting, team_meeting_context
from src.training import DAYS, PLAN_PRESETS, SESSION_ORDER, SESSION_TYPES, apply_training_plan, auto_plan, plan_name
from src.youth import CATEGORY_AGES, CATEGORY_LABELS, YOUTH_CATEGORIES, promote_youth, release_youth
from web.api.common import (
    _error,
    _fixture,
    _money,
    _ok,
    _opponent,
    _player,
    _save,
    _slot_rows,
    _state,
    _state_payload,
    _team,
    _team_summary,
    _web,
)

api = Blueprint("api_club", __name__, url_prefix="/api")

@api.get("/medical")
def medical():
    state, err = _state()
    if err:
        return err
    team = state.user_team
    injured = sorted(
        [player for player in team.players if player.injury > 0],
        key=lambda player: (-player.injury, player.name),
    )
    suspended = sorted(
        [player for player in team.players if player.suspension > 0],
        key=lambda player: (-player.suspension, player.name),
    )
    history: list[dict] = []
    for player in team.players:
        for item in player.injury_history:
            history.append(
                {
                    **item,
                    "player_id": player.id,
                    "player_name": player.name,
                    "kind": "injury",
                }
            )
        for item in player.card_history:
            history.append(
                {
                    **item,
                    "player_id": player.id,
                    "player_name": player.name,
                    "kind": "card",
                }
            )
    history.sort(key=lambda item: (str(item.get("date", "")), int(item.get("minute", 0))), reverse=True)
    avg_fatigue = sum(player.fatigue for player in team.players) / max(1, len(team.players))
    return _ok(
        {
            "injuries": [_player(player, team) for player in injured],
            "suspensions": [_player(player, team) for player in suspended],
            "history": history[:40],
            "summary": {
                "available": len(team.available_players),
                "injured": len(injured),
                "suspended": len(suspended),
                "avg_fatigue": round(avg_fatigue, 1),
                "risk": sum(1 for player in team.players if player.fatigue >= 65),
                "physio": team.staff_rating("physio"),
                "fitness_coach": team.staff_rating("fitness_coach"),
            },
        }
    )


@api.get("/squad")
def squad():
    state, err = _state()
    if err:
        return err
    groups = []
    for group in ("Portero", "Defensa", "Medio", "Delantero"):
        members = [p for p in state.user_team.players if p.position_group == group]
        if members:
            groups.append({"group": group, "players": [_player(p, state.user_team) for p in sorted(members, key=lambda p: (p.subposition, -p.overall))]})
    return _ok({"groups": groups, "team": _team(state.user_team)})


@api.get("/player/<player_id>")
def player_detail(player_id):
    state, err = _state()
    if err:
        return err
    owner = next((t for t in state.teams.values() if any(p.id == player_id for p in t.players)), None)
    player = next((p for p in owner.players if p.id == player_id), None) if owner else None
    if player is None:
        player = next((p for p in state.free_agents if p.id == player_id), None)
    if player is None:
        return _error("Jugador no encontrado.", 404, "player_not_found")
    owner_summary = _team_summary(owner) if owner else None
    data = {
        "player": _player(player, owner),
        "owner": owner_summary,
        "owner_name": owner.name if owner else "Agente libre",
        "is_user": owner is not None and owner.id == state.club_id,
        "editor": editor_payload(player),
        "market": None,
        "shortlisted": is_shortlisted(state, player.id),
    }
    if owner is None or owner.id != state.club_id:
        data["market"] = {
            "asking": asking_price(player),
            "scout": scout_range(player, state.user_team.staff_rating("scout")),
            "window": market_window(state),
            "window_text": market_window_text(state),
            "minimum_salary": int(max(5000, (player.overall - 45) * 900)),
        }
    return _ok(data)


@api.get("/team/<team_id>")
def team_detail(team_id):
    state, err = _state()
    if err:
        return err
    selected = state.teams.get(team_id)
    if selected is None:
        return _error("Equipo no encontrado.", 404, "team_not_found")
    if state.competition == selected.league:
        table = state.table()
    else:
        table = sorted(
            [t for t in state.teams.values() if t.league == selected.league],
            key=lambda t: (-t.points, -(t.goals_for - t.goals_against), -t.goals_for, t.name),
        )
    position = next((i for i, t in enumerate(table, 1) if t.id == selected.id), 0)
    fixtures = sorted([f for f in state.fixtures if selected.id in (f.home_id, f.away_id)], key=lambda f: (f.date, f.round))
    line, bench = selected.auto_lineup()
    web = _web()
    clubs = {**load_clubs()[0], **club_catalog()}
    club = clubs.get(selected.id, {})
    team_group = ""
    if competition(selected.league).system == "dhb_two_phase" and state.dhb_groups:
        team_group = next((g for g, ids in state.dhb_groups.items() if selected.id in ids), "")
    return _ok(
        {
            "team": _team(selected),
            "club": {
                "history": club.get("history", ""),
                "founded": club.get("founded", ""),
                "full_name": club.get("full_name", selected.name),
                "city": club.get("city", selected.city),
                "province": club.get("province", ""),
                "community": club.get("community", selected.community),
                "country": club.get("country", selected.country),
                "source_url": club.get("source_url", ""),
                "location_verified": club.get("location_verified", False),
                "stadium": club.get("stadium", {}),
                "colors": club.get("colors", []),
                "facilities": club.get("facilities", {}),
            },
            "position": position,
            "table": [_team_summary(t, i) for i, t in enumerate(table, 1)],
            "fixtures": [_fixture(f, state) for f in fixtures],
            "played": [_fixture(f, state) for f in fixtures if f.played][-5:],
            "upcoming": [_fixture(f, state) for f in fixtures if not f.played][:5],
            "probable_lineup": [_player(p, selected) for p in line],
            "probable_bench": [_player(p, selected) for p in bench],
            "probable_rows": _slot_rows(web.lineup_rows(selected, line)),
            "formation": selected.tactics.formation,
            "group": team_group,
            "is_user": selected.id == state.club_id,
        }
    )


@api.get("/training")
def training():
    state, err = _state()
    if err:
        return err
    opponent = _opponent(state)
    default_plan = auto_plan(state.user_team, opponent, random.Random(state.seed + state.round * 53 + 11))
    return _ok(
        {
            "sessions": SESSION_TYPES,
            "session_order": SESSION_ORDER,
            "days": DAYS,
            "default_plan": default_plan,
            "plan_name": plan_name(state.weekly_plan) if state.weekly_plan else plan_name(default_plan),
            "report": state.training_report,
            "trained": state.week_trained,
            "opponent": _team_summary(opponent) if opponent else None,
            "presets": PLAN_PRESETS,
        }
    )


@api.post("/training")
def apply_training():
    state, err = _state()
    if err:
        return err
    if state.week_trained:
        return _error("La semana ya está planificada.", 409, "already_trained")
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "auto")
    if action == "recovery":
        plan = list(PLAN_PRESETS["recuperacion"])
        delegated = False
    elif action == "edit":
        plan = [payload.get(f"session{i}", "recuperacion") for i in range(5)]
        plan = [p if p in SESSION_TYPES else "recuperacion" for p in plan]
        delegated = False
    else:
        plan = auto_plan(state.user_team, _opponent(state), random.Random(state.seed + state.round * 53 + 11))
        delegated = True
    report = apply_training_plan(
        state.user_team,
        plan,
        _opponent(state),
        random.Random(state.seed + state.round * 53 + 17),
        delegated=delegated,
    )
    state.weekly_plan = plan
    state.training_report = report
    state.week_trained = True
    _save(state)
    return _ok(
        {
            "report": report,
            "plan": plan,
            "plan_name": plan_name(plan),
            "trained": True,
            "state": _state_payload(state),
        },
        "Entrenamiento semanal aplicado.",
    )


@api.get("/board")
def board():
    state, err = _state()
    if err:
        return err
    return _ok(board_overview(state))


@api.post("/board/request")
def board_request():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = request_board(state, str(payload.get("request_id", "")))
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo procesar la petición."), 409, "board_request_failed")
    _save(state)
    return _ok(
        {"result": result, "board": board_overview(state), "state": _state_payload(state)},
        result.get("message", "Petición registrada."),
    )


@api.get("/clauses")
def clauses():
    state, err = _state()
    if err:
        return err
    return _ok(clauses_overview(state))


@api.post("/clauses/<player_id>")
def clauses_update(player_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        release_clause = int(payload.get("release_clause", 0) or 0)
        renewal_bonus = int(payload.get("renewal_bonus", 0) or 0)
    except (TypeError, ValueError):
        return _error("Cláusula o prima no válida.", 400, "invalid_clause")
    result = set_clause(state, player_id, release_clause, renewal_bonus)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo actualizar la cláusula."), 409, "clause_failed")
    _save(state)
    return _ok(
        {"result": result, "clauses": clauses_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/facilities")
def facilities():
    state, err = _state()
    if err:
        return err
    return _ok(facilities_overview(state))


@api.post("/facilities/upgrade")
def facilities_upgrade():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = upgrade_facility(state, str(payload.get("request_id", "")))
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo solicitar la mejora."), 409, "facility_failed")
    _save(state)
    return _ok(
        {"result": result, "facilities": facilities_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/contracts")
def contracts():
    state, err = _state()
    if err:
        return err
    return _ok(contracts_overview(state))


@api.get("/awards")
def awards():
    state, err = _state()
    if err:
        return err
    return _ok(awards_overview(state))


@api.get("/finance")
def finance():
    state, err = _state()
    if err:
        return err
    return _ok(finance_overview(state))


@api.post("/finance/ticket")
def finance_ticket():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        price = int(payload.get("price", state.user_team.ticket_price))
    except (TypeError, ValueError):
        return _error("Precio no válido.", 400, "invalid_price")
    result = set_ticket_price(state, price)
    _save(state)
    return _ok(
        {"result": result, "finance": finance_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/commercial")
def commercial():
    state, err = _state()
    if err:
        return err
    generate_sponsor_offers(state)
    return _ok(
        {
            "commercial": commercial_summary(state),
            "brands": brand_summary(state),
            "finance": financial_summary(state.user_team),
            "team": _team(state.user_team),
        }
    )


@api.post("/commercial/offers/<offer_id>")
def commercial_offer_action(offer_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "accept")
    result = accept_sponsor_offer(state, offer_id) if action == "accept" else reject_sponsor_offer(state, offer_id)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo procesar."), 409, "sponsor_failed")


@api.post("/commercial/ticket")
def commercial_ticket():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        price = int(payload.get("price", state.user_team.ticket_price))
    except (TypeError, ValueError):
        return _error("Precio no válido.", 400, "invalid_price")
    result = set_ticket_price(state, price)
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.post("/commercial/campaign")
def commercial_campaign():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = run_campaign(state, str(payload.get("campaign_id", "")))
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo lanzar."), 409, "campaign_failed")


@api.get("/datahub")
def datahub():
    state, err = _state()
    if err:
        return err
    return _ok(datahub_overview(state))


@api.post("/datahub/instructions")
def datahub_instructions():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    instructions = payload.get("instructions", {})
    if not isinstance(instructions, dict):
        instructions = {}
    result = set_instructions(state, str(payload.get("opponent_id", "")), instructions)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudieron guardar las instrucciones."), 409, "datahub_failed")
    _save(state)
    return _ok({"result": result, "datahub": datahub_overview(state), "state": _state_payload(state)}, result["message"])


@api.get("/affiliates")
def affiliates():
    state, err = _state()
    if err:
        return err
    return _ok({"affiliates": affiliate_overview(state), "mentoring": mentoring_overview(state)})


@api.post("/affiliates/request")
def affiliate_request():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = request_affiliate(state, str(payload.get("club_id", "")))
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo firmar la afiliación."), 409, "affiliate_failed")
    _save(state)
    return _ok(
        {
            "result": result,
            "affiliates": affiliate_overview(state),
            "mentoring": mentoring_overview(state),
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )


@api.post("/affiliates/<affiliate_id>/end")
def affiliate_end(affiliate_id: str):
    state, err = _state()
    if err:
        return err
    result = end_affiliate(state, affiliate_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo finalizar la afiliación."), 409, "affiliate_failed")
    _save(state)
    return _ok(
        {
            "result": result,
            "affiliates": affiliate_overview(state),
            "mentoring": mentoring_overview(state),
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )


@api.post("/mentoring")
def mentoring_create():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = assign_mentor(
        state,
        str(payload.get("mentor_id", "")),
        str(payload.get("mentee_id", "")),
        str(payload.get("focus", "tecnica") or "tecnica"),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo crear el plan de mentoría."), 409, "mentoring_failed")
    _save(state)
    return _ok(
        {
            "result": result,
            "affiliates": affiliate_overview(state),
            "mentoring": mentoring_overview(state),
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )


@api.delete("/mentoring/<pair_id>")
def mentoring_delete(pair_id: str):
    state, err = _state()
    if err:
        return err
    result = end_mentoring(state, pair_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo finalizar el plan."), 409, "mentoring_failed")
    _save(state)
    return _ok(
        {
            "result": result,
            "affiliates": affiliate_overview(state),
            "mentoring": mentoring_overview(state),
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )


@api.get("/history")
def history():
    state, err = _state()
    if err:
        return err
    try:
        limit = max(1, min(500, int(request.args.get("limit", 200))))
    except (TypeError, ValueError):
        limit = 200
    return _ok(
        history_overview(
            state,
            season=str(request.args.get("season", "")),
            competition_code=str(request.args.get("competition", "")),
            team_id=str(request.args.get("team_id", "")),
            player_query=str(request.args.get("player", "")),
            limit=limit,
        )
    )


@api.get("/team-meeting")
def team_meeting():
    state, err = _state()
    if err:
        return err
    return _ok(team_meeting_context(state))


@api.post("/team-meeting")
def team_meeting_perform():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    topics = payload.get("topics", [])
    if not isinstance(topics, list):
        topics = []
    result = perform_team_meeting(
        state,
        str(payload.get("meeting_type", "pre_match") or "pre_match"),
        str(payload.get("tone", "serena") or "serena"),
        [str(item) for item in topics],
        str(payload.get("promise_player_id", "")),
        str(payload.get("promise_type", "")),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo celebrar la reunión."), 409, "team_meeting_failed")
    _save(state)
    return _ok(
        {"result": result, "meeting": team_meeting_context(state), "state": _state_payload(state)},
        result.get("message", "Reunión celebrada."),
    )


@api.get("/responsibilities")
def responsibilities():
    state, err = _state()
    if err:
        return err
    return _ok(responsibilities_overview(state))


@api.post("/responsibilities")
def responsibilities_update():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = set_responsibility(state, str(payload.get("area", "")), str(payload.get("staff_name", "")))
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo actualizar la responsabilidad."), 409, "responsibility_failed")
    _save(state)
    return _ok(
        {"result": result, "responsibilities": responsibilities_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/development")
def development():
    state, err = _state()
    if err:
        return err
    return _ok(development_overview(state))


@api.post("/development/<player_id>")
def development_set(player_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = set_development_plan(
        state,
        player_id,
        str(payload.get("focus", "tecnica") or "tecnica"),
        str(payload.get("intensity", "normal") or "normal"),
        str(payload.get("notes", "")),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo asignar el plan."), 409, "development_failed")
    _save(state)
    return _ok(
        {"result": result, "development": development_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.delete("/development/<player_id>")
def development_clear(player_id: str):
    state, err = _state()
    if err:
        return err
    result = clear_development_plan(state, player_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo retirar el plan."), 409, "development_failed")
    _save(state)
    return _ok(
        {"result": result, "development": development_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/staff")
def staff():
    state, err = _state()
    if err:
        return err
    hireable = (
        "assistant",
        "fitness_coach",
        "gk_coach",
        "performance_analyst",
        "scout",
        "physio",
        "technical_director",
        "commercial_director",
        "marketing_manager",
    )
    free_roles = [r for r in hireable if not any(m.role == r for m in state.user_team.staff)]
    return _ok(
        {
            "team": _team(state.user_team),
            "staff_labels": STAFF_LABELS,
            "free_roles": free_roles,
        }
    )


@api.get("/staff/<role>/candidates")
def staff_candidates_route(role):
    state, err = _state()
    if err:
        return err
    if role not in STAFF_LABELS:
        return _error("Rol no válido.", 400, "invalid_role")
    rng = random.Random(state.seed * 1000 + state.round * 61 + len(state.user_team.staff))
    candidates = staff_candidates(state.user_team, role, rng)
    return _ok(
        {
            "role": role,
            "role_label": STAFF_LABELS[role],
            "candidates": [
                {
                    "role": c.role,
                    "name": c.name,
                    "rating": c.rating,
                    "salary": _money(c.salary),
                    "contract_until": c.contract_until,
                    "source": c.source,
                    "confidence": c.confidence,
                }
                for c in candidates
            ],
        }
    )


@api.post("/staff/hire/<role>")
def staff_hire(role):
    state, err = _state()
    if err:
        return err
    if role not in STAFF_LABELS:
        return _error("Rol no válido.", 400, "invalid_role")
    if any(m.role == role for m in state.user_team.staff):
        return _error("Ese rol ya está cubierto.", 409, "role_filled")
    rng = random.Random(state.seed * 1000 + state.round * 61 + len(state.user_team.staff))
    candidates = staff_candidates(state.user_team, role, rng)
    payload = request.get_json(silent=True) or request.form
    try:
        idx = int(payload.get("candidate", -1))
    except (TypeError, ValueError):
        idx = -1
    if not (0 <= idx < len(candidates)):
        return _error("Candidato no válido.", 400, "invalid_candidate")
    result = hire_staff(state, candidates[idx])
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo contratar."), 409, "hire_rejected")


@api.post("/staff/fire/<role>")
def staff_fire(role):
    state, err = _state()
    if err:
        return err
    result = fire_staff(state, role)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo despedir."), 409, "fire_rejected")


@api.get("/youth")
def youth():
    state, err = _state()
    if err:
        return err
    groups = []
    for category in YOUTH_CATEGORIES:
        members = [p for p in state.user_team.youth if p.youth_category == category]
        if members:
            groups.append(
                {
                    "category": category,
                    "label": CATEGORY_LABELS[category],
                    "ages": CATEGORY_AGES[category],
                    "players": [_player(p, state.user_team) for p in members],
                }
            )
    return _ok({"groups": groups, "team": _team(state.user_team)})


@api.post("/youth/<action>/<player_id>")
def youth_action(action, player_id):
    state, err = _state()
    if err:
        return err
    if action == "promote":
        ok, message = promote_youth(state.user_team, player_id)
    elif action == "release":
        ok, message = release_youth(state.user_team, player_id)
    else:
        return _error("Acción no válida.", 400, "invalid_action")
    if ok:
        _save(state)
    return _ok({"state": _state_payload(state)}, message) if ok else _error(message, 409, "youth_action_failed")


@api.get("/brands")
def brands():
    state, err = _state()
    if err:
        return err
    return _ok({"brands": brand_summary(state), "team": _team(state.user_team)})


@api.post("/brands/<offer_id>")
def brand_action(offer_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "accept")
    result = accept_brand_offer(state, offer_id) if action == "accept" else reject_brand_offer(state, offer_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo procesar la marca."), 409, "brand_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.post("/brands/players/<offer_id>")
def player_brand_action(offer_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "accept")
    result = accept_player_brand_offer(state, offer_id) if action == "accept" else reject_player_brand_offer(state, offer_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo procesar el contrato individual."), 409, "player_brand_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.post("/player/<player_id>/edit")
def player_edit(player_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    changes = payload.get("changes", payload) if isinstance(payload, dict) else {}
    result = edit_player(state, player_id, changes if isinstance(changes, dict) else {})
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo editar la ficha."), 400, "player_edit_failed")
    _save(state)
    player, owner_id = find_player(state, player_id)
    owner = state.teams.get(owner_id) if owner_id else None
    return _ok(
        {
            "result": result,
            "player": _player(player, owner) if player else None,
            "editor": editor_payload(player) if player else None,
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )
