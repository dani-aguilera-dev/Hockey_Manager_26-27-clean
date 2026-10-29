"""Marcas reales de material de hockey y acuerdos de equipación.

A diferencia de los patrocinadores de club, estas marcas visten y equipan al
equipo: palas, protección, calzado, ropa o material de portero. El acuerdo
aporta caja, marca y un pequeño bonus de equipación que se aplica en partido.
"""

from __future__ import annotations

import json
import random
import zlib
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .competitions import competition
from .models import GameState, TeamState

DATA = Path(__file__).resolve().parents[1] / "data" / "brands.json"
CATEGORY_LABELS = {
    "sticks": "Palas",
    "protection": "Protección",
    "apparel": "Ropa",
    "shoes": "Calzado",
    "goalkeeping": "Portero",
    "balls": "Bolas",
}
TIER_LABELS = {
    "regional": "Regional",
    "nacional": "Nacional",
    "global": "Global",
}


def load_brands() -> list[dict[str, Any]]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _eligible(state: GameState, brand: dict[str, Any]) -> bool:
    team = state.user_team
    meta = competition(team.league)
    tier = brand.get("tier", "regional")
    if tier == "global":
        return team.brand_rating >= 68 or meta.standard >= 72
    if tier == "nacional":
        return team.brand_rating >= 52 or meta.standard >= 58
    return True


def generate_brand_offers(state: GameState, force: bool = False) -> list[dict[str, Any]]:
    if not force and state.brand_offers and state.brand_offer_date == state.date:
        return state.brand_offers
    team = state.user_team
    rng = random.Random(state.seed * 7001 + date.fromisoformat(state.date).toordinal() + zlib.crc32(team.id.encode("utf-8")))
    pool = [brand for brand in load_brands() if _eligible(state, brand)]
    rng.shuffle(pool)
    offers: list[dict[str, Any]] = []
    for index, brand in enumerate(pool[:3]):
        tier = brand.get("tier", "regional")
        years = rng.randint(1, 3) if tier == "regional" else rng.randint(2, 4)
        annual = int(int(brand["base"]) * (0.82 + team.brand_rating / 110 + rng.uniform(-0.05, 0.12)))
        signing = int(annual * rng.uniform(0.06, 0.14))
        categories = [CATEGORY_LABELS.get(item, item) for item in brand.get("categories", [])]
        offers.append(
            {
                "id": f"BR-{state.season}-{state.round}-{brand['id']}",
                "brand_id": brand["id"],
                "brand": brand["name"],
                "country": brand.get("country", ""),
                "tier": tier,
                "tier_label": TIER_LABELS.get(tier, tier),
                "categories": categories,
                "annual": annual,
                "per_round": int(annual / max(1, state.total_rounds)),
                "signing_bonus": signing,
                "years": years,
                "bonus": float(brand.get("bonus", 0.5)),
                "description": brand.get("description", ""),
                "requirement": rng.choice(
                    [
                        "Mantener la categoría",
                        "Terminar en la mitad alta",
                        "Alcanzar los play-offs",
                        "Proyecto de cantera",
                        "Cuidar la imagen del club",
                    ]
                ),
                "expires": (date.fromisoformat(state.date) + timedelta(days=18)).isoformat(),
                "status": "pendiente",
            }
        )
    state.brand_offers = offers
    state.brand_offer_date = state.date
    return offers


def _recompute_bonus(team: TeamState) -> None:
    team.equipment_bonus = round(
        min(2.5, sum(float(deal.get("bonus", 0) or 0) for deal in team.equipment_deals if deal.get("active", True))),
        2,
    )


def accept_brand_offer(state: GameState, offer_id: str) -> dict[str, Any]:
    offer = next((item for item in state.brand_offers if item.get("id") == offer_id), None)
    if not offer:
        return {"ok": False, "message": "La oferta de marca ya no está disponible."}
    team = state.user_team
    deal = {
        **offer,
        "active": True,
        "signed": state.date,
        "end": f"{int(state.season[:4]) + int(offer.get('years', 1))}-06-30",
        "status": "activo",
    }
    team.equipment_deals.append(deal)
    team.budget += int(offer.get("signing_bonus", 0))
    team.brand_rating = int(max(0, min(100, team.brand_rating + 1 + int(offer.get("bonus", 0) * 2))))
    _recompute_bonus(team)
    team.commercial_history.append(
        {
            "date": state.date,
            "type": "marca",
            "name": offer["brand"],
            "annual": int(offer["annual"]),
            "bonus": int(offer.get("signing_bonus", 0)),
            "message": f"Acuerdo de equipación con {offer['brand']} hasta {deal['end']}.",
        }
    )
    state.brand_offers = [item for item in state.brand_offers if item.get("id") != offer_id]
    return {"ok": True, "message": f"Acuerdo de equipación firmado con {offer['brand']}.", "deal": deal}


def reject_brand_offer(state: GameState, offer_id: str) -> dict[str, Any]:
    before = len(state.brand_offers)
    state.brand_offers = [item for item in state.brand_offers if item.get("id") != offer_id]
    return {"ok": len(state.brand_offers) < before, "message": "Oferta de marca rechazada."}


def generate_player_brand_offers(state: GameState, force: bool = False) -> list[dict[str, Any]]:
    """Ofertas de imagen individual para jugadores de la plantilla."""
    if not force and state.player_brand_offers and state.player_brand_offer_date == state.date:
        return state.player_brand_offers
    team = state.user_team
    rng = random.Random(state.seed * 7301 + date.fromisoformat(state.date).toordinal() + 991)
    players = [
        player
        for player in sorted(team.players, key=lambda item: item.overall, reverse=True)
        if not player.brand_deal
    ][:4]
    pool = [brand for brand in load_brands() if _eligible(state, brand)]
    rng.shuffle(pool)
    offers: list[dict[str, Any]] = []
    for index, (player, brand) in enumerate(zip(players, pool[:2])):
        annual = int(max(12000, (player.overall - 42) ** 2 * 170 * (1.0 + team.brand_rating / 180)))
        offers.append(
            {
                "id": f"PB-{state.season}-{state.round}-{player.id}-{brand['id']}",
                "brand_id": brand["id"],
                "brand": brand["name"],
                "country": brand.get("country", ""),
                "player_id": player.id,
                "player_name": player.name,
                "tier": brand.get("tier", "regional"),
                "tier_label": TIER_LABELS.get(brand.get("tier", "regional"), brand.get("tier", "regional")),
                "categories": [CATEGORY_LABELS.get(item, item) for item in brand.get("categories", [])],
                "annual": annual,
                "signing_bonus": int(annual * rng.uniform(0.08, 0.18)),
                "years": rng.randint(1, 3),
                "bonus": float(brand.get("bonus", 0.5)),
                "description": brand.get("description", ""),
                "requirement": rng.choice(["Imagen del club", "Rendimiento deportivo", "Proyección internacional", "Compromiso con la cantera"]),
                "expires": (date.fromisoformat(state.date) + timedelta(days=21)).isoformat(),
                "status": "pendiente",
            }
        )
    state.player_brand_offers = offers
    state.player_brand_offer_date = state.date
    return offers


def accept_player_brand_offer(state: GameState, offer_id: str) -> dict[str, Any]:
    offer = next((item for item in state.player_brand_offers if item.get("id") == offer_id), None)
    if not offer:
        return {"ok": False, "message": "La oferta individual ya no está disponible."}
    player = next((item for item in state.user_team.players if item.id == offer.get("player_id")), None)
    if not player:
        return {"ok": False, "message": "El jugador ya no está en la plantilla."}
    team = state.user_team
    deal = {
        **offer,
        "active": True,
        "signed": state.date,
        "end": f"{int(state.season[:4]) + int(offer.get('years', 1))}-06-30",
    }
    player.brand_deal = deal
    player.relationship = min(100, player.relationship + 4)
    player.value = int(player.value * 1.05)
    team.budget += int(offer.get("signing_bonus", 0))
    team.brand_rating = min(100, team.brand_rating + 1)
    team.commercial_history.append(
        {
            "date": state.date,
            "type": "marca_jugador",
            "name": f"{offer['brand']} · {player.name}",
            "annual": int(offer["annual"]),
            "bonus": int(offer.get("signing_bonus", 0)),
            "message": f"Contrato de imagen de {player.name} con {offer['brand']} hasta {deal['end']}.",
        }
    )
    state.player_brand_offers = [item for item in state.player_brand_offers if item.get("id") != offer_id]
    return {"ok": True, "message": f"{player.name} firma con {offer['brand']}.", "deal": deal}


def reject_player_brand_offer(state: GameState, offer_id: str) -> dict[str, Any]:
    before = len(state.player_brand_offers)
    state.player_brand_offers = [item for item in state.player_brand_offers if item.get("id") != offer_id]
    return {"ok": len(state.player_brand_offers) < before, "message": "Oferta individual rechazada."}


def brand_summary(state: GameState) -> dict[str, Any]:
    team = state.user_team
    _recompute_bonus(team)
    active = [deal for deal in team.equipment_deals if deal.get("active", True)]
    return {
        "offers": generate_brand_offers(state),
        "player_offers": generate_player_brand_offers(state),
        "active_deals": active,
        "player_deals": [
            {"player_id": player.id, "player_name": player.name, **player.brand_deal}
            for player in team.players
            if player.brand_deal
        ],
        "equipment_bonus": team.equipment_bonus,
        "brand_rating": team.brand_rating,
        "history": [item for item in team.commercial_history if item.get("type") in ("marca", "marca_jugador")][-10:],
        "brands": load_brands(),
    }
