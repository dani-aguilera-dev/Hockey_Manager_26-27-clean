"""Planes de desarrollo individual por jugador.

El plan semanal se suma al entrenamiento colectivo: enfoca atributos,
modula la intensidad y registra el progreso. Los jóvenes de la cantera también
pueden tener plan.
"""

from __future__ import annotations

import random
import zlib
from datetime import date
from typing import Any

from .models import GameState, PlayerState

FOCUS_OPTIONS: dict[str, dict[str, Any]] = {
    "tecnica": {"label": "Técnica", "attributes": ["control", "pase", "conduccion", "golpeo", "flick"]},
    "fisico": {"label": "Físico", "attributes": ["velocidad", "resistencia", "fuerza", "agilidad", "coordinacion"]},
    "mental": {"label": "Mental", "attributes": ["decisiones", "concentracion", "competitividad", "liderazgo"]},
    "definicion": {"label": "Definición", "attributes": ["definicion", "pc_flick", "stroke_shot", "desmarque"]},
    "portero": {"label": "Portero", "attributes": ["reflejos", "blocaje", "distribucion", "uno_vs_uno", "pc_gk_save", "stroke_save"]},
    "polivalencia": {"label": "Polivalencia", "attributes": ["posicionamiento", "cobertura", "transicion", "pase"]},
}

INTENSITY_OPTIONS: dict[str, dict[str, Any]] = {
    "suave": {"label": "Suave", "progress": 8, "gain": 0.6, "fatigue": 0.4},
    "normal": {"label": "Normal", "progress": 12, "gain": 1.0, "fatigue": 1.0},
    "intensa": {"label": "Intensa", "progress": 18, "gain": 1.35, "fatigue": 2.2},
}


def _pool(team) -> list[PlayerState]:
    return list(team.squad) + list(team.youth)


def _find(team, player_id: str) -> PlayerState | None:
    return next((player for player in _pool(team) if player.id == player_id), None)


def _plan_payload(player: PlayerState) -> dict[str, Any]:
    plan = dict(player.development_plan or {})
    focus = plan.get("focus", "")
    intensity = plan.get("intensity", "")
    return {
        "player_id": player.id,
        "name": player.name,
        "age": player.age,
        "position": player.subposition,
        "overall": round(float(player.overall), 1),
        "potential": round(float(player.potential), 1),
        "category": player.youth_category,
        "is_youth": player.perfil == "Canterano",
        "focus": focus,
        "focus_label": FOCUS_OPTIONS.get(focus, {}).get("label", ""),
        "intensity": intensity,
        "intensity_label": INTENSITY_OPTIONS.get(intensity, {}).get("label", ""),
        "notes": plan.get("notes", ""),
        "since": plan.get("since", ""),
        "sessions": int(plan.get("sessions", 0) or 0),
        "progress": int(plan.get("progress", 0) or 0),
        "last_gain": plan.get("last_gain", ""),
    }


def development_overview(state: GameState) -> dict[str, Any]:
    team = state.user_team
    rows = [_plan_payload(player) for player in _pool(team)]
    active = [row for row in rows if row["focus"]]
    return {
        "players": rows,
        "active": len(active),
        "youth_active": sum(1 for row in active if row["is_youth"]),
        "average_progress": round(sum(row["progress"] for row in active) / len(active), 1) if active else 0.0,
        "focuses": [{"id": key, **value} for key, value in FOCUS_OPTIONS.items()],
        "intensities": [{"id": key, **value} for key, value in INTENSITY_OPTIONS.items()],
    }


def set_development_plan(
    state: GameState,
    player_id: str,
    focus: str,
    intensity: str = "normal",
    notes: str = "",
) -> dict[str, Any]:
    team = state.user_team
    player = _find(team, player_id)
    if player is None:
        return {"ok": False, "message": "El jugador no está en tu plantilla o cantera."}
    if focus not in FOCUS_OPTIONS:
        return {"ok": False, "message": "El enfoque no es válido."}
    if intensity not in INTENSITY_OPTIONS:
        return {"ok": False, "message": "La intensidad no es válida."}
    previous = player.development_plan or {}
    reset = previous.get("focus") != focus
    player.development_plan = {
        "focus": focus,
        "intensity": intensity,
        "notes": notes[:160],
        "since": previous.get("since", state.date) if not reset else state.date,
        "sessions": 0 if reset else int(previous.get("sessions", 0) or 0),
        "progress": 0 if reset else int(previous.get("progress", 0) or 0),
        "last_gain": "" if reset else previous.get("last_gain", ""),
    }
    return {"ok": True, "message": f"Plan de desarrollo asignado a {player.name}.", "plan": _plan_payload(player)}


def clear_development_plan(state: GameState, player_id: str) -> dict[str, Any]:
    player = _find(state.user_team, player_id)
    if player is None:
        return {"ok": False, "message": "El jugador no está en tu plantilla o cantera."}
    player.development_plan = {}
    return {"ok": True, "message": f"Plan de desarrollo retirado a {player.name}."}


def advance_development(state: GameState) -> dict[str, Any]:
    """Avanza una semana de planes individuales y aplica mejoras cada 4 sesiones."""
    team = state.user_team
    gains: list[dict[str, Any]] = []
    for player in _pool(team):
        plan = player.development_plan or {}
        if not plan:
            continue
        focus = str(plan.get("focus", ""))
        intensity = str(plan.get("intensity", "normal"))
        if focus not in FOCUS_OPTIONS or intensity not in INTENSITY_OPTIONS:
            continue
        profile = INTENSITY_OPTIONS[intensity]
        plan["sessions"] = int(plan.get("sessions", 0) or 0) + 1
        plan["progress"] = min(100, int(plan.get("progress", 0) or 0) + int(profile["progress"]))
        player.fatigue = min(100.0, player.fatigue + float(profile["fatigue"]))
        if plan["sessions"] % 4 == 0:
            rng = random.Random(state.seed + zlib.crc32(player.id.encode("utf-8")) + plan["sessions"])
            attrs = [attr for attr in FOCUS_OPTIONS[focus]["attributes"] if attr in player.attributes]
            if attrs:
                chosen = rng.sample(attrs, min(2, len(attrs)))
                for attr in chosen:
                    player.attributes[attr] = min(99, int(player.attributes[attr]) + 1)
                player.overall = round(min(player.potential, player.overall + 0.1 * float(profile["gain"])), 1)
                plan["last_gain"] = ", ".join(chosen)
                gains.append({"player": player.name, "attributes": chosen, "session": plan["sessions"]})
    return {"gains": gains, "active": sum(1 for player in _pool(team) if player.development_plan)}
