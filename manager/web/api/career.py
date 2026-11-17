"""API de career."""

from __future__ import annotations

from flask import Blueprint, request
from src.compare import compare_candidates, compare_players
from src.competitions import competition
from src.cup import cup_next_user_fixture, cup_round_fixtures, cup_status_text
from src.ehl import ehl_next_date, ehl_status_text, simulate_ehl_round
from src.jobs import accept_job_offer, generate_job_offers, job_security_overview, reject_job_offer
from src.manager_profile import manager_profile_overview
from src.managers import resign_user
from src.season import advance_to_next_season, season_summary, simulate_cup_remaining, simulate_cup_round
from src.vacancies import apply_vacancy, vacancy_overview
from web.api.common import (
    _error,
    _fixture,
    _ok,
    _promotion_payload,
    _save,
    _state,
    _state_payload,
)

api = Blueprint("api_career", __name__, url_prefix="/api")

@api.get("/vacancies")
def vacancies():
    state, err = _state()
    if err:
        return err
    return _ok(vacancy_overview(state))


@api.post("/vacancies/<vacancy_id>/apply")
def vacancies_apply(vacancy_id: str):
    state, err = _state()
    if err:
        return err
    result = apply_vacancy(state, vacancy_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo presentar la candidatura."), 409, "vacancy_failed")
    _save(state)
    return _ok(
        {"result": result, "vacancies": vacancy_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.post("/jobs/resign")
def jobs_resign():
    state, err = _state()
    if err:
        return err
    result = resign_user(state)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo presentar la dimisión."), 409, "resign_failed")
    _save(state)
    return _ok(
        {"result": result, "jobs": job_security_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/jobs")
def jobs():
    state, err = _state()
    if err:
        return err
    return _ok(job_security_overview(state))


@api.post("/jobs/offers")
def jobs_offers():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    generate_job_offers(
        state,
        bool(payload.get("force", False)),
        bool(payload.get("cross_league", True)),
    )
    _save(state)
    return _ok(
        {"jobs": job_security_overview(state), "state": _state_payload(state)},
        "Ofertas actualizadas.",
    )


@api.post("/jobs/offers/<offer_id>/accept")
def jobs_accept(offer_id: str):
    state, err = _state()
    if err:
        return err
    result = accept_job_offer(state, offer_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo aceptar la oferta."), 409, "job_offer_failed")
    _save(state)
    return _ok(
        {"result": result, "jobs": job_security_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.post("/jobs/offers/<offer_id>/reject")
def jobs_reject(offer_id: str):
    state, err = _state()
    if err:
        return err
    result = reject_job_offer(state, offer_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo rechazar la oferta."), 409, "job_offer_failed")
    _save(state)
    return _ok(
        {"result": result, "jobs": job_security_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/compare/players")
def compare_players_api():
    state, err = _state()
    if err:
        return err
    try:
        limit = max(1, min(80, int(request.args.get("limit", 30))))
    except (TypeError, ValueError):
        limit = 30
    return _ok({"players": compare_candidates(state, str(request.args.get("q", "")), limit)})


@api.get("/compare")
def compare_api():
    state, err = _state()
    if err:
        return err
    result = compare_players(
        state,
        str(request.args.get("player_a", "")),
        str(request.args.get("player_b", "")),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo comparar."), 409, "compare_failed")
    return _ok(result)


@api.get("/manager")
def manager_profile():
    state, err = _state()
    if err:
        return err
    return _ok(manager_profile_overview(state))


@api.get("/cup")
def cup():
    state, err = _state()
    if err:
        return err
    if competition(state.competition).system not in ("dha", "dhb_two_phase"):
        return _error("La Copa del Rey solo existe en las ligas españolas.", 400, "cup_unavailable")
    fixtures = [_fixture(f, state) for f in cup_round_fixtures(state)]
    nxt = cup_next_user_fixture(state)
    return _ok(
        {
            "status": cup_status_text(state),
            "active": state.cup_active,
            "round": state.cup_round,
            "fixtures": fixtures,
            "next": _fixture(nxt, state) if nxt else None,
        }
    )


@api.post("/cup")
def cup_action():
    state, err = _state()
    if err:
        return err
    if competition(state.competition).system not in ("dha", "dhb_two_phase"):
        return _error("La Copa del Rey solo existe en las ligas españolas.", 400, "cup_unavailable")
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "round")
    if action == "all":
        simulate_cup_remaining(state)
    else:
        simulate_cup_round(state, state.manual_lineup or None)
    _save(state)
    return _ok({"state": _state_payload(state)}, "Copa actualizada.")


@api.get("/ehl")
def ehl():
    state, err = _state()
    if err:
        return err
    if competition(state.competition).system not in ("dha", "dhb_two_phase"):
        return _error("La EHL se gestiona desde las ligas europeas españolas.", 400, "ehl_unavailable")
    return _ok({"ehl": state.ehl, "next": ehl_next_date(state), "status": ehl_status_text(state)})


@api.post("/ehl")
def ehl_action():
    state, err = _state()
    if err:
        return err
    if competition(state.competition).system not in ("dha", "dhb_two_phase"):
        return _error("La EHL se gestiona desde las ligas europeas españolas.", 400, "ehl_unavailable")
    if state.ehl.get("active"):
        simulate_ehl_round(state)
        _save(state)
    return _ok({"ehl": state.ehl, "next": ehl_next_date(state), "status": ehl_status_text(state), "state": _state_payload(state)}, "Ronda de EHL simulada.")


@api.get("/promotion")
def promotion():
    state, err = _state()
    if err:
        return err
    return _ok(_promotion_payload(state))


@api.get("/season/end")
def season_end():
    state, err = _state()
    if err:
        return err
    if state.phase != "season_end":
        return _error("La temporada todavía no ha terminado.", 409, "season_active")
    return _ok({"summary": season_summary(state), "state": _state_payload(state)})


@api.post("/season/continue")
def season_continue():
    state, err = _state()
    if err:
        return err
    if state.phase != "season_end":
        return _error("La temporada todavía no ha terminado.", 409, "season_active")
    advance_to_next_season(state)
    _save(state)
    return _ok(_state_payload(state), f"Nueva temporada: {state.season} · {state.competition}.")
