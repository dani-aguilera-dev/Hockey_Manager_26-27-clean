"""Negociaciones de fichajes, ventas y renovaciones.

El sistema antiguo resolvía una oferta en una sola tirada. Este módulo añade
una capa de negociación con contraofertas, rondas, paciencia y cierre. Se
mantienen las funciones antiguas de ``market.py`` para no romper partidas ni
tests; la interfaz nueva usa estas funciones.
"""

from __future__ import annotations

import zlib
from datetime import date, timedelta
from typing import Any

from .market import (
    _can_afford,
    _club_value,
    _complete_buy_transfer,
    _contract_until,
    _offer_value,
    accept_incoming_offer,
    asking_price,
    market_window,
)
from .models import GameState, PlayerState, TeamState

MAX_ROUNDS = 3
MAX_NEGOTIATIONS = 40


def _minimum_salary(player: PlayerState) -> int:
    return int(max(5000, (player.overall - 45) * 900))


def _find_player(state: GameState, player_id: str) -> tuple[PlayerState | None, TeamState | None, bool]:
    for team in state.teams.values():
        for player in team.players:
            if player.id == player_id:
                return player, team, False
    player = next((item for item in state.free_agents if item.id == player_id), None)
    return player, None, player is not None


def _open_negotiation(state: GameState, player_id: str, kind: str) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in reversed(state.negotiations)
            if item.get("player_id") == player_id and item.get("kind") == kind and item.get("status") == "open"
        ),
        None,
    )


def _negotiation_id(state: GameState, player_id: str, kind: str) -> str:
    raw = f"{state.seed}|{state.season}|{state.date}|{kind}|{player_id}|{len(state.negotiations)}"
    return f"NG-{zlib.crc32(raw.encode('utf-8')) & 0xFFFFFFFF:08x}"


def _add_negotiation(state: GameState, negotiation: dict[str, Any]) -> None:
    state.negotiations = (state.negotiations + [negotiation])[-MAX_NEGOTIATIONS:]


def _update_negotiation(state: GameState, negotiation: dict[str, Any]) -> None:
    for index, item in enumerate(state.negotiations):
        if item.get("id") == negotiation.get("id"):
            state.negotiations[index] = negotiation
            return
    _add_negotiation(state, negotiation)


def _history_entry(round_no: int, actor: str, offer: dict[str, int], message: str, day: date) -> dict[str, Any]:
    return {
        "round": round_no,
        "actor": actor,
        "offer": dict(offer),
        "message": message,
        "date": day.isoformat(),
    }


def _buy_demands(
    state: GameState,
    player: PlayerState,
    seller: TeamState | None,
    salary: int,
) -> tuple[int, int]:
    buyer = state.user_team
    if seller is None:
        seller_ask = 0
    else:
        seller_ask = max(asking_price(player), int(_club_value(player) * 1.04))
        key_players = sorted(seller.players, key=lambda item: item.overall, reverse=True)[:3]
        if player in key_players:
            seller_ask = int(seller_ask * 1.14)
        if player.transfer_listed:
            seller_ask = int(seller_ask * 0.93)
    player_ask = max(_minimum_salary(player), int(max(player.salary * 1.10, salary * 1.04)))
    if player.age >= 32:
        player_ask = int(player_ask * 0.95)
    if buyer.manager_rating >= 70:
        player_ask = int(player_ask * 0.97)
    if player.relationship >= 65:
        player_ask = int(player_ask * 0.97)
    return int(seller_ask), int(player_ask)


def _complete_buy(
    state: GameState,
    player: PlayerState,
    seller: TeamState | None,
    fee: int,
    salary: int,
    years: int,
    free_agent: bool,
) -> dict[str, Any]:
    buyer = state.user_team
    if market_window(state) == "cerrado":
        pending = {
            "id": f"PT-{state.round}-{zlib.crc32(player.id.encode('utf-8')) % 10000}",
            "type": "compra",
            "player_id": player.id,
            "player_name": player.name,
            "from_club_id": seller.id if seller else "",
            "to_club_id": buyer.id,
            "fee": int(fee),
            "salary": int(salary),
            "years": int(years),
            "free_agent": free_agent,
            "created": state.date,
            "status": "pendiente_ventana",
        }
        state.pending_transfers.append(pending)
        return {
            "ok": True,
            "pending": True,
            "message": f"Acuerdo con {player.name} cerrado. Se hará efectivo cuando abra el mercado.",
            "pending_transfer": pending,
        }
    entry = _complete_buy_transfer(state, buyer, seller, player, int(fee), int(salary), int(years), free_agent)
    return {
        "ok": True,
        "pending": False,
        "message": f"Fichado {player.name} por {fee:,} €.".replace(",", "."),
        "entry": entry,
    }


def _new_negotiation(
    state: GameState,
    kind: str,
    player: PlayerState,
    club: TeamState | None,
    offer: dict[str, int],
    ask: dict[str, int],
    message: str,
) -> dict[str, Any]:
    day = date.fromisoformat(state.date)
    negotiation = {
        "id": _negotiation_id(state, player.id, kind),
        "kind": kind,
        "status": "open",
        "player_id": player.id,
        "player_name": player.name,
        "club_id": club.id if club else "",
        "club_name": club.name if club else "Agente libre",
        "round": 1,
        "max_rounds": MAX_ROUNDS,
        "patience": MAX_ROUNDS,
        "offer": dict(offer),
        "ask": dict(ask),
        "message": message,
        "history": [_history_entry(1, "user", offer, message, day)],
        "created": state.date,
        "updated": state.date,
    }
    _add_negotiation(state, negotiation)
    return negotiation


def start_transfer_negotiation(
    state: GameState,
    player_id: str,
    fee: int,
    salary: int,
    years: int,
) -> dict[str, Any]:
    """Abre una negociación de compra. Si la oferta ya es suficiente, cierra."""
    player, seller, free_agent = _find_player(state, player_id)
    if player is None:
        return {"ok": False, "message": "Jugador no encontrado."}
    if seller and seller.id == state.club_id:
        return {"ok": False, "message": "Ese jugador ya es tuyo."}
    if seller and len(seller.players) <= 16:
        return {"ok": False, "message": f"{seller.name} no quiere quedarse sin efectivos."}
    if fee < 0 or salary <= 0 or years < 1:
        return {"ok": False, "message": "Oferta no válida."}
    if salary < _minimum_salary(player) and not free_agent:
        return {
            "ok": False,
            "message": f"{player.name} pide al menos {_minimum_salary(player):,} € de salario.".replace(",", "."),
        }
    if not _can_afford(state.user_team, fee):
        return {"ok": False, "message": "No tienes presupuesto suficiente para esa oferta."}

    existing = _open_negotiation(state, player_id, "buy")
    if existing:
        return {"ok": True, "negotiation": existing, "message": existing.get("message", "Negociación abierta.")}

    seller_ask, player_ask = _buy_demands(state, player, seller, salary)
    offer = {"fee": int(fee), "salary": int(salary), "years": int(years)}
    ask = {"fee": seller_ask, "salary": player_ask, "years": int(years)}
    if fee >= seller_ask and salary >= player_ask:
        result = _complete_buy(state, player, seller, fee, salary, years, free_agent)
        result["negotiation"] = {
            "id": "",
            "kind": "buy",
            "status": "accepted",
            "player_id": player.id,
            "player_name": player.name,
            "club_name": seller.name if seller else "Agente libre",
            "offer": offer,
            "ask": ask,
            "message": result["message"],
            "round": 1,
            "history": [],
        }
        return result

    counter_fee = max(fee, int((fee + seller_ask) / 2))
    counter_salary = max(salary, int((salary + player_ask) / 2))
    ask["fee"] = int(seller_ask)
    ask["salary"] = int(player_ask)
    negotiation = _new_negotiation(
        state,
        "buy",
        player,
        seller,
        offer,
        ask,
        f"{seller.name if seller else 'El agente'} pide {seller_ask:,} € y {player.name} pide {player_ask:,} € de salario.".replace(",", "."),
    )
    negotiation["counter"] = {"fee": counter_fee, "salary": counter_salary, "years": int(years)}
    return {"ok": True, "negotiation": negotiation, "message": negotiation["message"]}


def _complete_renewal(state: GameState, player: PlayerState, salary: int, years: int) -> dict[str, Any]:
    team = state.user_team
    player.salary = int(salary)
    player.contract_until = _contract_until(int(state.season[:4]), int(years))
    state.market_history.append(
        {
            "type": "renovacion",
            "round": state.round,
            "season": state.season,
            "player": player.name,
            "overall": round(player.overall, 1),
            "from": team.name,
            "to": team.name,
            "fee": 0,
            "salary": int(salary),
        }
    )
    return {"ok": True, "message": f"{player.name} renueva hasta {player.contract_until}.", "accepted": True}


def _renewal_ask(state: GameState, player: PlayerState, salary: int) -> int:
    ask = max(_minimum_salary(player), int(player.salary * 1.06), int(salary * 1.03))
    if player.rating >= 7.0 or player.season_goals >= 5:
        ask = int(ask * 1.04)
    if player.age <= 24:
        ask = int(ask * 1.04)
    if player.relationship >= 65:
        ask = int(ask * 0.96)
    if player.morale <= 8:
        ask = int(ask * 1.03)
    return max(5000, ask)


def start_renewal_negotiation(state: GameState, player_id: str, salary: int, years: int) -> dict[str, Any]:
    player = next((item for item in state.user_team.players if item.id == player_id), None)
    if player is None:
        return {"ok": False, "message": "Jugador no encontrado."}
    if salary <= 0 or years < 1:
        return {"ok": False, "message": "Contrato no válido."}
    existing = _open_negotiation(state, player_id, "renew")
    if existing:
        return {"ok": True, "negotiation": existing, "message": existing.get("message", "Renovación abierta.")}
    ask_salary = _renewal_ask(state, player, salary)
    offer = {"fee": 0, "salary": int(salary), "years": int(years)}
    ask = {"fee": 0, "salary": int(ask_salary), "years": int(max(2, years))}
    if salary >= ask_salary:
        result = _complete_renewal(state, player, salary, years)
        result["negotiation"] = {
            "id": "",
            "kind": "renew",
            "status": "accepted",
            "player_id": player.id,
            "player_name": player.name,
            "club_name": state.user_team.name,
            "offer": offer,
            "ask": ask,
            "message": result["message"],
            "round": 1,
            "history": [],
        }
        return result
    negotiation = _new_negotiation(
        state,
        "renew",
        player,
        state.user_team,
        offer,
        ask,
        f"{player.name} pide {ask_salary:,} € anuales para renovar.".replace(",", "."),
    )
    negotiation["counter"] = {"fee": 0, "salary": int((salary + ask_salary) / 2), "years": int(years)}
    return {"ok": True, "negotiation": negotiation, "message": negotiation["message"]}


def _respond_buy(
    state: GameState,
    negotiation: dict[str, Any],
    action: str,
    fee: int | None,
    salary: int | None,
    years: int | None,
) -> dict[str, Any]:
    player, seller, free_agent = _find_player(state, negotiation["player_id"])
    if player is None:
        negotiation["status"] = "rejected"
        _update_negotiation(state, negotiation)
        return {"ok": False, "message": "El jugador ya no está disponible."}
    day = date.fromisoformat(state.date)
    offer = dict(negotiation.get("offer", {}))
    ask = dict(negotiation.get("ask", {}))
    if action == "walk":
        negotiation["status"] = "walked"
        negotiation["message"] = "Has retirado la negociación."
        negotiation["updated"] = state.date
        _update_negotiation(state, negotiation)
        return {"ok": True, "negotiation": negotiation, "message": negotiation["message"]}
    if action == "accept":
        fee = int(ask.get("fee", 0))
        salary = int(ask.get("salary", 0))
        years = int(ask.get("years", offer.get("years", 3)))
    else:
        fee = int(fee if fee is not None else offer.get("fee", 0))
        salary = int(salary if salary is not None else offer.get("salary", 0))
        years = int(years if years is not None else offer.get("years", 3))
    if fee < 0 or salary <= 0 or years < 1:
        return {"ok": False, "message": "Oferta no válida."}
    if not _can_afford(state.user_team, fee):
        return {"ok": False, "message": "No tienes presupuesto suficiente para esa oferta."}
    offer = {"fee": fee, "salary": salary, "years": years}
    if action == "accept":
        result = _complete_buy(state, player, seller, fee, salary, years, free_agent)
        negotiation["status"] = "pending_window" if result.get("pending") else "accepted"
        negotiation["offer"] = offer
        negotiation["message"] = result["message"]
        negotiation["updated"] = state.date
        negotiation["history"] = (negotiation.get("history", []) + [_history_entry(negotiation["round"], "user", offer, result["message"], day)])[-10:]
        _update_negotiation(state, negotiation)
        return {**result, "negotiation": negotiation}
    seller_ask, player_ask = _buy_demands(state, player, seller, salary)
    if fee >= seller_ask and salary >= player_ask:
        result = _complete_buy(state, player, seller, fee, salary, years, free_agent)
        negotiation["status"] = "pending_window" if result.get("pending") else "accepted"
        negotiation["offer"] = offer
        negotiation["message"] = result["message"]
        negotiation["updated"] = state.date
        negotiation["history"] = (negotiation.get("history", []) + [_history_entry(negotiation["round"], "user", offer, result["message"], day)])[-10:]
        _update_negotiation(state, negotiation)
        return {**result, "negotiation": negotiation}
    negotiation["round"] = int(negotiation.get("round", 1)) + 1
    if negotiation["round"] > int(negotiation.get("max_rounds", MAX_ROUNDS)):
        negotiation["status"] = "rejected"
        negotiation["message"] = "La otra parte se ha cansado de esperar. Negociación cerrada."
        _update_negotiation(state, negotiation)
        return {"ok": False, "negotiation": negotiation, "message": negotiation["message"]}
    ask = {"fee": seller_ask, "salary": player_ask, "years": years}
    negotiation["offer"] = offer
    negotiation["ask"] = ask
    negotiation["counter"] = {
        "fee": max(fee, int((fee + seller_ask) / 2)),
        "salary": max(salary, int((salary + player_ask) / 2)),
        "years": years,
    }
    negotiation["message"] = (
        f"Contraoferta: {seller.name if seller else 'el agente'} pide {seller_ask:,} € y "
        f"{player.name} pide {player_ask:,} € de salario."
    ).replace(",", ".")
    negotiation["history"] = (
        negotiation.get("history", [])
        + [_history_entry(negotiation["round"], "user", offer, negotiation["message"], day)]
    )[-10:]
    negotiation["updated"] = state.date
    _update_negotiation(state, negotiation)
    return {"ok": True, "negotiation": negotiation, "message": negotiation["message"]}


def _respond_renewal(
    state: GameState,
    negotiation: dict[str, Any],
    action: str,
    salary: int | None,
    years: int | None,
) -> dict[str, Any]:
    player = next((item for item in state.user_team.players if item.id == negotiation["player_id"]), None)
    if player is None:
        negotiation["status"] = "rejected"
        _update_negotiation(state, negotiation)
        return {"ok": False, "message": "El jugador ya no está disponible."}
    day = date.fromisoformat(state.date)
    offer = dict(negotiation.get("offer", {}))
    ask = dict(negotiation.get("ask", {}))
    if action == "walk":
        negotiation["status"] = "walked"
        negotiation["message"] = "Has retirado la renovación."
        negotiation["updated"] = state.date
        _update_negotiation(state, negotiation)
        return {"ok": True, "negotiation": negotiation, "message": negotiation["message"]}
    if action == "accept":
        salary = int(ask.get("salary", 0))
        years = int(ask.get("years", offer.get("years", 3)))
    else:
        salary = int(salary if salary is not None else offer.get("salary", 0))
        years = int(years if years is not None else offer.get("years", 3))
    if salary <= 0 or years < 1:
        return {"ok": False, "message": "Contrato no válido."}
    offer = {"fee": 0, "salary": salary, "years": years}
    if action == "accept":
        result = _complete_renewal(state, player, salary, years)
        negotiation["status"] = "accepted"
        negotiation["offer"] = offer
        negotiation["message"] = result["message"]
        negotiation["updated"] = state.date
        _update_negotiation(state, negotiation)
        return {**result, "negotiation": negotiation}
    ask_salary = _renewal_ask(state, player, salary)
    if salary >= ask_salary:
        result = _complete_renewal(state, player, salary, years)
        negotiation["status"] = "accepted"
        negotiation["offer"] = offer
        negotiation["message"] = result["message"]
        negotiation["updated"] = state.date
        _update_negotiation(state, negotiation)
        return {**result, "negotiation": negotiation}
    negotiation["round"] = int(negotiation.get("round", 1)) + 1
    if negotiation["round"] > int(negotiation.get("max_rounds", MAX_ROUNDS)):
        negotiation["status"] = "rejected"
        negotiation["message"] = f"{player.name} se ha cansado de esperar. Renovación cerrada."
        _update_negotiation(state, negotiation)
        return {"ok": False, "negotiation": negotiation, "message": negotiation["message"]}
    ask = {"fee": 0, "salary": ask_salary, "years": int(max(2, years))}
    negotiation["offer"] = offer
    negotiation["ask"] = ask
    negotiation["counter"] = {"fee": 0, "salary": int((salary + ask_salary) / 2), "years": years}
    negotiation["message"] = f"{player.name} pide {ask_salary:,} € anuales para renovar.".replace(",", ".")
    negotiation["updated"] = state.date
    _update_negotiation(state, negotiation)
    return {"ok": True, "negotiation": negotiation, "message": negotiation["message"]}


def respond_negotiation(
    state: GameState,
    negotiation_id: str,
    action: str,
    fee: int | None = None,
    salary: int | None = None,
    years: int | None = None,
) -> dict[str, Any]:
    negotiation = next((item for item in state.negotiations if item.get("id") == negotiation_id), None)
    if negotiation is None:
        return {"ok": False, "message": "Negociación no encontrada."}
    if negotiation.get("status") != "open":
        return {"ok": False, "message": "La negociación ya está cerrada.", "negotiation": negotiation}
    if action not in ("accept", "counter", "walk"):
        return {"ok": False, "message": "Acción no válida."}
    if negotiation.get("kind") == "renew":
        return _respond_renewal(state, negotiation, action, salary, years)
    return _respond_buy(state, negotiation, action, fee, salary, years)


def counter_incoming_offer(
    state: GameState,
    offer_id: str,
    fee: int,
    salary: int | None = None,
    years: int | None = None,
) -> dict[str, Any]:
    offer = next((item for item in state.transfer_offers if item.get("id") == offer_id), None)
    if offer is None:
        return {"ok": False, "message": "Oferta no encontrada."}
    buyer = state.teams.get(offer.get("from_club_id"))
    player = next((item for item in state.user_team.players if item.id == offer.get("player_id")), None)
    if buyer is None or player is None:
        return {"ok": False, "message": "La oferta ya no es válida."}
    if fee <= 0:
        return {"ok": False, "message": "La contraoferta debe ser mayor que cero."}
    max_affordable = min(int(buyer.transfer_budget), int(_offer_value(player) * 1.22))
    if fee > max_affordable:
        return {
            "ok": False,
            "message": f"{buyer.name} no puede llegar a {fee:,} €. Su límite estimado es {max_affordable:,} €.".replace(",", "."),
            "counter": {"fee": max_affordable, "salary": int(offer.get("salary", 0)), "years": int(offer.get("years", 3))},
        }
    if fee <= int(_offer_value(player) * 1.08):
        offer["fee"] = int(fee)
        if salary:
            offer["salary"] = int(salary)
        if years:
            offer["years"] = int(years)
        result = accept_incoming_offer(state, offer_id)
        return {**result, "accepted": True, "offer": offer}
    counter_fee = max(int(fee), int((fee + _offer_value(player)) / 2))
    counter_fee = min(counter_fee, max_affordable)
    offer["fee"] = counter_fee
    if salary:
        offer["salary"] = int(salary)
    if years:
        offer["years"] = int(years)
    return {
        "ok": True,
        "accepted": False,
        "message": f"{buyer.name} estudia la contraoferta y ofrece {counter_fee:,} €.".replace(",", "."),
        "offer": offer,
        "counter": {"fee": counter_fee, "salary": offer["salary"], "years": offer["years"]},
    }
