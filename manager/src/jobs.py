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
from .models import GameState, TeamState

STATUS_LABELS = {
    "estable": "Estable",
    "observacion": "En observación",
    "peligro": "En peligro",
    "ultimatum": "Ultimátum",
}


def _position(state: GameState, team: TeamState) -> int:
    table = state.table()
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
    offers.sort(key=lambda offer: (offer["position"], offer["club_name"]))
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
        "history": list(reversed(state.job_offer_history[-12:])),
        "eligible_clubs": max(0, teams - 1),
    }


def generate_job_offers(state: GameState, force: bool = False) -> list[dict[str, Any]]:
    open_offers = [offer for offer in state.job_offers if offer.get("status") == "open"]
    if open_offers and not force:
        return [_offer_payload(state, offer) for offer in open_offers]
    user = state.user_team
    candidates = [
        team
        for team in state.teams.values()
        if team.league == state.competition and team.id != user.id and len(team.squad) >= 14
    ]
    if not candidates:
        return []
    candidates.sort(key=lambda team: (_position(state, team), team.board_confidence, team.name), reverse=True)
    rng = random.Random(state.seed * 9901 + int(state.round) * 17 + zlib.crc32(user.id.encode("utf-8")))
    selected = candidates[:2]
    offers: list[dict[str, Any]] = []
    for team in selected:
        offer_id = f"JOB-{state.season}-{state.round}-{team.id}"
        if any(offer.get("id") == offer_id for offer in state.job_offers):
            continue
        salary = int(max(25000, user.manager_rating * 900 + team.wage_budget * 0.04))
        years = 2 if team.club_tier >= 3 else 3
        expires = (date.fromisoformat(state.date) + timedelta(days=14)).isoformat()
        offer = {
            "id": offer_id,
            "club_id": team.id,
            "status": "open",
            "salary": salary,
            "years": years,
            "created": state.date,
            "expires": expires,
            "project": (
                "Proyecto de consolidación y cantera"
                if team.club_tier >= 3
                else "Proyecto ambicioso con refuerzos"
            ),
        }
        state.job_offers.append(offer)
        offers.append(offer)
        state.inbox.append(
            {
                "date": state.date,
                "from": "Representante",
                "subject": f"Oferta de {team.name}",
                "body": f"{team.name} quiere hablar contigo para su banquillo.",
            }
        )
    state.job_offers = state.job_offers[-30:]
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
    if new_team.league != state.competition:
        return {"ok": False, "message": "Solo se admiten cambios dentro de la misma liga en esta versión."}
    old_team = state.user_team
    state.club_id = new_team.id
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
