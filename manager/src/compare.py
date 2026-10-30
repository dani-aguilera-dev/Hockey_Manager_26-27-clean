"""Comparación de jugadores.

Compara dos fichas con los atributos y estadísticas ya persistidos. No genera
valoraciones nuevas: muestra los datos reales y cuenta en cuántos atributos
gana cada jugador.
"""

from __future__ import annotations

from typing import Any

from .competitions import competition
from .models import GameState, PlayerState, TeamState

ATTRIBUTE_INFO: dict[str, tuple[str, str]] = {
    # Técnica
    "control": ("Control", "Técnica"),
    "pase": ("Pase", "Técnica"),
    "conduccion": ("Conducción", "Técnica"),
    "golpeo": ("Golpeo", "Técnica"),
    "regate_3d": ("Regate 3D", "Técnica"),
    "flick": ("Flick", "Técnica"),
    "definicion": ("Definición", "Técnica"),
    "desmarque": ("Desmarque", "Técnica"),
    "aerial": ("Juego aéreo", "Técnica"),
    "alto": ("Bola alta", "Técnica"),
    # Físico
    "velocidad": ("Velocidad", "Físico"),
    "resistencia": ("Resistencia", "Físico"),
    "fuerza": ("Fuerza", "Físico"),
    "agilidad": ("Agilidad", "Físico"),
    "coordinacion": ("Coordinación", "Físico"),
    "rebote_gk": ("Rebote", "Físico"),
    # Mental
    "decisiones": ("Decisiones", "Mental"),
    "concentracion": ("Concentración", "Mental"),
    "competitividad": ("Competitividad", "Mental"),
    "liderazgo": ("Liderazgo", "Mental"),
    "posicionamiento": ("Posicionamiento", "Mental"),
    "transicion": ("Transición", "Mental"),
    "pressing": ("Pressing", "Mental"),
    "cobertura": ("Cobertura", "Mental"),
    # Portero
    "reflejos": ("Reflejos", "Portero"),
    "blocaje": ("Blocaje", "Portero"),
    "distribucion": ("Distribución", "Portero"),
    "uno_vs_uno": ("Uno contra uno", "Portero"),
    "pc_gk_save": ("Parada de PC", "Portero"),
    "stroke_save": ("Parada de stroke", "Portero"),
    # Balón parado
    "pc_injection": ("Saque de PC", "Balón parado"),
    "pc_trap": ("Control de PC", "Balón parado"),
    "pc_flick": ("Flick de PC", "Balón parado"),
    "pc_deflection": ("Desvío de PC", "Balón parado"),
    "pc_first_runner": ("Primer defensor de PC", "Balón parado"),
    "stroke_shot": ("Lanzamiento de stroke", "Balón parado"),
    "free_hit": ("Golpe franco", "Balón parado"),
}

CATEGORY_ORDER = ("Técnica", "Físico", "Mental", "Portero", "Balón parado", "Otros")


def _find_player(state: GameState, player_id: str) -> tuple[PlayerState | None, TeamState | None]:
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


def _payload(player: PlayerState, team: TeamState | None) -> dict[str, Any]:
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
        "team_name": team.name if team else "Agente libre",
        "league_name": _league_name(team),
        "origin_team": player.origin_team,
        "apps": player.apps,
        "goals": player.season_goals,
        "assists": player.season_assists,
        "rating": round(float(player.rating), 2),
        "form": round(float(player.form), 2),
        "fatigue": round(float(player.fatigue), 1),
        "morale": player.morale,
        "injury": player.injury,
        "suspension": player.suspension,
        "available": bool(player.available),
        "attributes": dict(player.attributes),
        "overalls": dict(player.overalls),
    }


def compare_candidates(state: GameState, query: str = "", limit: int = 30) -> list[dict[str, Any]]:
    needle = str(query or "").strip().lower()
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for team in state.teams.values():
        for player in team.players:
            if player.id in seen:
                continue
            seen.add(player.id)
            if needle and needle not in player.name.lower() and needle not in team.name.lower():
                continue
            rows.append(
                {
                    "id": player.id,
                    "name": player.name,
                    "team_name": team.name,
                    "position": player.subposition,
                    "age": player.age,
                    "overall": round(float(player.overall), 1),
                    "potential": round(float(player.potential), 1),
                    "value": int(player.value),
                }
            )
    for player in state.free_agents:
        if player.id in seen:
            continue
        if needle and needle not in player.name.lower():
            continue
        rows.append(
            {
                "id": player.id,
                "name": player.name,
                "team_name": "Agente libre",
                "position": player.subposition,
                "age": player.age,
                "overall": round(float(player.overall), 1),
                "potential": round(float(player.potential), 1),
                "value": int(player.value),
            }
        )
    rows.sort(key=lambda row: (-row["overall"], row["age"], row["name"]))
    return rows[: max(1, min(80, int(limit)))]


def compare_players(state: GameState, player_a_id: str, player_b_id: str) -> dict[str, Any]:
    if not player_a_id or not player_b_id:
        return {"ok": False, "message": "Selecciona dos jugadores."}
    if player_a_id == player_b_id:
        return {"ok": False, "message": "Selecciona dos jugadores distintos."}
    player_a, team_a = _find_player(state, player_a_id)
    player_b, team_b = _find_player(state, player_b_id)
    if player_a is None or player_b is None:
        return {"ok": False, "message": "Uno de los jugadores no existe."}
    keys = sorted(set(player_a.attributes) | set(player_b.attributes))
    rows = []
    for key in keys:
        label, category = ATTRIBUTE_INFO.get(key, (key.replace("_", " ").title(), "Otros"))
        value_a = int(player_a.attributes.get(key, 0))
        value_b = int(player_b.attributes.get(key, 0))
        rows.append(
            {
                "key": key,
                "label": label,
                "category": category,
                "a": value_a,
                "b": value_b,
                "winner": "a" if value_a > value_b else ("b" if value_b > value_a else "tie"),
                "difference": value_a - value_b,
            }
        )
    rows.sort(key=lambda row: (CATEGORY_ORDER.index(row["category"]) if row["category"] in CATEGORY_ORDER else 99, row["label"]))
    a_wins = sum(1 for row in rows if row["winner"] == "a")
    b_wins = sum(1 for row in rows if row["winner"] == "b")
    ties = len(rows) - a_wins - b_wins
    payload_a = _payload(player_a, team_a)
    payload_b = _payload(player_b, team_b)
    return {
        "ok": True,
        "a": payload_a,
        "b": payload_b,
        "attributes": rows,
        "categories": [
            {
                "name": category,
                "rows": [row for row in rows if row["category"] == category],
            }
            for category in CATEGORY_ORDER
            if any(row["category"] == category for row in rows)
        ],
        "summary": {
            "a_wins": a_wins,
            "b_wins": b_wins,
            "ties": ties,
            "attributes": len(rows),
            "winner": "a" if a_wins > b_wins else ("b" if b_wins > a_wins else "tie"),
        },
        "differences": {
            "overall": round(payload_a["overall"] - payload_b["overall"], 1),
            "potential": round(payload_a["potential"] - payload_b["potential"], 1),
            "value": payload_a["value"] - payload_b["value"],
            "salary": payload_a["salary"] - payload_b["salary"],
            "age": payload_a["age"] - payload_b["age"],
            "rating": round(payload_a["rating"] - payload_b["rating"], 2),
        },
    }
