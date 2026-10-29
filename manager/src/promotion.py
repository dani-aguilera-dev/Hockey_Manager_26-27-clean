"""Camino de ascenso a DHB: objetivos y clasificaciones de la fase nacional."""

from __future__ import annotations

from .calendar import league_table
from .competitions import COMPETITIONS, competition
from .models import GameState


def _row(table, team_id):
    return next((row for row in table if row["team_id"] == team_id), None)


def _league_rows(state: GameState, code: str) -> list[dict]:
    return [
        {"position": position, "team_id": team.id, "team": team.name, "points": team.points}
        for position, team in enumerate(league_table(state.teams, code), 1)
    ]


def promotion_leagues(state: GameState) -> list[dict]:
    rows = []
    for meta in COMPETITIONS.values():
        if meta.system != "regional":
            continue
        table = _league_rows(state, meta.code)
        rows.append(
            {
                "code": meta.code,
                "name": meta.name,
                "short_name": meta.short_name,
                "qualifiers": table[: meta.promotion_qualifiers],
                "spots": meta.promotion_qualifiers,
                "table": table,
            }
        )
    return rows


def promotion_path(state: GameState) -> dict:
    meta = competition(state.competition)
    if meta.system != "regional":
        return {"objectives": [], "leagues": [], "target": 0, "position": 0}

    table = _league_rows(state, state.competition)
    user_row = next((row for row in table if row["team_id"] == state.club_id), None)
    position = user_row["position"] if user_row else 0
    target = meta.promotion_qualifiers
    raw = state.promotion if state.phase == "promotion" else state.playout
    if not raw or raw.get("format") != "regional_promotion":
        raw = {}
    groups = raw.get("groups", [])
    final = raw.get("final_group") or {}
    group = next((item for item in groups if state.club_id in item.get("team_ids", [])), None)
    qualified = group is not None
    final_table = final.get("table", [])
    final_row = _row(final_table, state.club_id)
    promoted = state.club_id in raw.get("promoted_ids", [])
    phase = state.phase

    if phase == "regular":
        objective1_status = "active"
        objective1_detail = f"{position}º de {len(table)} · objetivo: top {target}"
        objective1_text = (
            "Ahora mismo estás dentro de la plaza de Fase Nacional."
            if position and position <= target
            else "Ahora mismo estás fuera; necesitas entrar en el top."
        )
    elif qualified:
        objective1_status = "completed"
        objective1_detail = f"Clasificado · {position}º de {len(table)}"
        objective1_text = "Objetivo cumplido. Ya estás en la Fase Nacional."
    else:
        objective1_status = "failed"
        objective1_detail = f"Sin clasificación · {position}º de {len(table)}"
        objective1_text = "No conseguiste entrar en la plaza de Fase Nacional."

    if not qualified:
        objective2_status = "pending" if phase == "regular" else "failed"
        objective2_detail = "Se activa al clasificarte para la Fase Nacional"
        objective2_text = "Todavía no está activo: primero hay que cumplir el Objetivo 1."
    elif final:
        if group and group.get("winner_id") == state.club_id:
            objective2_status = "completed"
            objective2_detail = "Primero de tu grupo"
            objective2_text = "Ganaste tu grupo. Estás en la liguilla final por el ascenso."
        else:
            objective2_status = "failed"
            objective2_detail = "Eliminado en la fase de grupos"
            objective2_text = "No ganaste tu grupo; la fase termina aquí."
    else:
        group_row = _row(group.get("table", []), state.club_id) if group else None
        objective2_status = "active"
        objective2_detail = (
            f"{group_row['position']}º de 4 · {group_row['points']} pts"
            if group_row
            else "Fase de grupos en juego"
        )
        objective2_text = (
            f"Vas {group_row['position']}º. Solo el primero del grupo pasa a la liguilla final."
            if group_row
            else "La fase de grupos está en juego."
        )

    if promoted:
        objective3_status = "completed"
        objective3_detail = "Ascenso conseguido"
        objective3_text = "Estás entre los dos primeros. Has ascendido a DHB."
    elif final_row and phase == "promotion":
        objective3_status = "active"
        objective3_detail = f"{final_row['position']}º de 4 · {final_row['points']} pts"
        objective3_text = f"Vas {final_row['position']}º. Los dos primeros ascienden; quedan partidos por jugar."
    elif final and phase == "season_end":
        objective3_status = "failed"
        objective3_detail = f"{final_row['position']}º de 4 · fuera del ascenso" if final_row else "Sin ascenso"
        objective3_text = "No terminaste entre los dos primeros; no hay ascenso."
    else:
        objective3_status = "pending"
        objective3_detail = "Se activa al ganar tu grupo"
        objective3_text = "Todavía no está activo: primero hay que ganar el grupo."

    return {
        "target": target,
        "position": position,
        "qualified": qualified,
        "leagues": promotion_leagues(state),
        "objectives": [
            {
                "key": "league",
                "title": f"Queda entre los {target} primeros",
                "description": f"Clasificación para la Fase Nacional desde {meta.short_name}.",
                "status": objective1_status,
                "detail": objective1_detail,
                "state_text": objective1_text,
            },
            {
                "key": "group",
                "title": "Primero de tu grupo",
                "description": "Gana tu grupo de cuatro para pasar a la liguilla final.",
                "status": objective2_status,
                "detail": objective2_detail,
                "state_text": objective2_text,
            },
            {
                "key": "final",
                "title": "Top 2 de la fase final",
                "description": "Los dos primeros de la liguilla final ascienden a DHB.",
                "status": objective3_status,
                "detail": objective3_detail,
                "state_text": objective3_text,
            },
        ],
    }
