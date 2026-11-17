"""API de market."""

from __future__ import annotations

from flask import Blueprint, request
from src.competitions import competition
from src.loans import loan_overview, offer_loan_out, request_loan_in
from src.market import (
    STAFF_LABELS,
    accept_incoming_offer,
    generate_incoming_offers,
    hire_market_staff,
    list_player_for_transfer,
    make_transfer_offer,
    market_players,
    market_window,
    market_window_text,
    reject_incoming_offer,
    renew_contract,
    staff_market,
)
from src.negotiation import (
    counter_incoming_offer,
    respond_negotiation,
    start_renewal_negotiation,
    start_transfer_negotiation,
)
from src.ratings import league_label, profile
from src.scouting import cancel_assignment, create_assignment, scouting_overview
from src.shortlist import (
    add_to_shortlist,
    remove_from_shortlist,
    shortlist_candidates,
    shortlist_overview,
    update_shortlist_entry,
)
from src.trials import end_trial, invite_trial, trial_overview
from web.api.common import (
    _error,
    _market_player,
    _ok,
    _player,
    _save,
    _state,
    _state_payload,
    _team_summary,
)

api = Blueprint("api_market", __name__, url_prefix="/api")

@api.get("/scouting")
def scouting():
    state, err = _state()
    if err:
        return err
    focus = request.args.get("focus", "equilibrado")
    raw_age = str(request.args.get("max_age", "")).strip()
    max_age = int(raw_age) if raw_age.isdigit() else None
    position = request.args.get("position", "")
    payload = scouting_overview(state, focus=focus, max_age=max_age, position=position or None)
    payload["recommendations"] = [
        {
            **{key: value for key, value in row.items() if key != "player"},
            "player": _market_player(row["player"], state),
        }
        for row in payload["recommendations"]
    ]
    return _ok(payload)


@api.post("/scouting/assignments")
def scouting_assignment_create():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    raw_age = str(payload.get("max_age", "")).strip()
    max_age = int(raw_age) if raw_age.isdigit() else None
    result = create_assignment(
        state,
        str(payload.get("scout_id", "")),
        str(payload.get("competition", "")),
        str(payload.get("position", "")),
        max_age,
        str(payload.get("focus", "equilibrado") or "equilibrado"),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo crear la asignación."), 409, "scouting_failed")
    _save(state)
    overview = scouting_overview(state)
    overview["recommendations"] = [
        {**{key: value for key, value in row.items() if key != "player"}, "player": _market_player(row["player"], state)}
        for row in overview["recommendations"]
    ]
    return _ok({"result": result, "scouting": overview, "state": _state_payload(state)}, result["message"])


@api.delete("/scouting/assignments/<assignment_id>")
def scouting_assignment_delete(assignment_id: str):
    state, err = _state()
    if err:
        return err
    result = cancel_assignment(state, assignment_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo cancelar la asignación."), 409, "scouting_failed")
    _save(state)
    overview = scouting_overview(state)
    overview["recommendations"] = [
        {**{key: value for key, value in row.items() if key != "player"}, "player": _market_player(row["player"], state)}
        for row in overview["recommendations"]
    ]
    return _ok({"result": result, "scouting": overview, "state": _state_payload(state)}, result["message"])


@api.get("/market")
def market():
    state, err = _state()
    if err:
        return err
    def number_arg(name, cast=int):
        raw = str(request.args.get(name, "")).strip()
        if not raw:
            return None
        try:
            return cast(raw)
        except ValueError:
            return None

    max_value = number_arg("max_value")
    min_age = number_arg("min_age")
    max_age = number_arg("max_age")
    min_overall = number_arg("min_overall", float)
    max_overall = number_arg("max_overall", float)
    min_attribute = number_arg("min_attribute")
    position = request.args.get("position", "")
    club_id = request.args.get("club_id", "")
    league = request.args.get("league", "")
    query = request.args.get("q", "").strip()
    attribute = request.args.get("attribute", "")
    listed_only = request.args.get("listed") == "1"
    free_agents_only = request.args.get("free_agents") == "1"
    staff_role = request.args.get("staff_role", "")
    staff_min_rating = number_arg("staff_min_rating")
    staff_max_salary = number_arg("staff_max_salary")
    players = market_players(
        state,
        limit=3000,
        max_value=max_value,
        position=position or None,
        min_age=min_age,
        max_age=max_age,
        min_overall=min_overall,
        max_overall=max_overall,
        league=league or None,
        club_id=club_id or None,
        query=query or None,
        attribute=attribute or None,
        min_attribute=min_attribute,
        listed_only=listed_only,
        free_agents_only=free_agents_only,
    )
    owners = {p.id: t for t in state.teams.values() for p in t.players}
    regular_players = [p for p in players if p.id in owners]
    free_agents = [p for p in players if p.id not in owners]
    all_teams = sorted(state.teams.values(), key=lambda t: (t.league, t.name))
    leagues = []
    seen = set()
    for team in all_teams:
        if team.league in seen:
            continue
        seen.add(team.league)
        meta = competition(team.league)
        leagues.append(
            {
                "code": meta.code,
                "name": meta.name,
                "short_name": meta.short_name,
                "country": meta.country,
                "standard": meta.standard,
            }
        )
    for code in sorted({p.league for p in state.free_agents}):
        if code in seen:
            continue
        seen.add(code)
        meta = profile(code)
        leagues.append(
            {
                "code": code,
                "name": league_label(code),
                "short_name": league_label(code),
                "country": "España",
                "standard": meta.standard,
            }
        )
    leagues.sort(key=lambda row: row["standard"], reverse=True)
    staff = staff_market(
        state,
        limit=80,
        role=staff_role or None,
        min_rating=staff_min_rating,
        max_salary=staff_max_salary,
    )
    return _ok(
        {
            "players": [_market_player(p, state) for p in regular_players],
            "free_agents": [_market_player(p, state) for p in free_agents],
            "staff": staff,
            "staff_roles": STAFF_LABELS,
            "teams": [_team_summary(t) for t in all_teams],
            "leagues": leagues,
            "attributes": sorted({key for player in players for key in player.attributes}),
            "listed": [
                _player(p, state.user_team)
                for p in state.user_team.players
                if p.transfer_listed
            ],
            "pending_transfers": state.pending_transfers,
            "own_players": [_player(p, state.user_team) for p in state.user_team.players],
            "window": market_window(state),
            "window_text": market_window_text(state),
            "offers": state.transfer_offers,
            "negotiations": state.negotiations[-10:],
            "query": query,
            "max_value": max_value,
            "min_age": min_age,
            "max_age": max_age,
            "min_overall": min_overall,
            "max_overall": max_overall,
            "position": position,
            "club_id": club_id,
            "league": league,
            "attribute": attribute,
            "min_attribute": min_attribute,
            "listed_only": listed_only,
            "free_agents_only": free_agents_only,
            "total": len(players),
            "free_agent_total": len(free_agents),
            "staff_total": len(staff),
        }
    )


@api.get("/trials")
def trials():
    state, err = _state()
    if err:
        return err
    return _ok(trial_overview(state, str(request.args.get("q", ""))))


@api.post("/trials")
def trials_invite():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        days = int(payload.get("days", 14) or 14)
    except (TypeError, ValueError):
        days = 14
    result = invite_trial(state, str(payload.get("player_id", "")), days)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo iniciar la prueba."), 409, "trial_failed")
    _save(state)
    return _ok(
        {"result": result, "trials": trial_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.post("/trials/<trial_id>/end")
def trials_end(trial_id: str):
    state, err = _state()
    if err:
        return err
    result = end_trial(state, trial_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo cerrar la prueba."), 409, "trial_failed")
    _save(state)
    return _ok(
        {"result": result, "trials": trial_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/shortlist")
def shortlist():
    state, err = _state()
    if err:
        return err
    return _ok(shortlist_overview(state))


@api.get("/shortlist/candidates")
def shortlist_candidates_api():
    state, err = _state()
    if err:
        return err
    try:
        limit = max(1, min(40, int(request.args.get("limit", 12))))
    except (TypeError, ValueError):
        limit = 12
    return _ok({"candidates": shortlist_candidates(state, str(request.args.get("q", "")), limit)})


@api.post("/shortlist")
def shortlist_add():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = add_to_shortlist(
        state,
        str(payload.get("player_id", "")),
        str(payload.get("priority", "media") or "media"),
        str(payload.get("note", "")),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo añadir al seguimiento."), 409, "shortlist_failed")
    _save(state)
    return _ok(
        {"result": result, "shortlist": shortlist_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.post("/shortlist/<player_id>")
def shortlist_update(player_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = update_shortlist_entry(
        state,
        player_id,
        str(payload.get("priority", "media") or "media"),
        str(payload.get("note", "")),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo actualizar el seguimiento."), 409, "shortlist_failed")
    _save(state)
    return _ok(
        {"result": result, "shortlist": shortlist_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.delete("/shortlist/<player_id>")
def shortlist_remove(player_id: str):
    state, err = _state()
    if err:
        return err
    result = remove_from_shortlist(state, player_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo retirar del seguimiento."), 409, "shortlist_failed")
    _save(state)
    return _ok(
        {"result": result, "shortlist": shortlist_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.post("/market/list/<player_id>")
def market_list(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = list_player_for_transfer(
        state,
        player_id,
        bool(payload.get("listed", True)),
        int(payload.get("asking_price", 0) or 0),
    )
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo actualizar."), 409, "list_failed")


@api.post("/market/staff/hire")
def market_staff_hire():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    candidate_id = str(payload.get("candidate_id", ""))
    result = hire_market_staff(state, candidate_id)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo contratar."), 409, "hire_failed")


@api.post("/market/offer/<player_id>")
def market_offer(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        fee = int(payload.get("fee", 0) or 0)
        salary = int(payload.get("salary", 0) or 0)
        years = int(payload.get("years", 3) or 3)
    except (TypeError, ValueError):
        return _error("Oferta no válida.", 400, "invalid_offer")
    result = make_transfer_offer(state, player_id, fee, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok(
        {"result": result, "state": _state_payload(state) if result.get("ok") else None},
        result.get("message", ""),
    ) if result.get("ok") else _error(result.get("message", "Oferta rechazada."), 409, "offer_rejected")


@api.post("/market/negotiate/<player_id>")
def market_negotiate(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        fee = int(payload.get("fee", 0) or 0)
        salary = int(payload.get("salary", 0) or 0)
        years = int(payload.get("years", 3) or 3)
    except (TypeError, ValueError):
        return _error("Oferta no válida.", 400, "invalid_negotiation")
    result = start_transfer_negotiation(state, player_id, fee, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok(
        {"result": result, "negotiation": result.get("negotiation"), "state": _state_payload(state) if result.get("ok") else None},
        result.get("message", ""),
    ) if result.get("ok") else _error(result.get("message", "No se pudo abrir la negociación."), 409, "negotiation_failed")


@api.post("/market/renew-negotiate/<player_id>")
def market_renew_negotiate(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        salary = int(payload.get("salary", 0) or 0)
        years = int(payload.get("years", 3) or 3)
    except (TypeError, ValueError):
        return _error("Contrato no válido.", 400, "invalid_negotiation")
    result = start_renewal_negotiation(state, player_id, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok(
        {"result": result, "negotiation": result.get("negotiation"), "state": _state_payload(state) if result.get("ok") else None},
        result.get("message", ""),
    ) if result.get("ok") else _error(result.get("message", "No se pudo abrir la renovación."), 409, "negotiation_failed")


@api.post("/market/negotiations/<negotiation_id>")
def market_negotiation_action(negotiation_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        fee = int(payload["fee"]) if payload.get("fee") not in (None, "") else None
        salary = int(payload["salary"]) if payload.get("salary") not in (None, "") else None
        years = int(payload["years"]) if payload.get("years") not in (None, "") else None
    except (TypeError, ValueError):
        return _error("Datos de negociación no válidos.", 400, "invalid_negotiation")
    result = respond_negotiation(state, negotiation_id, str(payload.get("action", "counter")), fee, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok(
        {"result": result, "negotiation": result.get("negotiation"), "state": _state_payload(state) if result.get("ok") else None},
        result.get("message", ""),
    ) if result.get("ok") else _error(result.get("message", "No se pudo continuar la negociación."), 409, "negotiation_failed")


@api.post("/market/offers/<offer_id>/counter")
def market_offer_counter(offer_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        fee = int(payload.get("fee", 0) or 0)
        salary = int(payload["salary"]) if payload.get("salary") not in (None, "") else None
        years = int(payload["years"]) if payload.get("years") not in (None, "") else None
    except (TypeError, ValueError):
        return _error("Contraoferta no válida.", 400, "invalid_counter")
    result = counter_incoming_offer(state, offer_id, fee, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo enviar la contraoferta."), 409, "counter_failed")


@api.get("/market/offers")
def market_offers():
    state, err = _state()
    if err:
        return err
    offers = generate_incoming_offers(state)
    return _ok({"offers": offers, "state": _state_payload(state)})


@api.post("/market/offers/<offer_id>")
def market_offer_action(offer_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "reject")
    if action == "accept":
        result = accept_incoming_offer(state, offer_id)
    else:
        reject_incoming_offer(state, offer_id)
        result = {"ok": True, "message": "Oferta rechazada."}
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.get("/market/renew")
def market_renew():
    state, err = _state()
    if err:
        return err
    return _ok({"players": [_player(p, state.user_team) for p in sorted(state.user_team.players, key=lambda p: (p.contract_until, -p.overall))]})


@api.post("/market/renew/<player_id>")
def market_renew_player(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        salary = int(payload.get("salary", 0) or 0)
        years = int(payload.get("years", 3) or 3)
    except (TypeError, ValueError):
        return _error("Datos de contrato no válidos.", 400, "invalid_contract")
    result = renew_contract(state, player_id, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo renovar."), 409, "renew_rejected")


@api.get("/loans")
def loans():
    state, err = _state()
    if err:
        return err
    return _ok(loan_overview(state))


@api.post("/loans/in")
def loan_in():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = request_loan_in(
        state,
        str(payload.get("player_id", "")),
        int(payload.get("wage_share", 50) or 50),
        str(payload.get("playing_time", "rotacion") or "rotacion"),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo cerrar la cesión."), 409, "loan_in_failed")
    _save(state)
    return _ok({"result": result, "loans": loan_overview(state), "state": _state_payload(state)}, result.get("message", ""))


@api.post("/loans/out")
def loan_out():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = offer_loan_out(
        state,
        str(payload.get("player_id", "")),
        str(payload.get("club_id", "")),
        int(payload.get("wage_share", 50) or 50),
        str(payload.get("playing_time", "rotacion") or "rotacion"),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo ofrecer la cesión."), 409, "loan_out_failed")
    _save(state)
    return _ok({"result": result, "loans": loan_overview(state), "state": _state_payload(state)}, result.get("message", ""))
