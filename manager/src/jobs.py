"""Ofertas de trabajo y seguridad del mánager.

Las ofertas se generan entre clubes de la misma liga para que el cambio de
equipo sea coherente con el calendario y la clasificación ya simulados. El
mánager puede aceptar o rechazar; al aceptar cambia de club y firma un nuevo
contrato. La seguridad se calcula con la confianza de la junta, la afición, la
posición y la forma reciente.
"""

from __future__ import annotations

import random
import zlib
from datetime import date, timedelta
from typing import Any

from .competitions import competition
from .managers import record_manager_change, replacement_manager
from .models import GameState, TeamState

STATUS_LABELS = {
    "estable": "Estable",
    "observacion": "En observación",
    "peligro": "En peligro",
    "ultimatum": "Ultimátum",
}


def _position(state: GameState, team: TeamState) -> int:
    if team.league == state.competition:
        table = state.table()
    else:
        table = sorted(
            [item for item in state.teams.values() if item.league == team.league],
            key=lambda item: (-item.points, -(item.goals_for - item.goals_against), -item.goals_for, item.name),
        )
    return next((index for index, item in enumerate(table, 1) if item.id == team.id), 0)


def _recent_form(state: GameState, team_id: str, limit: int = 5) -> list[str]:
    fixtures = [
        fixture
        for fixture in state.fixtures
        if fixture.played and team_id in (fixture.home_id, fixture.away_id)
    ]
    fixtures.sort(key=lambda fixture: (fixture.date, fixture.round))
    rows = []
    for fixture in fixtures[-limit:]:
        home = fixture.home_id == team_id
        gf = fixture.home_goals if home else fixture.away_goals
        ga = fixture.away_goals if home else fixture.home_goals
        rows.append("V" if gf > ga else ("E" if gf == ga else "D"))
    return rows


def _status(team: TeamState, position: int, teams: int) -> str:
    if team.board_confidence < 40:
        return "ultimatum"
    if team.board_confidence < 55 or (teams and position > max(1, teams - 3)):
        return "peligro"
    if team.board_confidence < 70:
        return "observacion"
    return "estable"


def _default_contract(state: GameState) -> dict[str, Any]:
    team = state.user_team
    start_year = int(state.season[:4])
    return {
        "club_id": team.id,
        "club_name": team.name,
        "salary": int(max(20000, team.wage_budget * 0.05)),
        "years": 2,
        "started": state.season,
        "until": f"{start_year + 2}-06-30",
    }


def _offer_payload(state: GameState, offer: dict[str, Any]) -> dict[str, Any]:
    team = state.teams.get(str(offer.get("club_id", "")))
    if team is None:
        return {}
    return {
        **offer,
        "club_name": team.name,
        "league": team.league,
        "league_name": competition(team.league).short_name,
        "position": _position(state, team),
        "budget": int(team.budget),
        "transfer_budget": int(team.transfer_budget),
        "wage_budget": int(team.wage_budget),
        "expectation": team.board_expectation or "Consolidar el proyecto",
        "board_confidence": team.board_confidence,
        "fan_confidence": team.fan_confidence,
        "squad_size": len(team.squad),
        "cross_league": bool(offer.get("cross_league", False)),
        "effective": str(offer.get("effective", "now")),
        "international": bool(competition(team.league).international),
    }


def job_security_overview(state: GameState) -> dict[str, Any]:
    team = state.user_team
    table = state.table()
    position = _position(state, team)
    teams = len(table)
    status = _status(team, position, teams)
    form = _recent_form(state, team.id)
    contract = state.manager_contract or _default_contract(state)
    offers = [
        _offer_payload(state, offer)
        for offer in state.job_offers
        if offer.get("status") == "open"
    ]
    offers = [offer for offer in offers if offer]
    offers.sort(key=lambda offer: (offer["cross_league"], offer["position"], offer["club_name"]))
    pending_job = {}
    if state.pending_job:
        pending_team = state.teams.get(str(state.pending_job.get("club_id", "")))
        if pending_team is not None:
            pending_job = {
                **state.pending_job,
                "club_name": pending_team.name,
                "league": pending_team.league,
                "league_name": competition(pending_team.league).short_name,
                "position": _position(state, pending_team),
            }
    return {
        "club": {
            "id": team.id,
            "name": team.name,
            "league": team.league,
            "league_name": competition(team.league).short_name,
            "position": position,
            "teams": teams,
            "board_confidence": team.board_confidence,
            "fan_confidence": team.fan_confidence,
            "manager_rating": team.manager_rating,
            "board_expectation": team.board_expectation,
            "board_patience": team.board_patience,
            "board_pressure": team.board_pressure,
            "budget": int(team.budget),
            "wage_budget": int(team.wage_budget),
        },
        "security": {
            "status": status,
            "status_label": STATUS_LABELS[status],
            "risk": max(0, min(100, 100 - team.board_confidence)),
            "form": " ".join(form) if form else "—",
            "form_points": sum(3 if result == "V" else (1 if result == "E" else 0) for result in form),
        },
        "contract": contract,
        "offers": offers,
        "pending_job": pending_job,
        "history": list(reversed(state.job_offer_history[-12:])),
        "eligible_clubs": max(0, teams - 1),
    }


def _make_offer(state: GameState, team: TeamState, cross_league: bool) -> dict[str, Any]:
    user = state.user_team
    prefix = "JOBX" if cross_league else "JOB"
    offer_id = f"{prefix}-{state.season}-{state.round}-{team.id}"
    salary = int(max(25000, user.manager_rating * 900 + team.wage_budget * 0.04))
    years = 2 if team.club_tier >= 3 else 3
    expires = (date.fromisoformat(state.date) + timedelta(days=14)).isoformat()
    return {
        "id": offer_id,
        "club_id": team.id,
        "status": "open",
        "salary": salary,
        "years": years,
        "created": state.date,
        "expires": expires,
        "cross_league": cross_league,
        "effective": "next_season" if cross_league else "now",
        "international": bool(competition(team.league).international),
        "project": (
            "Proyecto de consolidación y cantera"
            if team.club_tier >= 3
            else "Proyecto ambicioso con refuerzos"
        ),
    }


def _append_offer(state: GameState, offer: dict[str, Any], offers: list[dict[str, Any]]) -> bool:
    existing = next((item for item in state.job_offers if item.get("id") == offer["id"]), None)
    if existing is not None:
        if existing.get("status") == "open":
            return False
        state.job_offers.remove(existing)
    state.job_offers.append(offer)
    offers.append(offer)
    return True


def create_job_offer(state: GameState, team: TeamState, cross_league: bool) -> dict[str, Any] | None:
    """Crea una oferta concreta para un club (usada por vacantes)."""
    offer = _make_offer(state, team, cross_league)
    if any(item.get("id") == offer["id"] and item.get("status") == "open" for item in state.job_offers):
        return None
    state.job_offers.append(offer)
    state.job_offers = state.job_offers[-40:]
    state.inbox.append(
        {
            "date": state.date,
            "from": "Representante",
            "subject": f"Oferta de {team.name}",
            "body": f"{team.name} quiere hablar contigo para su banquillo.",
        }
    )
    state.inbox = state.inbox[-80:]
    return _offer_payload(state, offer)


def generate_job_offers(
    state: GameState,
    force: bool = False,
    include_cross_league: bool = True,
) -> list[dict[str, Any]]:
    open_offers = [offer for offer in state.job_offers if offer.get("status") == "open"]
    if open_offers and not force:
        return [_offer_payload(state, offer) for offer in open_offers]
    user = state.user_team
    offers: list[dict[str, Any]] = []
    same_league = [
        team
        for team in state.teams.values()
        if team.league == state.competition and team.id != user.id and len(team.squad) >= 14
    ]
    same_league.sort(key=lambda team: (_position(state, team), team.board_confidence, team.name), reverse=True)
    for team in same_league[:2]:
        offer = _make_offer(state, team, False)
        if not _append_offer(state, offer, offers):
            continue
        state.inbox.append(
            {
                "date": state.date,
                "from": "Representante",
                "subject": f"Oferta de {team.name}",
                "body": f"{team.name} quiere hablar contigo para su banquillo.",
            }
        )
    if include_cross_league and not state.pending_job and user.manager_rating >= 55:
        cross = [
            team
            for team in state.teams.values()
            if team.id != user.id
            and team.league != state.competition
            and team.country == state.country
            and competition(team.league).system in ("dha", "dhb_two_phase", "regional")
            and len(team.squad) >= 14
        ]
        cross.sort(
            key=lambda team: (competition(team.league).standard, _position(state, team), team.name),
            reverse=True,
        )
        international = [
            team
            for team in state.teams.values()
            if team.id != user.id
            and team.league != state.competition
            and competition(team.league).international
            and len(team.squad) >= 14
        ]
        international.sort(
            key=lambda team: (competition(team.league).standard, _position(state, team), team.name),
            reverse=True,
        )
        for team in cross[:2] + international[:2]:
            offer = _make_offer(state, team, True)
            if not _append_offer(state, offer, offers):
                continue
            state.inbox.append(
                {
                    "date": state.date,
                    "from": "Representante",
                    "subject": f"Oferta de {team.name} para la próxima temporada",
                    "body": f"{team.name} quiere firmarte para la próxima temporada.",
                }
            )
    state.job_offers = state.job_offers[-40:]
    state.inbox = state.inbox[-80:]
    return [_offer_payload(state, offer) for offer in offers]


def accept_job_offer(state: GameState, offer_id: str) -> dict[str, Any]:
    offer = next((item for item in state.job_offers if item.get("id") == offer_id), None)
    if offer is None:
        return {"ok": False, "message": "La oferta no existe."}
    if offer.get("status") != "open":
        return {"ok": False, "message": "La oferta ya no está disponible."}
    new_team = state.teams.get(str(offer.get("club_id", "")))
    if new_team is None:
        return {"ok": False, "message": "El club de la oferta no existe."}
    if offer.get("cross_league"):
        if new_team.league == state.competition:
            return {"ok": False, "message": "La oferta ya no es un cambio de liga."}
        new_meta = competition(new_team.league)
        if not new_meta.international and new_meta.system not in ("dha", "dhb_two_phase", "regional"):
            return {"ok": False, "message": "Ese cambio de liga no está soportado."}
        if state.pending_job:
            return {"ok": False, "message": "Ya tienes un acuerdo para la próxima temporada."}
        next_year = int(state.season[:4]) + 1
        state.pending_job = {
            **offer,
            "status": "accepted_pending",
            "accepted": state.date,
            "effective_season": f"{next_year}-{str(next_year + 1)[-2:]}",
        }
        for item in state.job_offers:
            if item.get("id") == offer_id:
                item["status"] = "accepted_pending"
            elif item.get("status") == "open":
                item["status"] = "withdrawn"
        state.job_offer_history.append(
            {
                "date": state.date,
                "type": "accepted_pending",
                "offer_id": offer_id,
                "from_club": state.user_team.name,
                "to_club": new_team.name,
                "league": new_team.league,
                "salary": int(offer.get("salary", 0)),
                "years": int(offer.get("years", 2)),
                "message": f"Acuerdo con {new_team.name} para la temporada {state.pending_job['effective_season']}.",
            }
        )
        state.job_offer_history = state.job_offer_history[-40:]
        state.inbox.append(
            {
                "date": state.date,
                "from": "Representante",
                "subject": f"Acuerdo con {new_team.name}",
                "body": f"Dirigirás a {new_team.name} en la temporada {state.pending_job['effective_season']}.",
            }
        )
        state.inbox = state.inbox[-80:]
        return {
            "ok": True,
            "pending": True,
            "message": f"Acuerdo con {new_team.name} para la próxima temporada.",
            "new_club": new_team.name,
            "pending_job": state.pending_job,
            "job_security": job_security_overview(state),
        }
    if new_team.league != state.competition:
        return {"ok": False, "message": "Solo se admiten cambios dentro de la misma liga de forma inmediata."}
    old_team = state.user_team
    old_manager = old_team.manager_name
    old_team.manager_name = replacement_manager(old_team)
    old_team.manager_pressure = 0
    old_team.manager_since_round = state.round
    record_manager_change(
        state,
        old_team,
        old_manager,
        old_team.manager_name,
        "user_left",
        "El mánager acepta otro banquillo.",
    )
    new_old_manager = new_team.manager_name
    state.club_id = new_team.id
    new_team.manager_name = state.manager_name
    new_team.manager_pressure = 0
    new_team.manager_since_round = state.round
    record_manager_change(
        state,
        new_team,
        new_old_manager,
        state.manager_name,
        "user_hired",
        "Nuevo mánager al frente del club.",
    )
    state.manager_contract = {
        "club_id": new_team.id,
        "club_name": new_team.name,
        "salary": int(offer.get("salary", 0)),
        "years": int(offer.get("years", 2)),
        "started": state.date,
        "until": f"{int(state.date[:4]) + int(offer.get('years', 2))}-06-30",
    }
    for item in state.job_offers:
        if item.get("id") == offer_id:
            item["status"] = "accepted"
        elif item.get("status") == "open":
            item["status"] = "withdrawn"
    state.job_offer_history.append(
        {
            "date": state.date,
            "type": "accepted",
            "offer_id": offer_id,
            "from_club": old_team.name,
            "to_club": new_team.name,
            "league": state.competition,
            "salary": state.manager_contract["salary"],
            "years": state.manager_contract["years"],
            "message": f"Has aceptado el banquillo de {new_team.name}.",
        }
    )
    state.job_offer_history = state.job_offer_history[-40:]
    state.manual_lineup = []
    state.weekly_plan = []
    state.training_report = {}
    state.week_trained = False
    state.last_result = {}
    state.transfer_offers = []
    state.negotiations = []
    state.inbox.append(
        {
            "date": state.date,
            "from": "Junta directiva",
            "subject": f"Bienvenido a {new_team.name}",
            "body": f"Firmas como mánager de {new_team.name} hasta {state.manager_contract['until']}.",
        }
    )
    state.inbox = state.inbox[-80:]
    return {
        "ok": True,
        "message": f"Has aceptado el banquillo de {new_team.name}.",
        "old_club": old_team.name,
        "new_club": new_team.name,
        "contract": state.manager_contract,
        "job_security": job_security_overview(state),
    }


def reject_job_offer(state: GameState, offer_id: str) -> dict[str, Any]:
    offer = next((item for item in state.job_offers if item.get("id") == offer_id), None)
    if offer is None:
        return {"ok": False, "message": "La oferta no existe."}
    if offer.get("status") != "open":
        return {"ok": False, "message": "La oferta ya no está disponible."}
    team = state.teams.get(str(offer.get("club_id", "")))
    offer["status"] = "rejected"
    state.job_offer_history.append(
        {
            "date": state.date,
            "type": "rejected",
            "offer_id": offer_id,
            "from_club": state.user_team.name,
            "to_club": team.name if team else offer.get("club_id", ""),
            "league": state.competition,
            "salary": int(offer.get("salary", 0)),
            "years": int(offer.get("years", 2)),
            "message": f"Has rechazado la oferta de {team.name if team else 'el club'}.",
        }
    )
    state.job_offer_history = state.job_offer_history[-40:]
    return {"ok": True, "message": f"Has rechazado la oferta de {team.name if team else 'el club'}."}
