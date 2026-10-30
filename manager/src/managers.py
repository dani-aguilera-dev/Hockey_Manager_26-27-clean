"""Cambios de entrenador en clubes IA.

La presión se acumula cuando un club lleva varias jornadas en la parte baja de
su liga. Al tercer aviso, la junta destituye al entrenador y nombra a un
reemplazo del cuerpo técnico o a un interino. El usuario no se despide
automáticamente: recibe ultimátum y sigue al mando hasta que acepte otro club.
"""

from __future__ import annotations

from typing import Any

from .competitions import competition
from .models import GameState, TeamState

SACK_PRESSURE = 4
MANAGER_COOLDOWN_ROUNDS = 10
BOTTOM_PLACES = 2


def _league_table(state: GameState, league: str) -> list[TeamState]:
    if league == state.competition:
        return state.table()
    return sorted(
        [team for team in state.teams.values() if team.league == league],
        key=lambda team: (
            -team.points,
            -(team.goals_for - team.goals_against),
            -team.goals_for,
            team.name,
        ),
    )


def _position(state: GameState, team: TeamState) -> int:
    table = _league_table(state, team.league)
    return next((index for index, item in enumerate(table, 1) if item.id == team.id), 0)


def replacement_manager(team: TeamState) -> str:
    """Nombre del sustituto inmediato: segundo entrenador o interino."""
    for role in ("assistant", "head_coach"):
        candidate = next(
            (
                member
                for member in team.staff
                if member.role == role and member.name != team.manager_name
            ),
            None,
        )
        if candidate is not None:
            return candidate.name
    return "Entrenador interino"


def ensure_manager_names(state: GameState) -> None:
    """Rellena nombres en partidas antiguas o equipos sin entrenador."""
    for team in state.teams.values():
        if team.manager_name:
            continue
        if team.id == state.club_id:
            team.manager_name = state.manager_name
        else:
            head = next((member for member in team.staff if member.role == "head_coach"), None)
            team.manager_name = head.name if head else "Entrenador interino"


def record_manager_change(
    state: GameState,
    team: TeamState,
    old_name: str,
    new_name: str,
    kind: str,
    reason: str,
) -> dict[str, Any]:
    change = {
        "date": state.date,
        "season": state.season,
        "round": state.round,
        "type": kind,
        "club_id": team.id,
        "club_name": team.name,
        "league": team.league,
        "league_name": competition(team.league).short_name,
        "old_manager": old_name,
        "new_manager": new_name,
        "reason": reason,
    }
    state.manager_changes.append(change)
    state.manager_changes = state.manager_changes[-60:]
    return change


def process_manager_changes(state: GameState) -> list[dict[str, Any]]:
    """Evalúa la presión de los clubes IA y ejecuta los despidos procedentes."""
    if state.phase not in ("regular", "promotion"):
        return []
    ensure_manager_names(state)
    changes: list[dict[str, Any]] = []
    for team in state.teams.values():
        if team.id == state.club_id:
            continue
        if team.played < 8:
            continue
        if team.manager_since_round and state.round - team.manager_since_round < MANAGER_COOLDOWN_ROUNDS:
            continue
        table = _league_table(state, team.league)
        if len(table) < 4:
            continue
        position = _position(state, team)
        bottom_from = max(1, len(table) - BOTTOM_PLACES + 1)
        if position >= bottom_from:
            team.manager_pressure += 1
        else:
            team.manager_pressure = max(0, team.manager_pressure - 1)
        if team.manager_pressure < SACK_PRESSURE:
            continue
        old_name = team.manager_name or "Entrenador"
        new_name = replacement_manager(team)
        if new_name == old_name or new_name == "Entrenador interino":
            team.manager_pressure = 0
            continue
        team.manager_name = new_name
        team.manager_pressure = 0
        team.manager_since_round = state.round
        team.board_confidence = min(100, max(35, team.board_confidence + 6))
        if old_name == "Entrenador interino":
            change_type = "hired"
            reason = f"La junta nombra a {new_name} para cubrir el banquillo."
        else:
            change_type = "sack"
            reason = f"La junta destituye a {old_name} tras {SACK_PRESSURE} avisos en la parte baja."
        change = record_manager_change(
            state,
            team,
            old_name,
            new_name,
            change_type,
            reason,
        )
        state.inbox.append(
            {
                "date": state.date,
                "from": "Mercado de entrenadores",
                "subject": f"Cambio de entrenador en {team.name}",
                "body": f"{old_name} deja el banquillo. {new_name} toma el mando de forma inmediata.",
            }
        )
        state.inbox = state.inbox[-120:]
        changes.append(change)
    return changes


def manager_changes_overview(state: GameState) -> list[dict[str, Any]]:
    return list(reversed(state.manager_changes[-12:]))


USER_SACK_PRESSURE = 3
USER_SACK_BOARD_CONFIDENCE = 12
USER_SACK_MIN_ROUNDS = 8


def sack_user(state: GameState, reason: str, kind: str = "sacked") -> dict[str, Any]:
    """Destituye al usuario o registra su dimisión.

    El club sigue existiendo y queda dirigido por un sustituto, pero el usuario
    pasa a estar sin banquillo hasta que acepte otra oferta.
    """
    if state.user_sacked:
        return {"ok": False, "message": "Ya estás sin club."}
    team = state.user_team
    old_name = state.manager_name
    new_name = replacement_manager(team)
    team.manager_name = new_name
    team.manager_pressure = 0
    team.manager_since_round = state.round
    state.user_sacked = True
    state.user_pressure = 0
    state.pending_job = {}
    state.manager_contract = {}
    state.user_sacking = {
        "date": state.date,
        "season": state.season,
        "round": state.round,
        "club_id": team.id,
        "club_name": team.name,
        "league": team.league,
        "league_name": competition(team.league).short_name,
        "manager_name": old_name,
        "replacement": new_name,
        "reason": reason,
        "kind": kind,
    }
    change_type = "resigned" if kind == "resigned" else "user_sacked"
    record_manager_change(state, team, old_name, new_name, change_type, reason)
    state.inbox.append(
        {
            "date": state.date,
            "from": "Junta directiva",
            "subject": f"Salida del banquillo de {team.name}",
            "body": reason,
        }
    )
    state.inbox = state.inbox[-120:]
    return {"ok": True, "message": reason, "sacking": state.user_sacking}


def process_user_sacking(state: GameState) -> dict[str, Any] | None:
    """Acumula presión sobre el usuario y lo destituye si la crisis persiste."""
    if state.user_sacked or state.phase not in ("regular", "promotion"):
        return None
    team = state.user_team
    if team.played < USER_SACK_MIN_ROUNDS:
        return None
    table = _league_table(state, team.league)
    if len(table) < 4:
        return None
    position = _position(state, team)
    bottom_from = max(1, len(table) - 1)
    crisis = team.board_confidence <= USER_SACK_BOARD_CONFIDENCE and position >= bottom_from
    if crisis:
        state.user_pressure += 1
    else:
        state.user_pressure = max(0, state.user_pressure - 1)
    if state.user_pressure < USER_SACK_PRESSURE:
        return None
    return sack_user(
        state,
        f"La junta destituye al mánager tras {USER_SACK_PRESSURE} avisos en la parte baja.",
    )


def resign_user(state: GameState) -> dict[str, Any]:
    return sack_user(state, "El mánager presenta su dimisión.", kind="resigned")
