"""Logística: distancias, viajes, costes y fatiga."""

from __future__ import annotations

import math

from .data_loader import norm
from .models import TeamState

EARTH_KM = 6371.0


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(a))


def city_for(team: TeamState, cities_by_name: dict[str, dict]) -> dict | None:
    return cities_by_name.get(norm(team.city))


def distance_between(team_a: TeamState, team_b: TeamState, cities_by_name: dict[str, dict]) -> float:
    a = city_for(team_a, cities_by_name)
    b = city_for(team_b, cities_by_name)
    if not a or not b:
        return 300.0
    return haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])


def _is_island(city: dict | None) -> bool:
    return bool(city and city.get("airport") == "LPA")


def travel_options(
    team: TeamState, rival: TeamState, cities_by_name: dict[str, dict], squad_size: int = 18
) -> list[dict]:
    """Devuelve 3 opciones de viaje para un partido fuera de casa."""
    if team.city == rival.city:
        return [
            {
                "id": "local",
                "label": "Desplazamiento local",
                "mode": "bus",
                "distance_km": 0,
                "hours": 0.5,
                "cost": 120,
                "fatigue": 0.005,
                "hotel_nights": 0,
                "notes": "Mismo municipio; bus y vuelta.",
            }
        ]
    d = distance_between(team, rival, cities_by_name)
    a = city_for(team, cities_by_name)
    b = city_for(rival, cities_by_name)
    island = _is_island(a) or _is_island(b)
    plane = island or d > 650
    train = (
        (not plane)
        and d > 300
        and a
        and b
        and a.get("train") not in (None, "", "No")
        and b.get("train") not in (None, "", "No")
    )
    people = squad_size + 4
    if plane:
        hours = 4.2 + d / 850
        base_flight = 130 * people
        hotel = 75 * people
        meals = 28 * people
        opts = [
            {
                "id": "economico",
                "label": "Vuelo el mismo día",
                "mode": "avión",
                "distance_km": round(d),
                "hours": round(hours, 1),
                "cost": int(base_flight + meals + 250),
                "fatigue": 0.20,
                "hotel_nights": 0,
                "notes": "Barato, pero llegada cansada y sin margen.",
            },
            {
                "id": "equilibrado",
                "label": "Vuelo + 1 noche",
                "mode": "avión",
                "distance_km": round(d),
                "hours": round(hours, 1),
                "cost": int(base_flight + hotel + meals * 2 + 250),
                "fatigue": 0.12,
                "hotel_nights": 1,
                "notes": "Opción recomendada: descanso razonable.",
            },
            {
                "id": "premium",
                "label": "Vuelo + 2 noches",
                "mode": "avión",
                "distance_km": round(d),
                "hours": round(hours, 1),
                "cost": int(base_flight * 1.08 + hotel * 2 + meals * 3 + 300),
                "fatigue": 0.06,
                "hotel_nights": 2,
                "notes": "Máximo descanso; coste alto.",
            },
        ]
    elif train:
        hours = 1.2 + d / 120
        base = 48 * people
        hotel = 70 * people
        meals = 26 * people
        opts = [
            {
                "id": "economico",
                "label": "Tren el mismo día",
                "mode": "tren",
                "distance_km": round(d),
                "hours": round(hours, 1),
                "cost": int(base + meals + 200),
                "fatigue": 0.12,
                "hotel_nights": 0,
                "notes": "Ahorra hotel; viaje largo el mismo día.",
            },
            {
                "id": "equilibrado",
                "label": "Tren + 1 noche",
                "mode": "tren",
                "distance_km": round(d),
                "hours": round(hours, 1),
                "cost": int(base + hotel + meals * 2 + 250),
                "fatigue": 0.06,
                "hotel_nights": 1,
                "notes": "Recomendada para distancias medias.",
            },
            {
                "id": "premium",
                "label": "Tren + 2 noches",
                "mode": "tren",
                "distance_km": round(d),
                "hours": round(hours, 1),
                "cost": int(base * 1.15 + hotel * 2 + meals * 3 + 300),
                "fatigue": 0.03,
                "hotel_nights": 2,
                "notes": "Máximo descanso.",
            },
        ]
    else:
        hours = 0.8 + d / 80
        base = 1.2 * d
        hotel = 70 * people
        meals = 24 * people
        if d < 100:
            opts = [
                {
                    "id": "economico",
                    "label": "Bus, ida y vuelta",
                    "mode": "bus",
                    "distance_km": round(d),
                    "hours": round(hours, 1),
                    "cost": int(base + 120),
                    "fatigue": 0.02,
                    "hotel_nights": 0,
                    "notes": "Desplazamiento corto.",
                },
                {
                    "id": "equilibrado",
                    "label": "Bus + comida",
                    "mode": "bus",
                    "distance_km": round(d),
                    "hours": round(hours, 1),
                    "cost": int(base + meals + 180),
                    "fatigue": 0.01,
                    "hotel_nights": 0,
                    "notes": "Algo más cómodo; no necesita hotel.",
                },
            ]
        else:
            opts = [
                {
                    "id": "economico",
                    "label": "Bus el mismo día",
                    "mode": "bus",
                    "distance_km": round(d),
                    "hours": round(hours, 1),
                    "cost": int(base + meals + 150),
                    "fatigue": 0.10,
                    "hotel_nights": 0,
                    "notes": "Barato; fatiga acumulada.",
                },
                {
                    "id": "equilibrado",
                    "label": "Bus + 1 noche",
                    "mode": "bus",
                    "distance_km": round(d),
                    "hours": round(hours, 1),
                    "cost": int(base + hotel + meals * 2 + 200),
                    "fatigue": 0.05,
                    "hotel_nights": 1,
                    "notes": "Opción recomendada.",
                },
                {
                    "id": "premium",
                    "label": "Bus + 2 noches",
                    "mode": "bus",
                    "distance_km": round(d),
                    "hours": round(hours, 1),
                    "cost": int(base * 1.1 + hotel * 2 + meals * 3 + 250),
                    "fatigue": 0.02,
                    "hotel_nights": 2,
                    "notes": "Máximo descanso.",
                },
            ]
    return opts


def apply_travel(team: TeamState, option: dict, players: list | None = None) -> dict:
    """Aplica coste y fatiga. Devuelve un resumen."""
    cost = int(option.get("cost", 0))
    team.budget -= cost
    fatigue_add = float(option.get("fatigue", 0.0)) * 100.0
    target = players if players is not None else team.players
    for p in target:
        p.fatigue = min(100.0, p.fatigue + fatigue_add)
        if fatigue_add >= 20:
            p.morale = max(1, p.morale - 1)
    return {"cost": cost, "fatigue_add": round(fatigue_add, 1), "option": option.get("label", "")}
