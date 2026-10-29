"""Reunión de equipo: charla, dinámica, promesas y efectos persistentes.

La reunión no es un botón decorativo: mueve moral, cohesión, confianza de la
junta y de la afición, relaciones individuales y puede dejar promesas que se
comprueban más adelante con `check_promises`.
"""

from __future__ import annotations

import random
import zlib
from datetime import date, timedelta
from typing import Any

from .models import GameState, PlayerState, TeamState

MEETING_TYPES: dict[str, dict[str, Any]] = {
    "pre_match": {"label": "Preparar el próximo partido", "description": "Mensaje de enfoque y plan para el siguiente compromiso."},
    "post_match": {"label": "Revisar el último partido", "description": "Análisis del resultado, el rendimiento y las incidencias."},
    "crisis": {"label": "Reunión de crisis", "description": "Recomponer el grupo cuando la moral o la cohesión están tocadas."},
    "season": {"label": "Revisar la temporada", "description": "Balance de objetivos, proyecto y relación con la junta."},
}

TONES: dict[str, dict[str, Any]] = {
    "motivadora": {"label": "Motivadora", "bonus": 0.04, "morale": 2, "fan": 1, "prep_bonus": 0.08},
    "exigente": {"label": "Exigente", "bonus": 0.02, "morale": -1, "board": 2, "prep_bonus": 0.12},
    "serena": {"label": "Serena", "bonus": 0.06, "morale": 1, "cohesion": 2, "board": 1},
    "honesta": {"label": "Honesta", "bonus": 0.03, "morale": 1, "relationship": 2, "board": 1},
}

TOPICS: dict[str, dict[str, Any]] = {
    "objetivo": {"label": "Objetivo de la temporada", "description": "Alinear al grupo con la meta de la junta.", "board": 1, "fan": 1},
    "vestuario": {"label": "Unidad del vestuario", "description": "Cuidar la cohesión y las relaciones internas.", "cohesion": 2, "relationship": 1},
    "minutos": {"label": "Reparto de minutos", "description": "Hablar claro sobre roles y oportunidades.", "morale": 1, "relationship": 1},
    "disciplina": {"label": "Disciplina y exigencia", "description": "Marcar normas y consecuencias.", "board": 2, "morale": -1},
    "aficion": {"label": "Relación con la afición", "description": "Conectar el equipo con la grada.", "fan": 2, "morale": 1},
    "proyecto": {"label": "Proyecto de club", "description": "Cantera, instalaciones y futuro compartido.", "board": 1, "cohesion": 1, "fan": 1},
}

PROMISE_TYPES: dict[str, dict[str, Any]] = {
    "minutes": {"label": "Prometer minutos", "days": 21, "apps": 3, "text": "Tendrás minutos en los próximos partidos."},
    "renewal": {"label": "Prometer renovación", "days": 30, "apps": 0, "text": "El club abrirá tu renovación."},
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _label(value: int, high: int, low: int) -> str:
    if value >= high:
        return "Alta"
    if value >= low:
        return "Estable"
    return "Baja"


def _dynamics(team: TeamState) -> dict[str, Any]:
    relationships = [player.relationship for player in team.players]
    avg_relationship = round(_avg([float(value) for value in relationships]), 1)
    warnings = []
    if team.morale < 8:
        warnings.append("La moral del grupo está baja; una reunión exigente puede empeorarla.")
    if team.cohesion < 8:
        warnings.append("La cohesión está rota; conviene priorizar el vestuario.")
    if team.board_confidence < 40:
        warnings.append("La junta está perdiendo la paciencia.")
    if team.fan_confidence < 40:
        warnings.append("La afición está desconectada del equipo.")
    open_promises = sum(1 for player in team.players for promise in player.promises if promise.get("status") == "open")
    if open_promises >= 3:
        warnings.append(f"Hay {open_promises} promesas abiertas; el grupo está pendiente de que se cumplan.")
    return {
        "morale": team.morale,
        "morale_label": _label(team.morale, 15, 9),
        "cohesion": team.cohesion,
        "cohesion_label": _label(team.cohesion, 15, 9),
        "board_confidence": team.board_confidence,
        "board_label": _label(team.board_confidence, 65, 40),
        "fan_confidence": team.fan_confidence,
        "fan_label": _label(team.fan_confidence, 65, 40),
        "avg_relationship": avg_relationship,
        "open_promises": open_promises,
        "warnings": warnings,
    }


def _fixture_payload(state: GameState) -> dict[str, Any] | None:
    fixture = state.next_user_fixture()
    if fixture is None:
        return None
    return {
        "id": fixture.id,
        "date": fixture.date,
        "round": fixture.round,
        "home_name": state.teams[fixture.home_id].name,
        "away_name": state.teams[fixture.away_id].name,
    }


def team_meeting_context(state: GameState) -> dict[str, Any]:
    team = state.user_team
    last = state.last_result or {}
    if team.morale < 8 or team.cohesion < 8:
        recommended = "crisis"
    elif last and last.get("date") == state.date:
        recommended = "post_match"
    elif state.phase == "season_end":
        recommended = "season"
    else:
        recommended = "pre_match"
    players = [
        {
            "id": player.id,
            "name": player.name,
            "age": player.age,
            "position": player.subposition,
            "overall": round(float(player.overall), 1),
            "relationship": player.relationship,
            "open_promises": sum(1 for promise in player.promises if promise.get("status") == "open"),
        }
        for player in sorted(team.squad, key=lambda item: (item.relationship, item.name))
    ]
    return {
        "team": {"id": team.id, "name": team.name},
        "dynamics": _dynamics(team),
        "next_fixture": _fixture_payload(state),
        "last_result": {
            "result": last.get("result"),
            "score": f"{last.get('home_goals', 0)}-{last.get('away_goals', 0)}",
            "rival": last.get("away_name") if last.get("user_is_home") else last.get("home_name"),
            "date": last.get("date"),
        }
        if last
        else None,
        "meeting_types": [{"id": key, **value} for key, value in MEETING_TYPES.items()],
        "tones": [{"id": key, **value} for key, value in TONES.items()],
        "topics": [{"id": key, **value} for key, value in TOPICS.items()],
        "promise_types": [{"id": key, **value} for key, value in PROMISE_TYPES.items()],
        "players": players,
        "recommended_type": recommended,
        "history": list(reversed(team.team_meetings[-10:])),
    }


def perform_team_meeting(
    state: GameState,
    meeting_type: str,
    tone: str,
    topics: list[str],
    promise_player_id: str = "",
    promise_type: str = "",
    rng: random.Random | None = None,
) -> dict[str, Any]:
    team = state.user_team
    if meeting_type not in MEETING_TYPES:
        return {"ok": False, "message": "El tipo de reunión no es válido."}
    if tone not in TONES:
        return {"ok": False, "message": "El tono de la reunión no es válido."}
    clean_topics = [item for item in dict.fromkeys(topics or []) if item in TOPICS]
    if len(clean_topics) > 3:
        return {"ok": False, "message": "Puedes elegir como máximo tres temas."}
    promise_player: PlayerState | None = None
    if promise_player_id:
        promise_player = next((player for player in team.squad if player.id == promise_player_id), None)
        if promise_player is None:
            return {"ok": False, "message": "El jugador de la promesa no está en la plantilla."}
        if promise_type not in PROMISE_TYPES:
            return {"ok": False, "message": "El tipo de promesa no es válido."}
    effects: dict[str, float] = {}

    def add(key: str, value: float) -> None:
        effects[key] = round(effects.get(key, 0.0) + value, 2)

    type_effect = {
        "pre_match": {"morale": 1, "cohesion": 1, "prep_bonus": 0.10},
        "post_match": {"morale": 1, "cohesion": 1, "board": 1},
        "crisis": {"morale": 1, "cohesion": 2, "board": 1},
        "season": {"board": 1, "fan": 1, "cohesion": 1},
    }[meeting_type]
    for key, value in type_effect.items():
        add(key, value)
    for key, value in TONES[tone].items():
        if key in ("label", "bonus"):
            continue
        add(key, value)
    for topic in clean_topics:
        for key, value in TOPICS[topic].items():
            if key in ("label", "description"):
                continue
            add(key, value)

    chance = 0.50 + (team.manager_rating - 50) / 200 + (team.morale - 10) / 50 + (team.cohesion - 10) / 50
    chance += float(TONES[tone].get("bonus", 0.0))
    if meeting_type == "crisis" and team.morale < 8:
        chance += 0.05
    if meeting_type == "post_match" and state.last_result.get("result") == "Derrota":
        chance -= 0.05
    chance = max(0.15, min(0.90, chance))
    rng = rng or random.Random(
        state.seed * 9701 + date.fromisoformat(state.date).toordinal() + zlib.crc32(tone.encode("utf-8"))
    )
    success = rng.random() < chance
    if success:
        message = "La reunión ha conectado con el grupo: el mensaje se ha entendido."
    else:
        message = "El mensaje no ha calado del todo; el grupo sale con dudas."
        add("morale", -1)
        add("cohesion", -1)
        add("board", -1)
        add("fan", -1)

    team.morale = int(_clamp(team.morale + effects.get("morale", 0), 1, 20))
    team.cohesion = int(_clamp(team.cohesion + effects.get("cohesion", 0), 1, 20))
    team.board_confidence = int(_clamp(team.board_confidence + effects.get("board", 0), 0, 100))
    team.fan_confidence = int(_clamp(team.fan_confidence + effects.get("fan", 0), 0, 100))
    team.prep_bonus = round(_clamp(team.prep_bonus + effects.get("prep_bonus", 0), 0.0, 0.60), 2)
    for player in team.players:
        player.morale = int(_clamp(player.morale + effects.get("morale", 0) * 0.5, 1, 20))
        if "vestuario" in clean_topics:
            player.relationship = int(_clamp(player.relationship + 1, 0, 100))

    promise = None
    if promise_player is not None:
        profile = PROMISE_TYPES[promise_type]
        due = date.fromisoformat(state.date) + timedelta(days=int(profile["days"]))
        promise = {
            "type": promise_type,
            "text": str(profile["text"]),
            "created": state.date,
            "due": due.isoformat(),
            "status": "open",
            "start_apps": promise_player.apps,
            "target_apps": promise_player.apps + int(profile["apps"]),
            "contract_before": promise_player.contract_until,
            "salary_before": promise_player.salary,
        }
        promise_player.promises = (promise_player.promises + [promise])[-12:]
        promise_player.relationship = int(_clamp(promise_player.relationship + 4, 0, 100))
        promise_player.morale = int(_clamp(promise_player.morale + 1, 1, 20))
        add("relationship", 4)

    entry = {
        "id": f"TM-{state.season}-{state.round}-{len(team.team_meetings) + 1}",
        "date": state.date,
        "season": state.season,
        "type": meeting_type,
        "type_label": MEETING_TYPES[meeting_type]["label"],
        "tone": tone,
        "tone_label": TONES[tone]["label"],
        "topics": clean_topics,
        "topic_labels": [TOPICS[item]["label"] for item in clean_topics],
        "success": success,
        "chance": round(chance, 3),
        "effects": effects,
        "promise": promise,
        "promise_player": promise_player.name if promise_player else "",
        "message": message,
    }
    team.team_meetings.append(entry)
    team.team_meetings = team.team_meetings[-30:]
    state.inbox.append(
        {
            "date": state.date,
            "from": "Vestuario",
            "subject": f"Reunión de equipo: {MEETING_TYPES[meeting_type]['label']}",
            "body": message,
        }
    )
    state.inbox = state.inbox[-80:]
    return {
        "ok": True,
        "success": success,
        "message": message,
        "effects": effects,
        "promise": promise,
        "meeting": entry,
    }
