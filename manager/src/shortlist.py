"""Lista de seguimiento de fichajes (shortlist).

La shortlist no duplica la ficha del jugador: guarda la intención del mánager
(prioridad, nota y fecha) y resuelve los datos vivos del jugador cada vez que se
consulta. Así el seguimiento refleja cambios de club, valor o contrato.
"""

from __future__ import annotations

from typing import Any

from .competitions import competition
from .market import asking_price
from .models import GameState, PlayerState, TeamState

PRIORITIES: dict[str, dict[str, Any]] = {
    "alta": {"label": "Prioridad alta", "order": 0},
    "media": {"label": "Prioridad media", "order": 1},
    "baja": {"label": "Prioridad baja", "order": 2},
}


def _resolve(state: GameState, player_id: str) -> tuple[PlayerState | None, TeamState | None]:
    for team in state.teams.values():
        for player in team.players:
            if player.id == player_id:
                return player, team
    for player in state.free_agents:
        if player.id == player_id:
            return player, None
    return None, None


def _league_name(team: TeamState | None) -> str:
    if team is None:
        return "Agente libre"
    try:
        return competition(team.league).short_name
    except Exception:
        return team.league


def _entry_row(state: GameState, entry: dict[str, Any]) -> dict[str, Any] | None:
    player, owner = _resolve(state, str(entry.get("player_id", "")))
    if player is None:
        return None
    priority = str(entry.get("priority", "media"))
    if priority not in PRIORITIES:
        priority = "media"
    return {
        "id": player.id,
        "name": player.name,
        "age": player.age,
        "position": player.subposition,
        "position_group": player.position_group,
        "overall": round(float(player.overall), 1),
        "potential": round(float(player.potential), 1),
        "value": int(player.value),
        "salary": int(player.salary),
        "contract_until": player.contract_until,
        "team_id": owner.id if owner else None,
        "team_name": owner.name if owner else "Agente libre",
        "league": owner.league if owner else "",
        "league_name": _league_name(owner),
        "transfer_listed": bool(player.transfer_listed),
        "asking": int(asking_price(player)) if owner else 0,
        "available": bool(player.available),
        "loan": bool(player.loan),
        "priority": priority,
        "priority_label": PRIORITIES[priority]["label"],
        "note": str(entry.get("note", "")),
        "added": str(entry.get("added", "")),
    }


def _clean_priority(priority: str) -> str:
    return priority if priority in PRIORITIES else "media"


def _clean_note(note: str) -> str:
    return str(note or "").strip()[:160]


def shortlist_overview(state: GameState) -> dict[str, Any]:
    rows = []
    for entry in state.shortlist:
        row = _entry_row(state, entry)
        if row is not None:
            rows.append(row)
    rows.sort(key=lambda row: (PRIORITIES[row["priority"]]["order"], -row["overall"], row["name"]))
    season_end = int(state.season[:4]) + 1
    return {
        "entries": rows,
        "summary": {
            "total": len(rows),
            "high": sum(1 for row in rows if row["priority"] == "alta"),
            "medium": sum(1 for row in rows if row["priority"] == "media"),
            "low": sum(1 for row in rows if row["priority"] == "baja"),
            "total_value": sum(row["value"] for row in rows),
            "expiring": sum(1 for row in rows if int(str(row["contract_until"])[:4] or 0) <= season_end),
            "available": sum(1 for row in rows if row["available"]),
        },
        "priorities": [{"id": key, **value} for key, value in PRIORITIES.items()],
    }


def shortlist_candidates(state: GameState, query: str = "", limit: int = 12) -> list[dict[str, Any]]:
    followed = {str(entry.get("player_id", "")) for entry in state.shortlist}
    needle = str(query or "").strip().lower()
    rows: list[dict[str, Any]] = []
    for team in state.teams.values():
        if team.id == state.club_id:
            continue
        for player in team.players:
            if player.id in followed or player.loan:
                continue
            if needle and needle not in player.name.lower() and needle not in team.name.lower():
                continue
            rows.append(
                {
                    "id": player.id,
                    "name": player.name,
                    "age": player.age,
                    "position": player.subposition,
                    "overall": round(float(player.overall), 1),
                    "potential": round(float(player.potential), 1),
                    "value": int(player.value),
                    "team_name": team.name,
                    "league_name": _league_name(team),
                    "asking": int(asking_price(player)),
                }
            )
    rows.sort(key=lambda row: (-row["overall"], row["age"], row["name"]))
    return rows[: max(1, min(40, int(limit)))]


def add_to_shortlist(
    state: GameState,
    player_id: str,
    priority: str = "media",
    note: str = "",
) -> dict[str, Any]:
    player, owner = _resolve(state, player_id)
    if player is None:
        return {"ok": False, "message": "El jugador no existe."}
    if owner is not None and owner.id == state.club_id:
        return {"ok": False, "message": "Ese jugador ya es tuyo; no hace falta seguirlo."}
    if any(str(entry.get("player_id", "")) == player.id for entry in state.shortlist):
        return {"ok": False, "message": f"{player.name} ya está en la lista de seguimiento."}
    entry = {
        "player_id": player.id,
        "priority": _clean_priority(priority),
        "note": _clean_note(note),
        "added": state.date,
    }
    state.shortlist.append(entry)
    state.shortlist = state.shortlist[-80:]
    return {
        "ok": True,
        "message": f"{player.name} añadido a la lista de seguimiento.",
        "entry": _entry_row(state, entry),
    }


def update_shortlist_entry(
    state: GameState,
    player_id: str,
    priority: str = "media",
    note: str = "",
) -> dict[str, Any]:
    entry = next((item for item in state.shortlist if str(item.get("player_id", "")) == player_id), None)
    if entry is None:
        return {"ok": False, "message": "El jugador no está en la lista de seguimiento."}
    entry["priority"] = _clean_priority(priority)
    entry["note"] = _clean_note(note)
    row = _entry_row(state, entry)
    return {
        "ok": True,
        "message": "Seguimiento actualizado.",
        "entry": row,
    }


def remove_from_shortlist(state: GameState, player_id: str) -> dict[str, Any]:
    entry = next((item for item in state.shortlist if str(item.get("player_id", "")) == player_id), None)
    if entry is None:
        return {"ok": False, "message": "El jugador no está en la lista de seguimiento."}
    state.shortlist = [item for item in state.shortlist if str(item.get("player_id", "")) != player_id]
    return {"ok": True, "message": "Jugador retirado de la lista de seguimiento."}


def is_shortlisted(state: GameState, player_id: str) -> bool:
    return any(str(entry.get("player_id", "")) == player_id for entry in state.shortlist)
