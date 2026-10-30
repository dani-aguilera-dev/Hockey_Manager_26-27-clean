"""Vacantes de entrenador y candidaturas.

El mercado de entrenadores muestra clubes con el banquillo en dificultades o
vacante. El mánager puede presentar su candidatura; si el club acepta, se crea
una oferta reutilizando el flujo de trabajo existente. No cambia de club
directamente.
"""

from __future__ import annotations

import random
import zlib
from datetime import date
from typing import Any

from .competitions import competition
from .jobs import create_job_offer
from .managers import manager_changes_overview
from .models import GameState, TeamState


def _league_table(state: GameState, league: str) -> list[TeamState]:
    return sorted(
        [team for team in state.teams.values() if team.league == league],
        key=lambda team: (-team.points, -(team.goals_for - team.goals_against), -team.goals_for, team.name),
    )


def _position(state: GameState, team: TeamState) -> tuple[int, int]:
    table = _league_table(state, team.league)
    position = next((index for index, item in enumerate(table, 1) if item.id == team.id), 0)
    return position, len(table)


def _interest(state: GameState, team: TeamState) -> float:
    user = state.user_team
    meta = competition(team.league)
    chance = 0.18 + (user.manager_rating - 50) / 200 + (user.manager_rating - meta.standard) / 300
    chance += (user.board_confidence - 50) / 500
    if team.league == state.competition:
        chance += 0.05
    if team.board_confidence < 30:
        chance += 0.08
    return round(max(0.05, min(0.90, chance)), 3)


def _application_status(state: GameState, club_id: str) -> str:
    rows = [item for item in state.vacancy_applications if item.get("club_id") == club_id]
    if not rows:
        return ""
    return str(rows[-1].get("status", ""))


def _vacancy_row(state: GameState, team: TeamState) -> dict[str, Any]:
    position, teams = _position(state, team)
    meta = competition(team.league)
    status = _application_status(state, team.id)
    return {
        "id": f"VAC-{state.season}-{state.round}-{team.id}",
        "club_id": team.id,
        "club_name": team.name,
        "league": team.league,
        "league_name": meta.short_name,
        "position": position,
        "teams": teams,
        "budget": int(team.budget),
        "transfer_budget": int(team.transfer_budget),
        "wage_budget": int(team.wage_budget),
        "expectation": team.board_expectation or "Consolidar el proyecto",
        "board_confidence": team.board_confidence,
        "fan_confidence": team.fan_confidence,
        "manager_name": team.manager_name,
        "manager_since_round": team.manager_since_round,
        "standard": round(meta.standard, 1),
        "international": meta.international,
        "same_league": team.league == state.competition,
        "interest": _interest(state, team),
        "application_status": status,
    }


def vacancy_overview(state: GameState) -> dict[str, Any]:
    user = state.user_team
    open_offer_clubs = {
        offer.get("club_id") for offer in state.job_offers if offer.get("status") == "open"
    }
    rows = []
    for team in state.teams.values():
        if team.id == user.id or team.id in open_offer_clubs:
            continue
        if state.pending_job.get("club_id") == team.id:
            continue
        position, teams = _position(state, team)
        if (
            team.board_confidence >= 45
            and position < max(1, teams - 2)
            and team.manager_name != "Entrenador interino"
        ):
            continue
        rows.append(_vacancy_row(state, team))
    rows.sort(key=lambda row: (-row["standard"], row["position"], row["club_name"]))
    applications = []
    for item in reversed(state.vacancy_applications[-20:]):
        team = state.teams.get(str(item.get("club_id", "")))
        applications.append(
            {
                **item,
                "club_name": team.name if team else item.get("club_name", ""),
                "league_name": competition(team.league).short_name if team else "",
            }
        )
    return {
        "vacancies": rows[:12],
        "pool": rows,
        "applications": applications,
        "changes": manager_changes_overview(state),
        "summary": {
            "vacancies": len(rows),
            "applications": len(state.vacancy_applications),
            "offers": sum(1 for item in state.vacancy_applications if item.get("status") == "offer"),
            "changes": len(state.manager_changes),
        },
    }


def apply_vacancy(state: GameState, vacancy_id: str, rng: random.Random | None = None) -> dict[str, Any]:
    overview = vacancy_overview(state)
    vacancy = next((row for row in overview["vacancies"] if row["id"] == vacancy_id), None)
    if vacancy is None:
        return {"ok": False, "message": "La vacante ya no está disponible."}
    team = state.teams.get(str(vacancy["club_id"]))
    if team is None:
        return {"ok": False, "message": "El club de la vacante no existe."}
    previous = _application_status(state, team.id)
    if previous == "offer":
        return {"ok": False, "message": "Ya tienes una oferta de ese club."}
    chance = float(vacancy["interest"])
    rng = rng or random.Random(
        state.seed * 9601
        + int(state.round) * 23
        + zlib.crc32(vacancy_id.encode("utf-8"))
    )
    accepted = rng.random() < chance
    application = {
        "date": state.date,
        "vacancy_id": vacancy_id,
        "club_id": team.id,
        "club_name": team.name,
        "league": team.league,
        "chance": chance,
        "status": "offer" if accepted else "rejected",
        "offer_id": "",
        "message": "",
    }
    if accepted:
        cross = team.league != state.competition
        offer = create_job_offer(state, team, cross)
        if offer is None:
            return {"ok": False, "message": "Ese club ya tiene una oferta abierta."}
        application["offer_id"] = offer["id"]
        application["message"] = f"{team.name} acepta tu candidatura y abre una oferta."
    else:
        application["message"] = f"{team.name} descarta tu candidatura por ahora."
    state.vacancy_applications.append(application)
    state.vacancy_applications = state.vacancy_applications[-60:]
    state.inbox.append(
        {
            "date": state.date,
            "from": "Mercado de entrenadores",
            "subject": f"Candidatura: {team.name}",
            "body": application["message"],
        }
    )
    state.inbox = state.inbox[-80:]
    return {
        "ok": True,
        "accepted": accepted,
        "message": application["message"],
        "application": application,
        "vacancy": vacancy,
        "offer": offer if accepted else None,
        "vacancies": vacancy_overview(state),
    }
