"""Objetivos de temporada con identidad propia para cada sistema de liga."""

from __future__ import annotations

from .competitions import competition
from .models import GameState
from .promotion import promotion_path


def _row(table, team_id):
    return next((row for row in table if row["team_id"] == team_id), None)


def _table_rows(state: GameState) -> list[dict]:
    return [
        {"position": position, "team_id": team.id, "team": team.name, "points": team.points}
        for position, team in enumerate(state.table(), 1)
    ]


def _objective(key, title, description, status, detail, state_text):
    return {
        "key": key,
        "title": title,
        "description": description,
        "status": status,
        "detail": detail,
        "state_text": state_text,
    }


def _status(position, target, phase, completed=False, failed=False):
    if completed:
        return "completed"
    if failed:
        return "failed"
    if phase == "regular":
        return "active"
    return "pending"


def _dhb_objectives(state: GameState) -> list[dict]:
    table = _table_rows(state)
    row = _row(table, state.club_id)
    position = row["position"] if row else 0
    phase = state.phase
    group = state.dhb_group
    in_group_a = group == "A"
    final4 = state.final4 or {}
    semifinalists = {item.get("home_id") for item in final4.get("semifinals", [])} | {
        item.get("away_id") for item in final4.get("semifinals", [])
    }
    promoted = state.club_id in state.promoted_ids
    champion = final4.get("champion_id") == state.club_id

    if phase == "regular" and state.dhb_phase == 1:
        status1 = "active"
        text1 = (
            "Ahora mismo estás dentro del grupo A."
            if position and position <= 4
            else "Ahora mismo estás fuera del grupo A; necesitas entrar en el top 4."
        )
    elif state.dhb_phase >= 2 or phase == "season_end":
        status1 = "completed" if in_group_a else "failed"
        text1 = "Pasaste al grupo A." if in_group_a else "Jugarás la segunda fase en el grupo B."
    else:
        status1, text1 = "pending", "Se activa al comenzar la liga regular."
    detail1 = f"{position}º de {len(table)} · objetivo: top 4"

    if state.club_id in semifinalists or champion:
        status2, text2 = "completed", "Estás en la Final Four por el título."
    elif phase == "season_end" or final4:
        status2, text2 = "failed", "No entraste en la Final Four."
    elif state.dhb_phase >= 2:
        status2, text2 = "active", "La segunda fase decide los cuatro finalistas."
    else:
        status2, text2 = "pending", "Se activa al pasar al grupo A."
    detail2 = "Final Four" if state.club_id in semifinalists else "Top 4 del grupo A"

    if promoted:
        status3, text3 = "completed", "Has ascendido a DHA."
    elif phase == "season_end":
        status3, text3 = "failed", "No has ascendido a DHA."
    elif state.dhb_phase >= 2 and in_group_a:
        status3, text3 = "active", "Los dos primeros de DHB ascienden a DHA."
    else:
        status3, text3 = "pending", "Se activa si llegas a la fase decisiva."
    detail3 = "2 plazas de ascenso a DHA"

    return [
        _objective("group", "Queda entre los 4 primeros de tu grupo", "Clasificación para el grupo A de la segunda fase.", status1, detail1, text1),
        _objective("final4", "Llega a la Final Four", "Los cuatro mejores equipos pelean por el título y el ascenso.", status2, detail2, text2),
        _objective("promotion", "Asciende a DHA", "Los dos primeros de la fase final suben a División de Honor A.", status3, detail3, text3),
    ]


def _dha_objectives(state: GameState) -> list[dict]:
    table = _table_rows(state)
    row = _row(table, state.club_id)
    position = row["position"] if row else 0
    final4 = state.final4 or {}
    semifinalists = {item.get("home_id") for item in final4.get("semifinals", [])} | {
        item.get("away_id") for item in final4.get("semifinals", [])
    }
    champion = final4.get("champion_id") == state.club_id
    in_ehl = state.user_team.name in (state.ehl or {}).get("participants", [])

    if state.club_id in semifinalists or champion:
        status1, text1 = "completed", "Estás en la Final Four."
    elif state.phase == "season_end" or final4:
        status1, text1 = "failed", "No entraste en la Final Four."
    else:
        status1, text1 = "active", "Top 4 al final de la liga regular."
    detail1 = f"{position}º de {len(table)} · objetivo: top 4"

    if champion:
        status2, text2 = "completed", "Has ganado la Final Four."
    elif final4:
        status2, text2 = "failed", "La Final Four no terminó con el título."
    else:
        status2, text2 = "pending", "Se activa al entrar en la Final Four."
    detail2 = "Campeón de la Final Four"

    if in_ehl or (state.ehl or {}).get("winner_id") == state.club_id:
        status3, text3 = "completed", "Estás clasificado para la EHL."
    elif state.phase == "season_end":
        status3, text3 = "failed", "No conseguiste plaza europea."
    else:
        status3, text3 = "pending", "Se decide por la clasificación y la Copa."
    detail3 = "Plaza europea"

    return [
        _objective("final4", "Queda entre los 4 primeros", "Acceso a la Final Four por el título de DHA.", status1, detail1, text1),
        _objective("champion", "Gana la Final Four", "El título de División de Honor A.", status2, detail2, text2),
        _objective("ehl", "Clasifícate para la EHL", "Plaza europea para el club.", status3, detail3, text3),
    ]


def _international_objectives(state: GameState) -> list[dict]:
    meta = competition(state.competition)
    table = _table_rows(state)
    row = _row(table, state.club_id)
    position = row["position"] if row else 0
    target = meta.playoffs or 4
    final4 = state.final4 or {}
    semifinalists = {item.get("home_id") for item in final4.get("semifinals", [])} | {
        item.get("away_id") for item in final4.get("semifinals", [])
    }
    champion = final4.get("champion_id") == state.club_id

    if state.club_id in semifinalists or champion:
        status1, text1 = "completed", "Estás en los play-offs."
    elif state.phase == "season_end" or final4:
        status1, text1 = "failed", "No entraste en los play-offs."
    else:
        status1, text1 = "active", f"Top {target} al final de la liga regular."
    detail1 = f"{position}º de {len(table)} · objetivo: top {target}"

    if champion:
        status2, text2 = "completed", "Has ganado el campeonato."
    elif final4:
        status2, text2 = "failed", "Los play-offs no terminaron con el título."
    else:
        status2, text2 = "pending", "Se activa al entrar en los play-offs."
    detail2 = "Campeón"

    return [
        _objective("playoffs", f"Queda entre los {target} primeros", "Clasificación para los play-offs.", status1, detail1, text1),
        _objective("champion", "Gana el campeonato", "Título de la liga internacional.", status2, detail2, text2),
    ]


def competition_objectives(state: GameState) -> dict:
    meta = competition(state.competition)
    if meta.system == "regional":
        path = promotion_path(state)
        return {
            "system": "regional",
            "title": "Camino al ascenso a DHB",
            "objectives": path.get("objectives", []),
            "path": path,
        }
    if meta.system == "dhb_two_phase":
        return {
            "system": "dhb_two_phase",
            "title": "Objetivos de DHB",
            "objectives": _dhb_objectives(state),
        }
    if meta.system == "dha":
        return {
            "system": "dha",
            "title": "Objetivos de DHA",
            "objectives": _dha_objectives(state),
        }
    if meta.international:
        return {
            "system": "international",
            "title": "Objetivos de liga",
            "objectives": _international_objectives(state),
        }
    return {"system": meta.system, "title": "Objetivos", "objectives": []}
