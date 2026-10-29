"""Editor de fichas para corregir datos de plantilla.

El juego trabaja con posiciones estimadas. Este editor permite que el jugador
corrija una posición, un atributo o un dato básico sin editar archivos CSV ni
reiniciar la partida. Los cambios quedan registrados en la partida.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import GameState, PlayerState

POSITION_GROUPS = ("Portero", "Defensa", "Medio", "Delantero")
SUBPOSITIONS = ("Portero", "Central", "Lateral", "Medio", "Delantero", "Polivalente")


def find_player(state: GameState, player_id: str) -> tuple[PlayerState | None, str]:
    for team in state.teams.values():
        for player in team.players:
            if player.id == player_id:
                return player, team.id
    for player in state.free_agents:
        if player.id == player_id:
            return player, ""
    return None, ""


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(float(value))))
    except (TypeError, ValueError):
        return default


def edit_player(state: GameState, player_id: str, changes: dict[str, Any]) -> dict[str, Any]:
    player, owner_id = find_player(state, player_id)
    if player is None:
        return {"ok": False, "message": "Jugador no encontrado."}
    before = {
        "name": player.name,
        "age": player.age,
        "position_group": player.position_group,
        "subposition": player.subposition,
        "overall": player.overall,
        "potential": player.potential,
        "archetype": player.archetype,
    }
    name = str(changes.get("name", player.name) or "").strip()
    if len(name) < 2 or len(name) > 80:
        return {"ok": False, "message": "El nombre debe tener entre 2 y 80 caracteres."}
    group = str(changes.get("position_group", player.position_group) or player.position_group)
    if group not in POSITION_GROUPS:
        return {"ok": False, "message": "Grupo de posición no válido."}
    sub = str(changes.get("subposition", player.subposition) or player.subposition)
    if sub not in SUBPOSITIONS:
        return {"ok": False, "message": "Subposición no válida."}
    player.name = name
    player.age = _clamp_int(changes.get("age", player.age), 14, 50, player.age)
    player.position_group = group
    player.subposition = sub
    player.archetype = str(changes.get("archetype", player.archetype) or player.archetype)[:80]
    player.overall = round(float(_clamp_int(changes.get("overall", player.overall), 1, 99, int(player.overall))), 1)
    player.potential = round(
        max(player.overall, float(_clamp_int(changes.get("potential", player.potential), 1, 99, int(player.potential)))),
        1,
    )
    attributes = changes.get("attributes")
    if isinstance(attributes, dict):
        for key, value in attributes.items():
            key = str(key)
            if key in player.attributes:
                player.attributes[key] = _clamp_int(value, 1, 99, int(player.attributes.get(key, 50)))
    log = state.event_flags.setdefault("player_edits", [])
    log.append(
        {
            "date": state.date,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "player_id": player.id,
            "player_name": player.name,
            "owner_id": owner_id,
            "before": before,
            "after": {
                "name": player.name,
                "age": player.age,
                "position_group": player.position_group,
                "subposition": player.subposition,
                "overall": player.overall,
                "potential": player.potential,
                "archetype": player.archetype,
            },
        }
    )
    state.event_flags["player_edits"] = log[-100:]
    return {"ok": True, "message": "Ficha actualizada.", "player": player}


def editor_payload(player: PlayerState) -> dict[str, Any]:
    return {
        "position_groups": list(POSITION_GROUPS),
        "subpositions": list(SUBPOSITIONS),
        "player": {
            "id": player.id,
            "name": player.name,
            "age": player.age,
            "position_group": player.position_group,
            "subposition": player.subposition,
            "archetype": player.archetype,
            "overall": player.overall,
            "potential": player.potential,
            "attributes": dict(player.attributes),
        },
    }
