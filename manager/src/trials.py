"""Período de prueba de agentes libres (trialists).

El club invita a un agente libre a entrenar durante unos días. El trial no
ocupa ficha permanente: genera un informe con recomendación de fichar, seguir
o descartar. El jugador sigue siendo agente libre y puede negociarse desde el
mercado.
"""

from __future__ import annotations

import zlib
from datetime import date, timedelta
from typing import Any

from .models import GameState, PlayerState

TRIAL_DAYS = 14
MAX_ACTIVE_TRIALS = 3

ATTRIBUTE_LABELS = {
    "control": "Control",
    "pase": "Pase",
    "conduccion": "Conducción",
    "golpeo": "Golpeo",
    "regate_3d": "Regate",
    "flick": "Flick",
    "definicion": "Definición",
    "velocidad": "Velocidad",
    "resistencia": "Resistencia",
    "fuerza": "Fuerza",
    "agilidad": "Agilidad",
    "decisiones": "Decisiones",
    "concentracion": "Concentración",
    "competitividad": "Competitividad",
    "liderazgo": "Liderazgo",
    "posicionamiento": "Posicionamiento",
    "cobertura": "Cobertura",
    "pressing": "Pressing",
    "reflejos": "Reflejos",
    "blocaje": "Blocaje",
    "distribucion": "Distribución",
    "uno_vs_uno": "Uno contra uno",
}


def _find_free_agent(state: GameState, player_id: str) -> PlayerState | None:
    return next((player for player in state.free_agents if player.id == player_id), None)


def _active(state: GameState, player_id: str) -> bool:
    return any(
        trial.get("player_id") == player_id and trial.get("status") == "active"
        for trial in state.trials
    )


def _player_row(player: PlayerState, trial: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "id": player.id,
        "name": player.name,
        "age": player.age,
        "position": player.subposition,
        "position_group": player.position_group,
        "overall": round(float(player.overall), 1),
        "potential": round(float(player.potential), 1),
        "value": int(player.value),
        "salary": int(player.salary),
        "origin_team": player.origin_team,
        "attributes": dict(player.attributes),
    }
    if trial is not None:
        row.update(
            {
                "trial_id": trial.get("id", ""),
                "start": trial.get("start", ""),
                "end": trial.get("end", ""),
                "progress": int(trial.get("progress", 0) or 0),
                "status": trial.get("status", "active"),
            }
        )
    return row


def trial_candidates(state: GameState, query: str = "", limit: int = 20) -> list[dict[str, Any]]:
    needle = str(query or "").strip().lower()
    rows = []
    for player in state.free_agents:
        if _active(state, player.id):
            continue
        if needle and needle not in player.name.lower():
            continue
        rows.append(_player_row(player))
    rows.sort(key=lambda row: (-row["overall"], row["age"], row["name"]))
    return rows[: max(1, min(50, int(limit)))]


def _strengths(player: PlayerState, limit: int = 3) -> list[str]:
    values = sorted(player.attributes.items(), key=lambda item: (-item[1], item[0]))
    return [f"{ATTRIBUTE_LABELS.get(key, key.replace('_', ' ').title())} {value}" for key, value in values[:limit]]


def _weaknesses(player: PlayerState, limit: int = 2) -> list[str]:
    values = sorted(player.attributes.items(), key=lambda item: (item[1], item[0]))
    return [f"{ATTRIBUTE_LABELS.get(key, key.replace('_', ' ').title())} {value}" for key, value in values[:limit]]


def _report(state: GameState, player: PlayerState) -> dict[str, Any]:
    team = state.user_team
    squad = team.squad
    average = sum(item.overall for item in squad) / len(squad) if squad else 60.0
    fit = float(player.overall) - average
    growth = max(0.0, float(player.potential) - float(player.overall))
    score = 50 + fit * 2.2 + growth * 1.4 + max(0, 24 - player.age) * 0.6
    score = round(max(0.0, min(100.0, score)), 1)
    if score >= 70:
        recommendation = "fichar"
        label = "Fichar"
    elif score >= 55:
        recommendation = "seguir"
        label = "Seguir"
    else:
        recommendation = "descartar"
        label = "Descartar"
    return {
        "score": score,
        "recommendation": recommendation,
        "recommendation_label": label,
        "fit": round(fit, 1),
        "growth": round(growth, 1),
        "strengths": _strengths(player),
        "weaknesses": _weaknesses(player),
        "summary": (
            f"{player.name} ({player.age} años, {player.subposition}) deja un informe de {score}/100. "
            f"Recomendación: {label.lower()}."
        ),
    }


def _complete_trial(state: GameState, trial: dict[str, Any]) -> dict[str, Any]:
    player = _find_free_agent(state, str(trial.get("player_id", "")))
    trial["status"] = "completed"
    trial["progress"] = 100
    trial["completed"] = state.date
    if player is None:
        trial["report"] = {
            "score": 0,
            "recommendation": "descartar",
            "recommendation_label": "Descartar",
            "fit": 0,
            "growth": 0,
            "strengths": [],
            "weaknesses": [],
            "summary": "El jugador ya no está disponible.",
        }
    else:
        trial["report"] = _report(state, player)
    entry = {
        **trial,
        "player_name": player.name if player else trial.get("player_name", ""),
    }
    state.trial_history.append(entry)
    state.trial_history = state.trial_history[-40:]
    state.inbox.append(
        {
            "date": state.date,
            "from": "Cuerpo técnico",
            "subject": f"Informe de prueba: {entry['player_name']}",
            "body": trial["report"]["summary"],
        }
    )
    state.inbox = state.inbox[-80:]
    return entry


def trial_overview(state: GameState, query: str = "") -> dict[str, Any]:
    active = []
    for trial in state.trials:
        if trial.get("status") != "active":
            continue
        player = _find_free_agent(state, str(trial.get("player_id", "")))
        if player is None:
            continue
        row = _player_row(player, trial)
        end = date.fromisoformat(str(trial.get("end", state.date)))
        row["days_left"] = max(0, (end - date.fromisoformat(state.date)).days)
        active.append(row)
    active.sort(key=lambda row: row["end"])
    history = list(reversed(state.trial_history[-12:]))
    return {
        "active": active,
        "candidates": trial_candidates(state, query),
        "history": history,
        "summary": {
            "active": len(active),
            "completed": len(state.trial_history),
            "candidates": len(state.free_agents),
            "max_active": MAX_ACTIVE_TRIALS,
        },
    }


def invite_trial(state: GameState, player_id: str, days: int = TRIAL_DAYS) -> dict[str, Any]:
    player = _find_free_agent(state, player_id)
    if player is None:
        return {"ok": False, "message": "El jugador no es agente libre."}
    if _active(state, player.id):
        return {"ok": False, "message": "El jugador ya está a prueba."}
    active = [trial for trial in state.trials if trial.get("status") == "active"]
    if len(active) >= MAX_ACTIVE_TRIALS:
        return {"ok": False, "message": f"Solo puedes tener {MAX_ACTIVE_TRIALS} jugadores a prueba."}
    days = max(7, min(28, int(days)))
    start = date.fromisoformat(state.date)
    trial = {
        "id": f"TR-{state.season}-{state.round}-{zlib.crc32(player.id.encode('utf-8')) % 10000}",
        "player_id": player.id,
        "player_name": player.name,
        "start": start.isoformat(),
        "end": (start + timedelta(days=days)).isoformat(),
        "status": "active",
        "progress": 0,
        "days": days,
    }
    state.trials.append(trial)
    state.inbox.append(
        {
            "date": state.date,
            "from": "Cuerpo técnico",
            "subject": f"Prueba iniciada: {player.name}",
            "body": f"{player.name} entrenará a prueba durante {days} días.",
        }
    )
    state.inbox = state.inbox[-80:]
    return {"ok": True, "message": f"{player.name} empieza una prueba de {days} días.", "trial": trial}


def end_trial(state: GameState, trial_id: str) -> dict[str, Any]:
    trial = next((item for item in state.trials if item.get("id") == trial_id), None)
    if trial is None:
        return {"ok": False, "message": "La prueba no existe."}
    if trial.get("status") != "active":
        return {"ok": False, "message": "La prueba ya ha terminado."}
    entry = _complete_trial(state, trial)
    return {"ok": True, "message": entry["report"]["summary"], "trial": entry}


def advance_trials(state: GameState) -> dict[str, Any]:
    completed = []
    for trial in list(state.trials):
        if trial.get("status") != "active":
            continue
        start = date.fromisoformat(str(trial.get("start", state.date)))
        end = date.fromisoformat(str(trial.get("end", state.date)))
        today = date.fromisoformat(state.date)
        total = max(1, (end - start).days)
        elapsed = max(0, (today - start).days)
        trial["progress"] = min(99, int(100 * elapsed / total))
        if today >= end:
            completed.append(_complete_trial(state, trial))
    return {"completed": len(completed), "active": sum(1 for trial in state.trials if trial.get("status") == "active")}
