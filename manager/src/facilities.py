"""Instalaciones del club: estado, capacidad y mejoras."""

from __future__ import annotations

import random
from typing import Any

from .board import board_overview, request_board
from .models import GameState

FACILITY_INFO: dict[str, dict[str, str]] = {
    "training": {"label": "Entrenamiento", "description": "Campos, gimnasio y espacios de recuperación."},
    "youth": {"label": "Cantera", "description": "Recursos y entrenadores de categorías inferiores."},
    "medical": {"label": "Servicios médicos", "description": "Fisioterapia, readaptación y prevención."},
    "video": {"label": "Videoanálisis", "description": "Cámaras y software para analizar partidos."},
    "scouting": {"label": "Ojeo", "description": "Red de seguimiento de jugadores."},
    "stadium": {"label": "Estadio", "description": "Aforo, servicios y experiencia de la grada."},
}


def _label(value: int) -> str:
    if value >= 80:
        return "Élite"
    if value >= 65:
        return "Alta"
    if value >= 50:
        return "Media"
    return "Baja"


def facilities_overview(state: GameState) -> dict[str, Any]:
    team = state.user_team
    board = board_overview(state)
    facilities = []
    for key, info in FACILITY_INFO.items():
        value = int(team.facilities.get(key, 50))
        facilities.append({**info, "id": key, "value": value, "level": _label(value)})
    upgrades = [
        request
        for request in board["requests"]
        if request.get("facility") in FACILITY_INFO
    ]
    history = [
        entry
        for entry in board["history"]
        if entry.get("request_id") in {request["id"] for request in upgrades}
    ]
    values = [item["value"] for item in facilities]
    return {
        "facilities": facilities,
        "stadium": {"name": team.stadium_name, "capacity": team.stadium_capacity},
        "academy_rating": team.academy_rating,
        "summary": {
            "average": round(sum(values) / len(values), 1) if values else 0,
            "lowest": min(values) if values else 0,
            "highest": max(values) if values else 0,
            "capacity": team.stadium_capacity,
            "upgrades": len(history),
        },
        "upgrades": upgrades,
        "history": history,
    }


def upgrade_facility(state: GameState, request_id: str, rng: random.Random | None = None) -> dict[str, Any]:
    result = request_board(state, request_id, rng=rng)
    if not result.get("ok"):
        return result
    return {**result, "facilities": facilities_overview(state)}
