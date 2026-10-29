"""Cesiones y préstamos entre clubes.

Las cesiones mueven al jugador de verdad: sale de la plantilla de origen y
entra en la del club de destino. Al terminar la temporada vuelve a su club de
origen. La operación guarda contribución salarial, promesa de minutos y una
pequeña tasa de cesión.
"""

from __future__ import annotations

import random
import zlib
from datetime import date
from typing import Any

from .competitions import competition
from .market import market_window, market_window_text
from .models import GameState, PlayerState, TeamState

PLAYING_TIMES: dict[str, dict[str, Any]] = {
    "titular": {"label": "Titular habitual", "bonus": 0.08},
    "rotacion": {"label": "Rotación", "bonus": 0.0},
    "suplente": {"label": "Suplente", "bonus": -0.08},
}


def _mean_overall(team: TeamState) -> float:
    values = [player.overall for player in team.players]
    return sum(values) / len(values) if values else 50.0


def _key_threshold(team: TeamState) -> float:
    values = sorted((player.overall for player in team.players), reverse=True)
    if len(values) >= 11:
        return values[10]
    return values[-1] if values else 50.0


def _loan_fee(player: PlayerState, wage_share: int) -> int:
    factor = 0.5 + max(0, min(100, int(wage_share))) / 100
    return max(5000, int(max(1, player.value) * 0.012 * factor))


def _loan_rng(state: GameState, salt: str) -> random.Random:
    return random.Random(
        state.seed * 9301
        + date.fromisoformat(state.date).toordinal()
        + zlib.crc32(salt.encode("utf-8"))
    )


def _player_row(player: PlayerState, owner: TeamState) -> dict[str, Any]:
    meta = competition(owner.league)
    return {
        "id": player.id,
        "name": player.name,
        "age": player.age,
        "position_group": player.position_group,
        "subposition": player.subposition,
        "overall": round(float(player.overall), 1),
        "potential": round(float(player.potential), 1),
        "team_id": owner.id,
        "team_name": owner.name,
        "country": owner.country,
        "league": owner.league,
        "league_name": meta.short_name,
        "salary": int(player.salary),
        "value": int(player.value),
    }


def loan_targets(state: GameState, limit: int = 40) -> list[dict[str, Any]]:
    """Jugadores de otros clubes que pueden salir cedidos.

    Se priorizan los que no son titulares indiscutibles en su club de origen.
    """
    rows: list[dict[str, Any]] = []
    for team in state.teams.values():
        if team.id == state.club_id or len(team.squad) <= 16:
            continue
        threshold = _key_threshold(team)
        for player in team.players:
            if player.loan or player.age > 34 or player.overall < 45:
                continue
            if player.overall >= threshold and not player.transfer_listed:
                continue
            row = _player_row(player, team)
            row.update(
                {
                    "loan_fee": _loan_fee(player, 50),
                    "wage_share_options": [0, 25, 50, 75, 100],
                    "playing_time_options": [
                        {"id": key, "label": value["label"]} for key, value in PLAYING_TIMES.items()
                    ],
                    "is_key": False,
                }
            )
            rows.append(row)
    rows.sort(key=lambda row: (row["country"] != state.country, -row["overall"], row["age"], row["name"]))
    return rows[:limit]


def outgoing_candidates(state: GameState) -> list[dict[str, Any]]:
    """Jugadores del usuario que pueden salir cedidos y clubes interesados."""
    user = state.user_team
    threshold = _key_threshold(user)
    rows: list[dict[str, Any]] = []
    for player in user.players:
        if player.loan or player.age > 34:
            continue
        interested = []
        for team in state.teams.values():
            if team.id == user.id or len(team.squad) >= 25:
                continue
            if competition(team.league).standard + 12 < player.overall:
                continue
            if team.league == user.league or competition(team.league).standard <= competition(user.league).standard:
                interested.append(
                    {
                        "id": team.id,
                        "name": team.name,
                        "league": team.league,
                        "league_name": competition(team.league).short_name,
                        "squad_size": len(team.players),
                    }
                )
        interested.sort(key=lambda item: (item["league_name"], item["name"]))
        if not interested:
            continue
        row = _player_row(player, user)
        row.update(
            {
                "loan_fee": _loan_fee(player, 50),
                "wage_share_options": [0, 25, 50, 75, 100],
                "playing_time_options": [
                    {"id": key, "label": value["label"]} for key, value in PLAYING_TIMES.items()
                ],
                "is_key": player.overall >= threshold,
                "interested_clubs": interested[:6],
            }
        )
        rows.append(row)
    rows.sort(key=lambda row: (-row["overall"], row["name"]))
    return rows


def _find_player(state: GameState, player_id: str) -> tuple[PlayerState | None, TeamState | None]:
    for team in state.teams.values():
        for player in team.players:
            if player.id == player_id:
                return player, team
    return None, None


def _loan_entry(
    state: GameState,
    player: PlayerState,
    parent: TeamState,
    borrower: TeamState,
    wage_share: int,
    playing_time: str,
    fee: int,
    *,
    incoming: bool,
) -> dict[str, Any]:
    return {
        "id": f"LN-{state.season}-{state.round}-{player.id}-{borrower.id}",
        "player_id": player.id,
        "player_name": player.name,
        "parent_club_id": parent.id,
        "parent_club_name": parent.name,
        "loan_club_id": borrower.id,
        "loan_club_name": borrower.name,
        "start_date": state.date,
        "end_date": f"{int(state.season[:4]) + 1}-06-30",
        "wage_share": int(wage_share),
        "playing_time": playing_time,
        "playing_time_label": PLAYING_TIMES.get(playing_time, PLAYING_TIMES["rotacion"])["label"],
        "fee": int(fee),
        "incoming": incoming,
        "accepted": True,
        "apps": 0,
        "goals": 0,
        "assists": 0,
    }


def request_loan_in(
    state: GameState,
    player_id: str,
    wage_share: int = 50,
    playing_time: str = "rotacion",
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """Pide una cesión al club propietario del jugador."""
    player, owner = _find_player(state, player_id)
    if player is None or owner is None:
        return {"ok": False, "message": "El jugador no existe."}
    user = state.user_team
    if owner.id == user.id:
        return {"ok": False, "message": "Ese jugador ya es tuyo."}
    if player.loan:
        return {"ok": False, "message": "El jugador ya está cedido."}
    if len(owner.squad) <= 16:
        return {"ok": False, "message": "El club de origen no puede quedarse sin fondo de armario."}
    if len(user.squad) >= 25:
        return {"ok": False, "message": "La plantilla está llena; libera una ficha antes de pedir una cesión."}
    wage_share = max(0, min(100, int(wage_share)))
    if playing_time not in PLAYING_TIMES:
        playing_time = "rotacion"
    fee = _loan_fee(player, wage_share)
    if user.budget < fee:
        return {"ok": False, "message": "No hay caja suficiente para la tasa de cesión."}
    chance = 0.45 + (wage_share - 50) / 250 + (player.overall - _mean_overall(owner)) / 160
    chance += PLAYING_TIMES[playing_time]["bonus"]
    if player.overall >= _key_threshold(owner):
        chance -= 0.20
    if len(owner.squad) <= 18:
        chance -= 0.25
    chance = max(0.08, min(0.90, chance))
    rng = rng or _loan_rng(state, f"in-{player_id}")
    accepted = rng.random() < chance
    entry = {
        "date": state.date,
        "player_id": player.id,
        "player_name": player.name,
        "parent_club_id": owner.id,
        "parent_club_name": owner.name,
        "loan_club_id": user.id,
        "loan_club_name": user.name,
        "wage_share": wage_share,
        "playing_time": playing_time,
        "fee": fee,
        "accepted": accepted,
        "chance": round(chance, 3),
        "direction": "in",
    }
    if not accepted:
        entry["message"] = f"{owner.name} rechaza ceder a {player.name} en estas condiciones."
        state.loan_history.append(entry)
        state.loan_history = state.loan_history[-50:]
        state.inbox.append(
            {"date": state.date, "from": "Secretaría técnica", "subject": "Cesión rechazada", "body": entry["message"]}
        )
        return {"ok": True, "accepted": False, "message": entry["message"], "entry": entry}
    owner.players.remove(player)
    user.players.append(player)
    player.team_name = user.name
    player.league = user.league
    loan = _loan_entry(state, player, owner, user, wage_share, playing_time, fee, incoming=True)
    player.loan = loan
    state.loans.append(loan)
    user.budget -= fee
    owner.budget += fee
    entry["message"] = f"{player.name} llega cedido desde {owner.name}."
    state.loan_history.append(entry)
    state.loan_history = state.loan_history[-50:]
    state.inbox.append(
        {"date": state.date, "from": "Secretaría técnica", "subject": "Cesión cerrada", "body": entry["message"]}
    )
    return {"ok": True, "accepted": True, "message": entry["message"], "loan": loan, "entry": entry}


def offer_loan_out(
    state: GameState,
    player_id: str,
    club_id: str,
    wage_share: int = 50,
    playing_time: str = "rotacion",
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """Ofrece un jugador propio a otro club."""
    player, owner = _find_player(state, player_id)
    borrower = state.teams.get(club_id)
    if player is None or owner is None or owner.id != state.club_id:
        return {"ok": False, "message": "Ese jugador no está en tu plantilla."}
    if borrower is None or borrower.id == owner.id:
        return {"ok": False, "message": "El club de destino no es válido."}
    if player.loan:
        return {"ok": False, "message": "El jugador ya está cedido."}
    if len(borrower.squad) >= 25:
        return {"ok": False, "message": "El club de destino no tiene hueco en la plantilla."}
    wage_share = max(0, min(100, int(wage_share)))
    if playing_time not in PLAYING_TIMES:
        playing_time = "rotacion"
    fee = _loan_fee(player, wage_share)
    if borrower.budget < fee:
        return {"ok": False, "message": "El club de destino no puede pagar la tasa de cesión."}
    chance = 0.50 + (player.overall - _mean_overall(borrower)) / 140
    chance += (wage_share - 50) / 250 + PLAYING_TIMES[playing_time]["bonus"]
    if player.overall < _key_threshold(borrower):
        chance -= 0.10
    chance = max(0.08, min(0.90, chance))
    rng = rng or _loan_rng(state, f"out-{player_id}-{club_id}")
    accepted = rng.random() < chance
    entry = {
        "date": state.date,
        "player_id": player.id,
        "player_name": player.name,
        "parent_club_id": owner.id,
        "parent_club_name": owner.name,
        "loan_club_id": borrower.id,
        "loan_club_name": borrower.name,
        "wage_share": wage_share,
        "playing_time": playing_time,
        "fee": fee,
        "accepted": accepted,
        "chance": round(chance, 3),
        "direction": "out",
    }
    if not accepted:
        entry["message"] = f"{borrower.name} rechaza la cesión de {player.name}."
        state.loan_history.append(entry)
        state.loan_history = state.loan_history[-50:]
        state.inbox.append(
            {"date": state.date, "from": "Secretaría técnica", "subject": "Cesión rechazada", "body": entry["message"]}
        )
        return {"ok": True, "accepted": False, "message": entry["message"], "entry": entry}
    owner.players.remove(player)
    borrower.players.append(player)
    player.team_name = borrower.name
    player.league = borrower.league
    loan = _loan_entry(state, player, owner, borrower, wage_share, playing_time, fee, incoming=False)
    player.loan = loan
    state.loans.append(loan)
    borrower.budget -= fee
    owner.budget += fee
    entry["message"] = f"{player.name} sale cedido a {borrower.name}."
    state.loan_history.append(entry)
    state.loan_history = state.loan_history[-50:]
    state.inbox.append(
        {"date": state.date, "from": "Secretaría técnica", "subject": "Cesión cerrada", "body": entry["message"]}
    )
    return {"ok": True, "accepted": True, "message": entry["message"], "loan": loan, "entry": entry}


def _loan_payload(state: GameState, loan: dict[str, Any]) -> dict[str, Any]:
    player = next(
        (p for team in state.teams.values() for p in team.players if p.id == loan.get("player_id")),
        None,
    )
    return {
        **loan,
        "is_incoming": loan.get("loan_club_id") == state.club_id,
        "player_overall": round(float(player.overall), 1) if player else None,
        "player_position": player.subposition if player else "",
        "player_age": player.age if player else None,
    }


def loan_overview(state: GameState) -> dict[str, Any]:
    return {
        "window": market_window(state),
        "window_text": market_window_text(state),
        "squad_size": len(state.user_team.squad),
        "targets": loan_targets(state),
        "outgoing": outgoing_candidates(state),
        "active": [_loan_payload(state, loan) for loan in state.loans],
        "history": list(reversed(state.loan_history[-15:])),
        "playing_times": [{"id": key, "label": value["label"]} for key, value in PLAYING_TIMES.items()],
    }


def return_loans(state: GameState) -> list[dict[str, Any]]:
    """Devuelve a todos los cedidos a su club de origen al cerrar la temporada."""
    returned: list[dict[str, Any]] = []
    for loan in list(state.loans):
        player = next(
            (p for team in state.teams.values() for p in team.players if p.id == loan.get("player_id")),
            None,
        )
        parent = state.teams.get(str(loan.get("parent_club_id", "")))
        current = state.teams.get(str(loan.get("loan_club_id", "")))
        if player is None or parent is None:
            continue
        if current is not None and player in current.players:
            current.players.remove(player)
        if player not in parent.players:
            parent.players.append(player)
        player.team_name = parent.name
        player.league = parent.league
        player.loan = {}
        entry = {
            **loan,
            "returned_on": state.date,
            "apps": int(getattr(player, "apps", 0)),
            "goals": int(getattr(player, "season_goals", 0)),
            "assists": int(getattr(player, "season_assists", 0)),
            "rating": round(float(getattr(player, "rating", 0.0)), 2),
        }
        state.loan_history.append(entry)
        returned.append(entry)
        state.inbox.append(
            {
                "date": state.date,
                "from": "Secretaría técnica",
                "subject": f"Fin de cesión: {player.name}",
                "body": f"{player.name} vuelve a {parent.name} tras su cesión en {loan.get('loan_club_name', '')}.",
            }
        )
    state.loans = []
    state.loan_history = state.loan_history[-80:]
    return returned
