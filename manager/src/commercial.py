"""Comercial, marca y patrocinios.

La marca del club se calcula con el nivel de la liga, la clasificación, la
afición, la academia, los jugadores y los resultados recientes. Los acuerdos
activos pagan cada jornada; las campañas y el precio de las entradas mueven
afición, marca y taquilla.
"""

from __future__ import annotations

import random
import zlib
from datetime import date, timedelta
from typing import Any

from .competitions import competition
from .models import GameState, TeamState


SPONSOR_CATEGORIES = {
    "equipacion": "Equipación",
    "estadio": "Estadio",
    "formacion": "Formación",
    "salud": "Salud",
    "energia": "Energía",
    "banca": "Banca",
    "tecnologia": "Tecnología",
    "alimentacion": "Alimentación",
    "movilidad": "Movilidad",
    "seguros": "Seguros",
}

SPONSOR_NAMES = {
    "local": ["Talleres Delta", "Cafés del Club", "Hockey Store", "Clínica Local", "Autoescuela Sur"],
    "regional": ["Banco del Mediterráneo", "Energía Levante", "Grupo Costa", "Seguros Delta", "Transportes Sur"],
    "nacional": ["Iberia Sports", "Banco Atlántico", "Movistar Hockey", "Endesa Club", "Mapfre Equipo"],
    "global": ["KPN", "ABN AMRO", "Santander Global", "Red Bull Hockey", "Emirates Field"],
}

TIERS = {
    "local": {"label": "Local", "min_brand": 0, "base": 26000, "years": (1, 2), "color": "neutral"},
    "regional": {"label": "Regional", "min_brand": 42, "base": 70000, "years": (2, 3), "color": "blue"},
    "nacional": {"label": "Nacional", "min_brand": 58, "base": 180000, "years": (2, 4), "color": "gold"},
    "global": {"label": "Global", "min_brand": 74, "base": 420000, "years": (3, 5), "color": "gold"},
}

CAMPAIGNS = {
    "social": {"label": "Campaña digital", "cost": 12000, "brand": 2, "fan": 2, "desc": "Redes, contenido y comunidad."},
    "local": {"label": "Campaña de barrio", "cost": 22000, "brand": 3, "fan": 4, "desc": "Presencia local, colegios y afición."},
    "internacional": {"label": "Campaña internacional", "cost": 60000, "brand": 5, "fan": 2, "desc": "Marca global y mercados exteriores."},
    "socios": {"label": "Captación de socios", "cost": 18000, "brand": 1, "fan": 5, "desc": "Abonos, familias y fidelización."},
}


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def _form(state: GameState, team: TeamState) -> list[str]:
    played = [f for f in state.fixtures if f.phase == "regular" and f.played and team.id in (f.home_id, f.away_id)]
    played.sort(key=lambda f: f.round)
    out = []
    for fixture in played[-5:]:
        gf = fixture.home_goals if fixture.home_id == team.id else fixture.away_goals
        ga = fixture.away_goals if fixture.home_id == team.id else fixture.home_goals
        out.append("V" if gf > ga else ("E" if gf == ga else "D"))
    return out


def brand_score(state: GameState, team: TeamState | None = None) -> int:
    team = team or state.user_team
    meta = competition(team.league)
    table = state.table() if team.league == state.competition else sorted(
        [t for t in state.teams.values() if t.league == team.league],
        key=lambda t: (-t.points, -(t.goals_for - t.goals_against), t.name),
    )
    position = next((i for i, t in enumerate(table, 1) if t.id == team.id), len(table) or 1)
    top = sorted(team.players, key=lambda p: p.overall, reverse=True)[:5]
    top_avg = sum(p.overall for p in top) / max(1, len(top))
    form = _form(state, team)
    form_bonus = form.count("V") * 2.0 - form.count("D") * 1.2
    position_bonus = max(0, (len(table) - position + 1) * 1.1)
    sponsor_bonus = len(team.sponsor_deals) * 1.4
    score = (
        meta.standard * 0.52
        + team.fan_confidence * 0.17
        + team.board_confidence * 0.07
        + team.academy_rating * 0.06
        + top_avg * 0.12
        + form_bonus
        + position_bonus
        + sponsor_bonus
        + team.brand_rating * 0.08
    )
    return int(round(_clamp(score)))


def brand_value(state: GameState, team: TeamState | None = None) -> int:
    score = brand_score(state, team)
    return int(score * score * 950)


def active_sponsor_round(team: TeamState) -> int:
    return sum(int(deal.get("per_round", 0)) for deal in team.sponsor_deals if deal.get("active", True))


def active_sponsor_annual(team: TeamState) -> int:
    return sum(int(deal.get("annual", 0)) for deal in team.sponsor_deals if deal.get("active", True))


def merchandising_round(team: TeamState) -> int:
    return int(max(0, team.merchandising) * max(1, team.fan_confidence) * 4.2)


def ticket_income_estimate(team: TeamState) -> int:
    return int(max(1, team.stadium_capacity) * max(8, team.ticket_price) * 0.62)


def _offer_name(rng: random.Random, tier: str, used: set[str]) -> str:
    pool = [name for name in SPONSOR_NAMES.get(tier, SPONSOR_NAMES["local"]) if name not in used]
    if not pool:
        pool = SPONSOR_NAMES["local"]
    name = rng.choice(pool)
    used.add(name)
    return name


def generate_sponsor_offers(state: GameState, force: bool = False) -> list[dict[str, Any]]:
    if not force and state.sponsor_offers and state.sponsor_offer_date == state.date:
        return state.sponsor_offers
    team = state.user_team
    rng = random.Random(state.seed * 1000 + date.fromisoformat(state.date).toordinal() + 311)
    score = brand_score(state, team)
    tiers = [tier for tier, data in TIERS.items() if score >= data["min_brand"]]
    offers = []
    used: set[str] = set()
    for index in range(rng.randint(2, 4)):
        tier = rng.choice(tiers[-2:] if len(tiers) > 1 else tiers)
        data = TIERS[tier]
        category = rng.choice(list(SPONSOR_CATEGORIES))
        years = rng.randint(*data["years"])
        multiplier = 0.75 + score / 140 + rng.uniform(-0.08, 0.22)
        annual = int(data["base"] * multiplier)
        signing = int(annual * rng.uniform(0.08, 0.18))
        offers.append(
            {
                "id": f"SP{state.round}-{date.fromisoformat(state.date).toordinal()}-{index}",
                "name": _offer_name(rng, tier, used),
                "category": SPONSOR_CATEGORIES[category],
                "category_id": category,
                "tier": tier,
                "tier_label": data["label"],
                "annual": annual,
                "per_round": int(annual / 22),
                "years": years,
                "signing_bonus": signing,
                "brand_boost": round(1.5 + score / 45 + rng.uniform(0, 1.5), 1),
                "requirement": rng.choice(
                    [
                        "Mantener la categoría",
                        "Terminar en la mitad alta",
                        "Alcanzar los play-offs",
                        "Cuidar la imagen del club",
                        "Participar en la Copa",
                    ]
                ),
                "expires": (date.fromisoformat(state.date) + timedelta(days=14)).isoformat(),
                "status": "pendiente",
            }
        )
    state.sponsor_offers = offers
    state.sponsor_offer_date = state.date
    return offers


def accept_sponsor_offer(state: GameState, offer_id: str) -> dict[str, Any]:
    offer = next((item for item in state.sponsor_offers if item.get("id") == offer_id), None)
    if not offer:
        return {"ok": False, "message": "La oferta ya no está disponible."}
    team = state.user_team
    start = state.date
    end_year = int(state.season[:4]) + int(offer.get("years", 1))
    deal = {
        **offer,
        "active": True,
        "signed": start,
        "end": f"{end_year}-06-30",
        "status": "activo",
    }
    team.sponsor_deals.append(deal)
    team.budget += int(offer.get("signing_bonus", 0))
    team.brand_rating = int(_clamp(team.brand_rating + float(offer.get("brand_boost", 0))))
    team.commercial_history.append(
        {
            "date": start,
            "type": "patrocinio",
            "name": offer["name"],
            "annual": int(offer["annual"]),
            "bonus": int(offer.get("signing_bonus", 0)),
            "message": f"Acuerdo con {offer['name']} hasta {end_year}.",
        }
    )
    state.sponsor_offers = [item for item in state.sponsor_offers if item.get("id") != offer_id]
    return {"ok": True, "message": f"Patrocinio firmado con {offer['name']}."}


def reject_sponsor_offer(state: GameState, offer_id: str) -> dict[str, Any]:
    before = len(state.sponsor_offers)
    state.sponsor_offers = [item for item in state.sponsor_offers if item.get("id") != offer_id]
    return {"ok": len(state.sponsor_offers) < before, "message": "Oferta de patrocinio rechazada."}


def set_ticket_price(state: GameState, price: int) -> dict[str, Any]:
    team = state.user_team
    price = int(max(8, min(40, price)))
    previous = team.ticket_price
    team.ticket_price = price
    if price > 28:
        team.fan_confidence = int(_clamp(team.fan_confidence - 2))
    elif price < 12:
        team.fan_confidence = int(_clamp(team.fan_confidence + 1))
    team.commercial_history.append(
        {
            "date": state.date,
            "type": "taquilla",
            "name": "Precio de entrada",
            "annual": 0,
            "bonus": 0,
            "message": f"Entrada de {previous} € a {price} €.",
        }
    )
    return {"ok": True, "message": f"Precio de entrada actualizado a {price} €."}


def run_campaign(state: GameState, campaign_id: str) -> dict[str, Any]:
    campaign = CAMPAIGNS.get(campaign_id)
    if not campaign:
        return {"ok": False, "message": "Campaña no válida."}
    team = state.user_team
    cost = int(campaign["cost"])
    if team.budget < cost:
        return {"ok": False, "message": "No hay caja suficiente para la campaña."}
    team.budget -= cost
    team.brand_rating = int(_clamp(team.brand_rating + campaign["brand"]))
    team.fan_confidence = int(_clamp(team.fan_confidence + campaign["fan"]))
    team.commercial_history.append(
        {
            "date": state.date,
            "type": "campana",
            "name": campaign["label"],
            "annual": 0,
            "bonus": -cost,
            "message": f"{campaign['desc']} Marca +{campaign['brand']} · afición +{campaign['fan']}.",
        }
    )
    return {"ok": True, "message": f"Campaña lanzada: {campaign['label']}."}


def commercial_summary(state: GameState) -> dict[str, Any]:
    team = state.user_team
    score = brand_score(state, team)
    active = [deal for deal in team.sponsor_deals if deal.get("active", True)]
    return {
        "brand_score": score,
        "brand_value": brand_value(state, team),
        "brand_rating": team.brand_rating,
        "fan_confidence": team.fan_confidence,
        "board_confidence": team.board_confidence,
        "ticket_price": team.ticket_price,
        "merchandising": team.merchandising,
        "sponsor_round": active_sponsor_round(team),
        "sponsor_annual": active_sponsor_annual(team),
        "merchandising_round": merchandising_round(team),
        "ticket_estimate": ticket_income_estimate(team),
        "active_deals": active,
        "offers": generate_sponsor_offers(state),
        "campaigns": [
            {"id": key, **value, "affordable": team.budget >= value["cost"]}
            for key, value in CAMPAIGNS.items()
        ],
        "history": team.commercial_history[-10:],
        "staff": [
            {
                "role": member.role,
                "name": member.name,
                "rating": member.rating,
                "salary": member.salary,
                "role_label": "Director comercial" if member.role == "commercial_director" else member.role,
            }
            for member in team.staff
            if member.role in ("commercial_director", "marketing_manager")
        ],
    }


def daily_commercial_tick(state: GameState, day: date, rng: random.Random | None = None) -> None:
    team = state.user_team
    rng = rng or random.Random(state.seed + day.toordinal() + 707)
    for deal in team.sponsor_deals:
        if deal.get("active", True) and str(deal.get("end", "")) and day >= date.fromisoformat(str(deal["end"])):
            deal["active"] = False
            team.commercial_history.append(
                {
                    "date": day.isoformat(),
                    "type": "patrocinio",
                    "name": deal.get("name", "Patrocinador"),
                    "annual": 0,
                    "bonus": 0,
                    "message": "El acuerdo de patrocinio ha expirado.",
                }
            )
    team.brand_rating = int(round(_clamp(team.brand_rating * 0.995 + brand_score(state, team) * 0.005)))
    if not state.sponsor_offers and rng.random() < 0.18:
        generate_sponsor_offers(state, force=True)
        state.daily_events = (
            state.daily_events
            + [
                {
                    "date": day.isoformat(),
                    "category": "Comercial",
                    "headline": "Nuevas propuestas de patrocinio",
                    "body": "La dirección comercial ha recibido ofertas para la marca del club.",
                    "important": True,
                    "team_id": team.id,
                    "player_id": "",
                    "league": state.competition,
                    "type": "commercial",
                }
            ]
        )[-240:]
