"""Junta directiva, visión de club e instalaciones.

La junta no es un adorno: aprueba o rechaza peticiones según la confianza, la
caja disponible y el tipo de inversión. Cada petición queda registrada y las
mejoras se guardan en la partida.
"""

from __future__ import annotations

import random
import zlib
from datetime import date
from typing import Any

from .competitions import competition
from .models import GameState, TeamState

FACILITY_LABELS: dict[str, str] = {
    "training": "Entrenamiento",
    "youth": "Cantera",
    "medical": "Servicios médicos",
    "video": "Videoanálisis",
    "scouting": "Ojeo",
    "stadium": "Estadio",
}

REQUESTS: tuple[dict[str, Any], ...] = (
    {
        "id": "training",
        "label": "Mejorar las instalaciones de entrenamiento",
        "description": "Nuevo material, gimnasio y espacios de recuperación para el primer equipo.",
        "base_cost": 120000,
        "facility": "training",
        "delta": 6,
        "confidence": 2,
    },
    {
        "id": "youth",
        "label": "Impulsar la cantera",
        "description": "Más entrenadores y recursos para las categorías inferiores.",
        "base_cost": 90000,
        "facility": "youth",
        "delta": 6,
        "confidence": 1,
    },
    {
        "id": "medical",
        "label": "Ampliar el equipo médico",
        "description": "Fisioterapia, readaptación y prevención de lesiones.",
        "base_cost": 80000,
        "facility": "medical",
        "delta": 6,
        "confidence": 1,
    },
    {
        "id": "video",
        "label": "Instalar videoanálisis",
        "description": "Cámaras y software para analizar partidos y rivales.",
        "base_cost": 70000,
        "facility": "video",
        "delta": 6,
        "confidence": 1,
    },
    {
        "id": "scouting",
        "label": "Ampliar la red de ojeadores",
        "description": "Más cobertura nacional e internacional para detectar talento.",
        "base_cost": 60000,
        "facility": "scouting",
        "delta": 6,
        "confidence": 1,
    },
    {
        "id": "stadium",
        "label": "Ampliar el estadio",
        "description": "Nuevas gradas y servicios para aumentar el aforo y la taquilla.",
        "base_cost": 250000,
        "facility": "stadium",
        "delta": 5,
        "confidence": 2,
        "capacity": 500,
    },
    {
        "id": "budget",
        "label": "Ampliar el presupuesto de fichajes",
        "description": "La junta libera fondos extraordinarios para reforzar la plantilla.",
        "base_cost": 0,
        "budget_gain": 150000,
        "confidence": 1,
    },
)


def _factor(team: TeamState) -> float:
    meta = competition(team.league)
    return 0.6 + meta.standard / 100


def _request_cost(team: TeamState, request: dict[str, Any]) -> int:
    return int(int(request.get("base_cost", 0)) * _factor(team))


def _request_gain(team: TeamState, request: dict[str, Any]) -> int:
    return int(int(request.get("budget_gain", 0)) * _factor(team))


def _approval_chance(team: TeamState, request: dict[str, Any], cost: int) -> float:
    chance = 0.35 + (team.board_confidence - 50) / 150 + (team.fan_confidence - 50) / 300
    chance -= cost / max(1, team.budget) * 0.25
    if request.get("id") == "budget":
        chance -= 0.15
    if request.get("facility") == "stadium":
        chance -= 0.08
    return max(0.08, min(0.92, chance))


def _effect_text(team: TeamState, request: dict[str, Any]) -> str:
    facility = request.get("facility")
    if facility == "stadium":
        return f"Aforo +{int(request.get('capacity', 500))} y estadio +{int(request.get('delta', 0))}"
    if facility:
        return f"{FACILITY_LABELS.get(facility, facility)} +{int(request.get('delta', 0))}"
    gain = _request_gain(team, request)
    return f"Presupuesto de fichajes +{gain:,}".replace(",", ".")


def _vision(team: TeamState) -> list[dict[str, str]]:
    meta = competition(team.league)
    if meta.standard >= 72:
        short = "Competir en la zona alta y pelear por Europa"
    elif meta.standard >= 60:
        short = "Consolidarse y pelear por el ascenso"
    else:
        short = "Ascender y construir un proyecto sostenible"
    return [
        {
            "horizon": "Corto plazo",
            "goal": team.board_expectation or short,
            "detail": f"Objetivo de la temporada en {meta.short_name}",
        },
        {
            "horizon": "Medio plazo",
            "goal": "Consolidar la estructura deportiva",
            "detail": "Cantera, staff y estabilidad financiera",
        },
        {
            "horizon": "Largo plazo",
            "goal": "Instalaciones y marca de club",
            "detail": "Crecimiento sostenible y presencia internacional",
        },
    ]


def _position(state: GameState, team: TeamState) -> tuple[int, int]:
    if state.competition == team.league:
        table = state.table()
    else:
        table = sorted(
            [item for item in state.teams.values() if item.league == team.league],
            key=lambda item: (-item.points, -(item.goals_for - item.goals_against), -item.goals_for, item.name),
        )
    position = next((index for index, item in enumerate(table, 1) if item.id == team.id), 0)
    return position, len(table)


def board_overview(state: GameState) -> dict[str, Any]:
    team = state.user_team
    meta = competition(team.league)
    position, teams = _position(state, team)
    requests = []
    for request in REQUESTS:
        cost = _request_cost(team, request)
        requests.append(
            {
                **request,
                "cost": cost,
                "approval_chance": round(_approval_chance(team, request, cost), 3),
                "available": cost <= team.budget,
                "effect_text": _effect_text(team, request),
            }
        )
    return {
        "confidence": team.board_confidence,
        "fan_confidence": team.fan_confidence,
        "patience": team.board_patience,
        "pressure": team.board_pressure,
        "expectation": team.board_expectation,
        "manager_rating": team.manager_rating,
        "budget": team.budget,
        "transfer_budget": team.transfer_budget,
        "competition": {
            "code": meta.code,
            "name": meta.name,
            "short_name": meta.short_name,
            "position": position,
            "teams": teams,
        },
        "stadium": {"name": team.stadium_name, "capacity": team.stadium_capacity},
        "board_members": [member.to_dict() for member in team.board],
        "vision": _vision(team),
        "facilities": [
            {"id": key, "label": FACILITY_LABELS.get(key, key), "value": int(team.facilities.get(key, 50))}
            for key in ("training", "youth", "medical", "video", "scouting", "stadium")
        ],
        "requests": requests,
        "history": list(reversed(team.board_requests[-10:])),
    }


def request_board(
    state: GameState, request_id: str, rng: random.Random | None = None
) -> dict[str, Any]:
    team = state.user_team
    request = next((item for item in REQUESTS if item["id"] == request_id), None)
    if request is None:
        return {"ok": False, "message": "La petición no existe."}
    cost = _request_cost(team, request)
    if cost > team.budget:
        return {
            "ok": False,
            "message": f"La caja actual no permite esta inversión: faltan {cost - team.budget:,} €.".replace(",", "."),
        }
    chance = _approval_chance(team, request, cost)
    if rng is None:
        rng = random.Random(
            state.seed * 9101
            + date.fromisoformat(state.date).toordinal()
            + zlib.crc32(request_id.encode("utf-8"))
        )
    approved = rng.random() < chance
    before = {
        "budget": team.budget,
        "transfer_budget": team.transfer_budget,
        "confidence": team.board_confidence,
        "facility": team.facilities.get(request.get("facility", ""), None),
        "capacity": team.stadium_capacity,
    }
    if approved:
        team.budget -= cost
        facility = request.get("facility")
        if facility:
            team.facilities[facility] = min(99, int(team.facilities.get(facility, 50)) + int(request.get("delta", 0)))
        if facility == "youth":
            team.academy_rating = min(95, team.academy_rating + 4)
        if facility == "stadium":
            team.stadium_capacity += int(request.get("capacity", 500))
        gain = _request_gain(team, request)
        if gain:
            team.transfer_budget += gain
        team.board_confidence = min(100, team.board_confidence + int(request.get("confidence", 1)))
        message = f"La junta aprueba: {request['label'].lower()}."
    else:
        team.board_confidence = max(0, team.board_confidence - 1)
        message = f"La junta rechaza por ahora: {request['label'].lower()}."
    entry = {
        "date": state.date,
        "request_id": request_id,
        "label": request["label"],
        "cost": cost,
        "approved": approved,
        "chance": round(chance, 3),
        "message": message,
        "before": before,
        "after": {
            "budget": team.budget,
            "transfer_budget": team.transfer_budget,
            "confidence": team.board_confidence,
            "facility": team.facilities.get(request.get("facility", ""), None),
            "capacity": team.stadium_capacity,
        },
    }
    team.board_requests.append(entry)
    team.board_requests = team.board_requests[-30:]
    state.inbox.append(
        {
            "date": state.date,
            "from": "Junta directiva",
            "subject": request["label"],
            "body": message,
        }
    )
    state.inbox = state.inbox[-80:]
    return {"ok": True, "approved": approved, "message": message, "entry": entry}
