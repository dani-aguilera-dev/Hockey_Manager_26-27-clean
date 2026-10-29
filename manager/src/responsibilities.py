"""Responsabilidades del cuerpo técnico.

Cada área del club puede tener un responsable. Su valoración modula la
calidad de las sesiones de entrenamiento y se guarda en la partida.
"""

from __future__ import annotations

from typing import Any

from .models import GameState, TeamState

AREAS: dict[str, dict[str, str]] = {
    "training": {"label": "Entrenamiento general", "description": "Coordinación del plan semanal y del grupo.", "session": "general"},
    "attack": {"label": "Ataque", "description": "Sesiones ofensivas, definición y creación.", "session": "ataque"},
    "defense": {"label": "Defensa", "description": "Organización defensiva, presión y coberturas.", "session": "defensa"},
    "fitness": {"label": "Preparación física", "description": "Carga, recuperación y prevención de lesiones.", "session": "fisico"},
    "set_pieces": {"label": "Balón parado", "description": "Penalty corners, strokes y golpes francos.", "session": "set_pieces"},
    "goalkeeping": {"label": "Porteros", "description": "Entrenamiento específico de porteros.", "session": "porteros"},
    "scouting": {"label": "Ojeo", "description": "Cobertura de mercado y filtrado de objetivos.", "session": "scouting"},
    "medical": {"label": "Servicios médicos", "description": "Recuperación, readaptación y prevención.", "session": "medical"},
    "analysis": {"label": "Análisis del rival", "description": "Vídeo, informes y preparación de partido.", "session": "video"},
    "youth": {"label": "Cantera", "description": "Desarrollo y promoción de jóvenes.", "session": "youth"},
}


def _staff_member(team: TeamState, name: str):
    return next((member for member in team.staff if member.name == name), None)


def responsibility_bonus(team: TeamState, area: str) -> float:
    member = _staff_member(team, team.staff_assignments.get(area, ""))
    if member is None:
        return 0.0
    return round(max(0.0, min(1.0, (float(member.rating) - 45.0) / 50.0)), 3)


def responsibilities_overview(state: GameState) -> dict[str, Any]:
    team = state.user_team
    staff = sorted(team.staff, key=lambda member: (-member.rating, member.name))
    rows = []
    for area, meta in AREAS.items():
        assigned = _staff_member(team, team.staff_assignments.get(area, ""))
        rows.append(
            {
                "id": area,
                **meta,
                "staff_name": assigned.name if assigned else "",
                "staff_role": assigned.role if assigned else "",
                "staff_rating": assigned.rating if assigned else None,
                "bonus": responsibility_bonus(team, area),
                "options": [
                    {"name": member.name, "role": member.role, "rating": member.rating}
                    for member in staff
                ],
            }
        )
    return {
        "areas": rows,
        "assigned": sum(1 for row in rows if row["staff_name"]),
        "total": len(rows),
        "staff": [
            {"name": member.name, "role": member.role, "rating": member.rating, "salary": member.salary}
            for member in staff
        ],
    }


def set_responsibility(state: GameState, area: str, staff_name: str) -> dict[str, Any]:
    team = state.user_team
    if area not in AREAS:
        return {"ok": False, "message": "El área no es válida."}
    if not staff_name:
        team.staff_assignments.pop(area, None)
        return {"ok": True, "message": f"{AREAS[area]['label']}: responsable retirado."}
    member = _staff_member(team, staff_name)
    if member is None:
        return {"ok": False, "message": "Ese miembro del staff no está en el club."}
    team.staff_assignments[area] = member.name
    return {
        "ok": True,
        "message": f"{member.name} asume {AREAS[area]['label'].lower()}.",
        "area": area,
        "staff_name": member.name,
        "bonus": responsibility_bonus(team, area),
    }
