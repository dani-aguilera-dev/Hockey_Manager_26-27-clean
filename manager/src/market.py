"""Mercado de fichajes, contratos y contratación de staff (Fase 3A)."""

from __future__ import annotations

import random
import zlib
from datetime import date, timedelta
from typing import Any

from .competitions import competition
from .models import GameState, PlayerState, StaffMember, TeamState

STAFF_LABELS = {
    "head_coach": "Entrenador",
    "assistant": "Segundo entrenador",
    "fitness_coach": "Preparador físico",
    "gk_coach": "Entrenador de porteros",
    "performance_analyst": "Analista de rendimiento",
    "scout": "Ojeador",
    "physio": "Fisioterapeuta",
    "technical_director": "Director deportivo",
    "commercial_director": "Director comercial",
    "marketing_manager": "Responsable de marketing",
    "doctor": "Médico",
    "psychologist": "Psicólogo",
    "delegate": "Delegado",
    "additional": "Staff adicional",
}
STAFF_BASE_SALARY = {
    "head_coach": 60000,
    "assistant": 42000,
    "fitness_coach": 30000,
    "gk_coach": 24000,
    "performance_analyst": 26000,
    "scout": 20000,
    "physio": 28000,
    "technical_director": 45000,
    "commercial_director": 40000,
    "marketing_manager": 32000,
    "doctor": 26000,
    "psychologist": 24000,
    "delegate": 12000,
    "additional": 15000,
}
STAFF_NAMES = [
    "Jordi Pons",
    "Marc Ferrer",
    "Laia Soler",
    "Pere Roca",
    "Núria Camps",
    "Xavier Puig",
    "Marta Vidal",
    "Oriol Serra",
    "Anna Bosch",
    "Pau Mas",
    "Carles Riera",
    "Elena Font",
    "Sergi Vidal",
    "Clara Pujol",
    "Toni Sala",
]


def market_window(state: GameState) -> str:
    if state.phase != "regular":
        return "cerrado"
    from datetime import date, timedelta

    today = date.fromisoformat(state.date)
    year = int(state.season[:4])
    if date(year, 8, 1) <= today <= date(year, 9, 30):
        return "verano"
    if date(year + 1, 1, 1) <= today <= date(year + 1, 1, 31):
        return "invierno"
    return "cerrado"


def market_window_text(state: GameState) -> str:
    w = market_window(state)
    if w == "verano":
        return "Mercado de verano abierto"
    if w == "invierno":
        return "Mercado de invierno abierto"
    return "Mercado cerrado"


def _rng(state: GameState, salt: int = 0) -> random.Random:
    return random.Random(state.seed * 1000 + state.round * 71 + salt)


def market_players(
    state: GameState,
    limit: int = 40,
    max_value: int | None = None,
    position: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    min_overall: float | None = None,
    max_overall: float | None = None,
    league: str | None = None,
    club_id: str | None = None,
    query: str | None = None,
    attribute: str | None = None,
    min_attribute: int | None = None,
    listed_only: bool = False,
    free_agents_only: bool = False,
) -> list[PlayerState]:
    """Mercado global: cualquier club de cualquier liga y agentes libres."""
    pool: list[PlayerState] = []
    owners: dict[str, TeamState] = {}
    if not free_agents_only:
        for team in state.teams.values():
            if team.id == state.club_id:
                continue
            if league and team.league != league:
                continue
            if club_id and team.id != club_id:
                continue
            for player in team.players:
                owners[player.id] = team
                pool.append(player)
    if free_agents_only:
        pool = [player for player in state.free_agents if not league or player.league == league]
    elif not league and not club_id:
        pool += list(state.free_agents)
    if min_age is not None:
        pool = [p for p in pool if p.age >= int(min_age)]
    if max_age is not None:
        pool = [p for p in pool if p.age <= int(max_age)]
    if min_overall is not None:
        pool = [p for p in pool if p.overall >= float(min_overall)]
    if max_overall is not None:
        pool = [p for p in pool if p.overall <= float(max_overall)]
    if max_value is not None:
        pool = [p for p in pool if asking_price(p) <= max_value]
    if position:
        pool = [p for p in pool if p.subposition == position]
    if listed_only:
        pool = [p for p in pool if p.transfer_listed]
    if attribute:
        pool = [p for p in pool if int(p.attributes.get(attribute, 0)) >= int(min_attribute or 0)]
    if query:
        needle = query.lower()
        pool = [
            p
            for p in pool
            if needle in p.name.lower()
            or needle in p.archetype.lower()
            or needle in p.subposition.lower()
            or needle in (owners[p.id].name if p.id in owners else "Agente libre").lower()
        ]
    pool.sort(key=lambda p: (-p.overall, p.age, p.name))
    return pool[:limit]


def asking_price(player: PlayerState) -> int:
    if player.team_name == "Agente libre":
        return 0
    if player.transfer_asking_price:
        return int(player.transfer_asking_price)
    return _club_value(player)


def scout_range(player: PlayerState, scout_rating: int) -> str:
    error = max(2, int(13 - scout_rating / 8))
    low = max(1, int(player.overall) - error)
    high = min(99, int(player.overall) + error)
    return f"{low}-{high}"


def _record_partial_career(player: PlayerState, club: TeamState, state: GameState) -> None:
    if not (player.apps or player.season_goals or player.season_assists):
        return
    entry = {
        "season": state.season,
        "club": club.name,
        "league": club.league,
        "apps": player.apps,
        "goals": player.season_goals,
        "assists": player.season_assists,
        "rating": round(player.rating, 2),
        "overall": round(player.overall, 1),
        "partial": True,
    }
    player.career = [e for e in player.career if not (e.get("season") == state.season and e.get("club") == club.name)]
    player.career.append(entry)
    player.career = player.career[-30:]


def _contract_until(start_year: int, years: int) -> str:
    return f"{start_year + max(1, years)}-06-30"


def _club_value(player: PlayerState) -> int:
    age_factor = (
        1.25
        if player.age <= 24
        else (1.0 if player.age <= 29 else (0.70 if player.age <= 32 else (0.45 if player.age <= 34 else 0.25)))
    )
    factors = {
        "DHA": 1.0,
        "DHB": 0.78,
        "1A": 0.42,
        "1N": 0.40,
        "1M": 0.40,
        "1G": 0.40,
        "1C": 0.40,
        "1V": 0.40,
        "SUP": 0.55,
        "CAT1": 0.34,
    }
    league_factor = factors.get(player.league, 0.78)
    base = int((max(1, player.overall - 40) ** 2) * 180 * age_factor * league_factor)
    return max(int(player.value * 1.10), base, 50000 if player.league in ("DHA", "DHB") else 8000)


def _complete_buy_transfer(
    state: GameState,
    buyer: TeamState,
    seller: TeamState | None,
    player: PlayerState,
    fee: int,
    salary: int,
    years: int,
    free_agent: bool,
    source: str = "transferencia",
) -> dict[str, Any]:
    if free_agent:
        state.free_agents = [p for p in state.free_agents if p.id != player.id]
    elif seller:
        seller.players.remove(player)
    buyer.players.append(player)
    player.team_name = buyer.name
    player.league = buyer.league
    player.salary = int(salary)
    player.contract_until = _contract_until(int(state.season[:4]), years)
    player.transfer_listed = False
    player.transfer_asking_price = 0
    if seller:
        _record_partial_career(player, seller, state)
    player.apps = player.season_goals = player.season_assists = 0
    player.rating_sum = 0.0
    player.fatigue = 0
    player.injury = 0
    player.suspension = 0
    buyer.transfer_budget -= int(fee)
    if seller:
        seller.budget += int(fee)
    entry = {
        "type": source,
        "round": state.round,
        "season": state.season,
        "player": player.name,
        "overall": round(player.overall, 1),
        "from": seller.name if seller else "Agente libre",
        "to": buyer.name,
        "fee": int(fee),
        "salary": int(salary),
    }
    state.market_history.append(entry)
    return entry


def make_transfer_offer(
    state: GameState, player_id: str, fee: int, salary: int, years: int, rng: random.Random | None = None
) -> dict[str, Any]:
    buyer = state.user_team
    seller = None
    player = None
    for t in state.teams.values():
        for p in t.players:
            if p.id == player_id:
                seller, player = t, p
                break
        if player:
            break
    free_agent = False
    if not player:
        player = next((p for p in state.free_agents if p.id == player_id), None)
        free_agent = player is not None
    if not player:
        return {"ok": False, "message": "Jugador no encontrado."}
    if seller and seller.id == buyer.id:
        return {"ok": False, "message": "Ese jugador ya es tuyo."}
    if seller and len(seller.players) <= 16:
        return {"ok": False, "message": f"{seller.name} no quiere quedarse sin efectivos."}
    if fee < 0 or salary <= 0 or years < 1:
        return {"ok": False, "message": "Oferta no válida."}
    minimum_salary = int(max(5000, (player.overall - 45) * 900))
    if salary < minimum_salary and not free_agent:
        return {
            "ok": False,
            "message": f"{player.name} pide al menos {minimum_salary:,} € de salario.".replace(",", "."),
        }
    if not _can_afford(buyer, fee):
        return {"ok": False, "message": f"No tienes dinero suficiente para una oferta de {fee:,} €.".replace(",", ".")}
    rng = rng or _rng(state, zlib.crc32(player_id.encode("utf-8")) % 1000)
    if not free_agent:
        value = _club_value(player)
        key_threshold = sorted(seller.players, key=lambda p: p.overall, reverse=True)[:3]
        key = player in key_threshold
        seller_prob = 0.35 + (fee / max(1, value) - 1.0) * 0.85 - (0.22 if key else 0.0)
        if player.transfer_listed:
            seller_prob += 0.18
        seller_prob += (buyer.manager_rating - 50) / 250
        seller_prob = max(0.04, min(0.95, seller_prob))
        if rng.random() > seller_prob:
            return {"ok": False, "message": f"{seller.name} rechaza la oferta por {player.name}. Pide más dinero."}
    else:
        fee = 0
    raise_ratio = (salary - player.salary) / max(10000, player.salary)
    player_prob = 0.20 + raise_ratio * 0.55 + (buyer.manager_rating - 50) / 220
    if years >= 3:
        player_prob += 0.08
    if player.age > 31:
        player_prob -= 0.08
    player_prob = max(0.08, min(0.95, player_prob))
    if rng.random() > player_prob:
        return {"ok": False, "message": f"{player.name} rechaza el contrato. Quiere un salario mayor o más años."}
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
            "message": f"Acuerdo con {player.name} registrado. Se hará efectivo cuando abra el mercado.",
            "pending_transfer": pending,
        }
    entry = _complete_buy_transfer(state, buyer, seller, player, int(fee), int(salary), int(years), free_agent)
    origin = seller.name if seller else "agente libre"
    return {
        "ok": True,
        "message": f"Fichado {player.name} ({origin}) por {fee:,} €.".replace(",", "."),
        "player": player,
        "entry": entry,
    }


def _ai_market_activity(state: GameState, rng: random.Random) -> None:
    """Movimientos entre clubes IA con presupuesto y salario coherentes."""
    teams = [t for t in state.teams.values() if t.id != state.club_id]
    if len(teams) < 4:
        return
    for _ in range(3):
        buyer, seller = rng.sample(teams, 2)
        if len(seller.players) <= 17:
            continue
        candidates = [p for p in seller.players if p.overall < max(x.overall for x in seller.players) - 2]
        if not candidates:
            continue
        player = rng.choice(candidates)
        fee = int(_club_value(player) * rng.uniform(0.90, 1.20))
        if not _can_afford(buyer, fee):
            continue
        salary = int(max(player.salary * rng.uniform(1.10, 1.30), (player.overall - 45) * 900))
        seller.players.remove(player)
        buyer.players.append(player)
        player.team_name = buyer.name
        player.league = buyer.league
        player.salary = salary
        player.contract_until = _contract_until(int(state.season[:4]), rng.randint(2, 4))
        _record_partial_career(player, seller, state)
        buyer.transfer_budget -= fee
        seller.budget += fee
        player.apps = player.season_goals = player.season_assists = 0
        player.rating_sum = 0.0
        player.fatigue = 0
        player.injury = 0
        player.suspension = 0
        state.market_history.append(
            {
                "type": "IA",
                "round": state.round,
                "season": state.season,
                "player": player.name,
                "overall": round(player.overall, 1),
                "from": seller.name,
                "to": buyer.name,
                "fee": fee,
                "salary": salary,
            }
        )


def _offer_value(player: PlayerState) -> int:
    if player.transfer_asking_price:
        return max(50000, int(player.transfer_asking_price))
    rating = player.rating if player.apps else 6.5
    multiplier = 0.88 + max(0.0, player.overall - 55) * 0.012 + max(0.0, rating - 6.5) * 0.06
    multiplier += min(0.16, player.season_goals * 0.012)
    return max(50000, int(_club_value(player) * multiplier))


def _can_afford(team: TeamState, fee: int) -> bool:
    """Un club no puede prometer más de lo que tiene en caja y fichajes."""
    return fee >= 0 and fee <= max(0, int(team.transfer_budget)) and fee <= max(0, int(team.budget))


def _buyers_for(state: GameState, fee: int) -> list[TeamState]:
    return [
        t
        for t in state.teams.values()
        if t.id != state.club_id and _can_afford(t, fee)
    ]


def _new_offer(state: GameState, player: PlayerState, buyer: TeamState, rng: random.Random, source: str) -> dict[str, Any] | None:
    value = _offer_value(player)
    fee = int(value * rng.uniform(0.92, 1.24))
    if player.transfer_asking_price:
        fee = max(int(player.transfer_asking_price), int(fee * 0.96))
    if not _can_afford(buyer, fee):
        return None
    salary = int(max(player.salary * rng.uniform(1.12, 1.48), (player.overall - 45) * 950))
    return {
        "id": f"OF-{state.round}-{date.fromisoformat(state.date).toordinal()}-{zlib.crc32(player.id.encode('utf-8')) % 10000}-{rng.randint(10, 99)}",
        "player_id": player.id,
        "player_name": player.name,
        "from_club_id": buyer.id,
        "from_club_name": buyer.name,
        "from_league": buyer.league,
        "fee": fee,
        "salary": salary,
        "years": rng.randint(2, 4),
        "source": source,
        "listed": bool(player.transfer_listed),
        "buyer_budget": int(buyer.transfer_budget),
        "buyer_cash": int(buyer.budget),
        "expires": (date.fromisoformat(state.date) + timedelta(days=10)).isoformat(),
        "status": "pendiente",
    }


def daily_transfer_activity(state: GameState, day: date, rng: random.Random | None = None) -> list[dict[str, Any]]:
    """Genera ofertas a lo largo de la simulación según lista, liga y rendimiento.

    El mercado cerrado no bloquea la recepción de ofertas: se pueden negociar
    y aceptar, pero la ejecución queda pendiente hasta la apertura.
    """
    process_pending_transfers(state, day)
    rng = rng or _rng(state, day.toordinal() + 53)
    # Las ofertas caducan si el club no responde.
    state.transfer_offers = [
        offer
        for offer in state.transfer_offers
        if not offer.get("expires") or date.fromisoformat(str(offer["expires"])) >= day
    ]
    user = state.user_team
    existing = {offer.get("player_id") for offer in state.transfer_offers}
    listed = [p for p in user.players if p.transfer_listed and p.id not in existing]
    high_performers = [
        p
        for p in user.players
        if p.id not in existing and not p.transfer_listed and (p.rating >= 7.0 or p.season_goals >= 3)
    ]
    candidates = [(p, 0.44, "lista") for p in listed] + [(p, 0.045, "rendimiento") for p in high_performers]
    new_offers = []
    for player, chance, source in candidates:
        if rng.random() > chance:
            continue
        value = _offer_value(player)
        buyers = _buyers_for(state, value)
        if not buyers:
            continue
        # Clubes de la misma categoría o superior tienen más peso.
        buyers.sort(key=lambda t: (competition(t.league).standard, t.transfer_budget), reverse=True)
        buyer = rng.choice(buyers[: max(1, min(8, len(buyers)))])
        offer = _new_offer(state, player, buyer, rng, source)
        if not offer:
            continue
        new_offers.append(offer)
        if len(new_offers) >= 3:
            break
    if new_offers:
        state.transfer_offers = (state.transfer_offers + new_offers)[-12:]
        state.market_offers_date = day.isoformat()
        state.daily_events = (
            state.daily_events
            + [
                {
                    "date": day.isoformat(),
                    "category": "Mercado",
                    "headline": f"{new_offers[0]['from_club_name']} pregunta por {new_offers[0]['player_name']}",
                    "body": "Hay una oferta real sobre la mesa. Revisa el mercado y decide si vendes o negocias.",
                    "important": True,
                    "team_id": user.id,
                    "player_id": new_offers[0]["player_id"],
                    "league": state.competition,
                    "type": "offer",
                }
            ]
        )[-240:]
    return new_offers


def generate_incoming_offers(state: GameState, rng: random.Random | None = None) -> list[dict]:
    if state.transfer_offers and state.market_offers_date == state.date:
        return state.transfer_offers
    rng = rng or _rng(state, 7)
    _ai_market_activity(state, rng)
    new_offers = daily_transfer_activity(state, date.fromisoformat(state.date), rng)
    state.market_offers_round = state.round
    state.market_offers_date = state.date
    return state.transfer_offers


def _complete_sale(
    state: GameState,
    buyer: TeamState,
    player: PlayerState,
    fee: int,
    salary: int,
    years: int,
    source: str = "venta",
) -> dict[str, Any]:
    user = state.user_team
    user.players.remove(player)
    buyer.players.append(player)
    player.team_name = buyer.name
    player.league = buyer.league
    player.salary = int(max(salary, (player.overall - 45) * 900))
    player.contract_until = _contract_until(int(state.season[:4]), int(years))
    player.transfer_listed = False
    player.transfer_asking_price = 0
    player.apps = player.season_goals = player.season_assists = 0
    player.rating_sum = 0.0
    buyer.transfer_budget -= int(fee)
    user.budget += int(fee)
    state.market_history.append(
        {
            "type": source,
            "round": state.round,
            "season": state.season,
            "player": player.name,
            "overall": round(player.overall, 1),
            "from": user.name,
            "to": buyer.name,
            "fee": int(fee),
            "salary": int(salary),
        }
    )
    return {"ok": True, "message": f"Vendido {player.name} a {buyer.name} por {fee:,} €.".replace(",", ".")}


def accept_incoming_offer(state: GameState, offer_id: str) -> dict[str, Any]:
    offer = next((o for o in state.transfer_offers if o.get("id") == offer_id), None)
    if not offer:
        return {"ok": False, "message": "Oferta no encontrada."}
    user = state.user_team
    buyer = state.teams.get(offer["from_club_id"])
    player = next((p for p in user.players if p.id == offer["player_id"]), None)
    if not buyer or not player:
        return {"ok": False, "message": "La oferta ya no es válida."}
    if not _can_afford(buyer, int(offer["fee"])):
        state.transfer_offers = [o for o in state.transfer_offers if o.get("id") != offer_id]
        return {"ok": False, "message": f"{buyer.name} ya no tiene dinero suficiente para pagar {offer['fee']:,} €.".replace(",", ".")}
    if market_window(state) == "cerrado":
        pending = {
            "id": f"PT-{state.round}-{zlib.crc32(player.id.encode('utf-8')) % 10000}",
            "type": "venta",
            "player_id": player.id,
            "player_name": player.name,
            "from_club_id": user.id,
            "to_club_id": buyer.id,
            "fee": int(offer["fee"]),
            "salary": int(offer["salary"]),
            "years": int(offer["years"]),
            "free_agent": False,
            "created": state.date,
            "status": "pendiente_ventana",
        }
        state.pending_transfers.append(pending)
        state.transfer_offers = [o for o in state.transfer_offers if o.get("id") != offer_id]
        return {
            "ok": True,
            "pending": True,
            "message": f"Venta de {player.name} acordada. Se hará efectiva cuando abra el mercado.",
            "pending_transfer": pending,
        }
    result = _complete_sale(state, buyer, player, int(offer["fee"]), int(offer["salary"]), int(offer["years"]))
    state.transfer_offers = [o for o in state.transfer_offers if o.get("id") != offer_id]
    return result


def process_pending_transfers(state: GameState, day: date | None = None) -> list[dict[str, Any]]:
    """Ejecuta acuerdos cerrados en ventana cerrada cuando el mercado abre."""
    if market_window(state) == "cerrado" or not state.pending_transfers:
        return []
    day = day or date.fromisoformat(state.date)
    processed = []
    remaining = []
    for pending in state.pending_transfers:
        player_id = pending.get("player_id", "")
        if pending.get("type") == "compra":
            buyer = state.user_team
            seller = state.teams.get(pending.get("from_club_id", ""))
            player = next((p for p in (seller.players if seller else state.free_agents) if p.id == player_id), None)
            if not player or not _can_afford(buyer, int(pending.get("fee", 0))):
                remaining.append(pending)
                continue
            _complete_buy_transfer(
                state,
                buyer,
                seller,
                player,
                int(pending.get("fee", 0)),
                int(pending.get("salary", 0)),
                int(pending.get("years", 1)),
                bool(pending.get("free_agent", False)),
                source="compra_ventana",
            )
            processed.append({**pending, "status": "ejecutado"})
        elif pending.get("type") == "venta":
            seller = state.user_team
            buyer = state.teams.get(pending.get("to_club_id", ""))
            player = next((p for p in seller.players if p.id == player_id), None)
            if not player or not buyer or not _can_afford(buyer, int(pending.get("fee", 0))):
                remaining.append(pending)
                continue
            _complete_sale(
                state,
                buyer,
                player,
                int(pending.get("fee", 0)),
                int(pending.get("salary", 0)),
                int(pending.get("years", 1)),
                source="venta_ventana",
            )
            processed.append({**pending, "status": "ejecutado"})
        else:
            remaining.append(pending)
            continue
        state.transfer_offers = [o for o in state.transfer_offers if o.get("player_id") != player_id]
    state.pending_transfers = remaining
    if processed:
        state.daily_events = (
            state.daily_events
            + [
                {
                    "date": day.isoformat(),
                    "category": "Mercado",
                    "headline": f"{len(processed)} acuerdo(s) de mercado ejecutados",
                    "body": "La ventana de transferencias ha abierto y los acuerdos pendientes se han hecho efectivos.",
                    "important": True,
                    "team_id": state.club_id,
                    "player_id": "",
                    "league": state.competition,
                    "type": "market_window",
                }
            ]
        )[-240:]
    return processed


def reject_incoming_offer(state: GameState, offer_id: str) -> None:
    state.transfer_offers = [o for o in state.transfer_offers if o.get("id") != offer_id]


def renew_contract(
    state: GameState, player_id: str, salary: int, years: int, rng: random.Random | None = None
) -> dict[str, Any]:
    team = state.user_team
    player = next((p for p in team.players if p.id == player_id), None)
    if not player:
        return {"ok": False, "message": "Jugador no encontrado."}
    if salary <= 0 or years < 1:
        return {"ok": False, "message": "Contrato no válido."}
    rng = rng or _rng(state, 19)
    raise_ratio = (salary - player.salary) / max(10000, player.salary)
    prob = 0.25 + raise_ratio * 0.65 + (team.morale - 10) / 60
    if years >= 3:
        prob += 0.08
    if player.age > 32:
        prob -= 0.12
    prob = max(0.05, min(0.95, prob))
    if rng.random() > prob:
        return {"ok": False, "message": f"{player.name} rechaza la renovación. Pide más salario o años."}
    player.salary = int(salary)
    player.contract_until = _contract_until(int(state.season[:4]), years)
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
    return {"ok": True, "message": f"{player.name} renueva hasta {player.contract_until}."}


def list_player_for_transfer(
    state: GameState, player_id: str, listed: bool, asking_price: int = 0
) -> dict[str, Any]:
    player = next((p for p in state.user_team.players if p.id == player_id), None)
    if not player:
        return {"ok": False, "message": "Jugador no encontrado."}
    player.transfer_listed = bool(listed)
    player.transfer_asking_price = max(0, int(asking_price)) if listed else 0
    state.market_history.append(
        {
            "type": "lista" if listed else "retirado",
            "round": state.round,
            "season": state.season,
            "player": player.name,
            "overall": round(player.overall, 1),
            "from": state.user_team.name,
            "to": "mercado" if listed else "plantilla",
            "fee": player.transfer_asking_price,
            "salary": player.salary,
        }
    )
    return {
        "ok": True,
        "message": f"{player.name} {'puesto en el mercado' if listed else 'retirado del mercado'}.",
        "player": player,
    }


def staff_market(
    state: GameState,
    limit: int = 30,
    role: str | None = None,
    min_rating: int | None = None,
    max_salary: int | None = None,
) -> list[dict[str, Any]]:
    """Empleados libres ficticios, pero coherentes con la categoría del club."""
    rng = _rng(state, 909)
    roles = [key for key in STAFF_LABELS if key not in ("head_coach",)]
    out = []
    used_names: set[str] = set()
    for index in range(limit * 2):
        chosen_role = role or rng.choice(roles)
        if chosen_role not in STAFF_LABELS:
            continue
        rating = max(48, min(88, 54 + int(competition(state.competition).standard * 0.22) + rng.randint(-9, 10)))
        if min_rating is not None and rating < int(min_rating):
            continue
        base = STAFF_BASE_SALARY.get(chosen_role, 25000)
        salary = int(base * (0.72 + rating / 190) * rng.uniform(0.92, 1.12))
        if max_salary is not None and salary > int(max_salary):
            continue
        name = rng.choice(STAFF_NAMES)
        if name in used_names:
            name = f"{name} {index + 1}"
        used_names.add(name)
        out.append(
            {
                "id": f"ST-{chosen_role}-{index}-{rng.randint(100, 999)}",
                "role": chosen_role,
                "role_label": STAFF_LABELS.get(chosen_role, chosen_role),
                "name": name,
                "rating": rating,
                "salary": salary,
                "contract_until": "2028-06-30",
                "source": "ficticio",
                "confidence": "media",
                "relationship": 50,
                "morale": 12,
            }
        )
        if len(out) >= limit:
            break
    return out


def hire_market_staff(state: GameState, candidate_id: str) -> dict[str, Any]:
    candidate = next((row for row in staff_market(state, limit=120) if row["id"] == candidate_id), None)
    if not candidate:
        return {"ok": False, "message": "El empleado ya no está disponible."}
    member = StaffMember(
        role=candidate["role"],
        name=candidate["name"],
        rating=candidate["rating"],
        salary=candidate["salary"],
        contract_until=candidate["contract_until"],
        source=candidate["source"],
        confidence=candidate["confidence"],
    )
    return hire_staff(state, member)


def staff_candidates(team: TeamState, role: str, rng: random.Random | None = None, count: int = 4) -> list[StaffMember]:
    rng = rng or random.Random(0)
    base = STAFF_BASE_SALARY.get(role, 25000)
    out = []
    for i in range(count):
        rating = max(50, min(85, team.assistant_rating + rng.randint(-9, 9)))
        salary = int(base * (0.75 + rating / 180))
        out.append(
            StaffMember(
                role=role,
                name=rng.choice(STAFF_NAMES),
                rating=rating,
                salary=salary,
                contract_until="2028-06-30",
                source="modelo",
                confidence="baja",
            )
        )
    return out


def hire_staff(state: GameState, candidate: StaffMember) -> dict[str, Any]:
    team = state.user_team
    if any(m.role == candidate.role for m in team.staff):
        return {"ok": False, "message": f"Ya tienes {STAFF_LABELS.get(candidate.role, candidate.role)}."}
    bonus = int(candidate.salary * 0.20)
    if team.budget < bonus:
        return {"ok": False, "message": "No hay caja suficiente para la prima de contratación."}
    team.staff.append(candidate)
    team.budget -= bonus
    if candidate.role == "assistant":
        team.assistant_rating = candidate.rating
    state.market_history.append(
        {
            "type": "staff",
            "round": state.round,
            "player": candidate.name,
            "from": "mercado",
            "to": team.name,
            "fee": bonus,
            "salary": candidate.salary,
        }
    )
    return {
        "ok": True,
        "message": f"Contratado {candidate.name} como {STAFF_LABELS.get(candidate.role, candidate.role)}.",
    }


def fire_staff(state: GameState, role: str) -> dict[str, Any]:
    team = state.user_team
    member = next((m for m in team.staff if m.role == role), None)
    if not member:
        return {"ok": False, "message": "No hay nadie en ese rol."}
    compensation = int(member.salary * 0.50)
    if team.budget < compensation:
        return {"ok": False, "message": "No hay caja suficiente para la indemnización."}
    team.staff.remove(member)
    team.budget -= compensation
    if role == "assistant":
        team.assistant_rating = 55
    state.market_history.append(
        {
            "type": "despido",
            "round": state.round,
            "player": member.name,
            "from": team.name,
            "to": "libre",
            "fee": compensation,
            "salary": 0,
        }
    )
    return {"ok": True, "message": f"Despedido {member.name}. Indemnización: {compensation:,} €.".replace(",", ".")}
