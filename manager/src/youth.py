"""Cantera: generación, desarrollo y promoción de juveniles.

Los nombres se generan con pools por comunidad autónoma. Las categorías
modeladas son Sub-16 (14-15 años), Sub-18 (16-17) y Sub-21 (18-20).
"""

from __future__ import annotations

import json
import random
import re
import unicodedata
import zlib
from pathlib import Path

from .models import PlayerState, TeamState
from .runtime import project_root

DATA = project_root() / "manager" / "data" / "youth_names.json"
POOLS = json.loads(DATA.read_text(encoding="utf-8"))
POOLS_BY_KEY = {
    re.sub(
        r"[^a-z0-9]+", " ", unicodedata.normalize("NFKD", key).encode("ascii", "ignore").decode().lower()
    ).strip(): value
    for key, value in POOLS.items()
}
DEFAULT_POOL = POOLS["_default"]

COMMUNITY_ALIASES = {
    "cataluna": "Cataluña",
    "catalunya": "Cataluña",
    "comunidad valenciana": "Comunidad Valenciana",
    "valencia": "Comunidad Valenciana",
    "comunidad de madrid": "Comunidad de Madrid",
    "madrid": "Comunidad de Madrid",
    "pais vasco": "País Vasco",
    "euskadi": "País Vasco",
    "islas baleares": "Islas Baleares",
    "baleares": "Islas Baleares",
    "principado de asturias": "Asturias",
    "asturias": "Asturias",
    "comunidad foral de navarra": "Comunidad Foral de Navarra",
    "navarra": "Comunidad Foral de Navarra",
    "region de murcia": "Región de Murcia",
    "murcia": "Región de Murcia",
    "castilla la mancha": "Castilla-La Mancha",
    "castilla y leon": "Castilla y León",
}

CATEGORY_AGES = {"Sub-16": (14, 15), "Sub-18": (16, 17), "Sub-21": (18, 20)}
YOUTH_CATEGORIES = ("Sub-16", "Sub-18", "Sub-21")
CATEGORY_LABELS = {"Sub-16": "Sub-16 · Cadete", "Sub-18": "Sub-18 · Juvenil", "Sub-21": "Sub-21 · Júnior"}

KEYS = [
    "control",
    "pase",
    "conduccion",
    "golpeo",
    "flick",
    "regate_3d",
    "definicion",
    "aerial",
    "pc_injection",
    "pc_trap",
    "pc_flick",
    "pc_deflection",
    "pc_first_runner",
    "pc_gk_save",
    "stroke_shot",
    "stroke_save",
    "free_hit",
    "posicionamiento",
    "pressing",
    "cobertura",
    "transicion",
    "desmarque",
    "velocidad",
    "resistencia",
    "fuerza",
    "agilidad",
    "coordinacion",
    "decisiones",
    "concentracion",
    "competitividad",
    "liderazgo",
    "reflejos",
    "blocaje",
    "distribucion",
    "uno_vs_uno",
    "alto",
    "rebote_gk",
]


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def category_for_age(age: int) -> str:
    if age <= 15:
        return "Sub-16"
    if age <= 17:
        return "Sub-18"
    if age <= 20:
        return "Sub-21"
    return "Senior"


def community_pool(community: str) -> dict[str, list[str]]:
    key = normalize(community)
    key = normalize(COMMUNITY_ALIASES.get(key, key))
    return POOLS_BY_KEY.get(key, DEFAULT_POOL)


def regional_name(team: TeamState, rng: random.Random) -> str:
    pool = community_pool(team.community)
    first = rng.choice(pool.get("names") or DEFAULT_POOL["names"])
    surnames = pool.get("surnames") or DEFAULT_POOL["surnames"]
    if len(surnames) >= 2:
        first_surname, second_surname = rng.sample(surnames, 2)
        return f"{first} {first_surname} {second_surname}"
    return f"{first} {surnames[0]}"


def generate_youth(team: TeamState, rng: random.Random, year: int, seq: int, age: int | None = None) -> PlayerState:
    pos = rng.choice(["Portero", "Central", "Lateral", "Medio", "Delantero"])
    group = "Portero" if pos == "Portero" else ("Defensa" if pos in ("Central", "Lateral") else pos)
    youth_age = age if age is not None else rng.randint(14, 17)
    youth_age = max(14, min(20, int(youth_age)))
    academy = team.academy_rating
    age_penalty = 4 if youth_age <= 15 else (2 if youth_age <= 17 else 0)
    base = 38 + int(academy / 8) - age_penalty
    attrs = {k: max(28, min(72, base + rng.randint(-8, 10))) for k in KEYS}
    overall = round(max(38.0, min(66.0, base + rng.uniform(-3, 6))), 1)
    potential_bonus = 3 if youth_age <= 15 else (1 if youth_age <= 17 else 0)
    potential = round(min(92.0, overall + rng.uniform(10, 24) + academy / 10 + potential_bonus), 1)
    return PlayerState(
        id=f"{team.id}-youth-{year}-{seq}",
        name=regional_name(team, rng),
        team_name=team.name,
        position_group=group,
        subposition=pos,
        age=youth_age,
        overall=overall,
        potential=potential,
        attributes=attrs,
        archetype="Canterano",
        perfil="Canterano",
        goals_isquad=0,
        value=int(overall * 4000), polivalencia=0.0, league=team.league,
        relationship=50,
        salary=int(rng.uniform(5000, 10000)),
        contract_until=f"{year + 3}-06-30",
    )


def initial_youth(teams: dict[str, TeamState], seed: int, count: int = 6) -> None:
    for team in teams.values():
        if team.league not in ("DHA", "DHB"):
            continue
        rng = random.Random(seed + zlib.crc32(team.id.encode("utf-8")) % 10000)
        # Dos jugadores por categoría para que la cantera nazca completa.
        ages = [14, 15, 16, 17, 18, 19][:count]
        team.youth = [generate_youth(team, rng, 2026, i + 1, age=age) for i, age in enumerate(ages)]


def develop_youth(team: TeamState, rng: random.Random, new_year: int) -> None:
    kept = []
    for p in team.youth:
        p.age += 1
        if p.age >= 21:
            continue
        category = p.youth_category
        growth_factor = 1.25 if category == "Sub-16" else (1.0 if category == "Sub-18" else 0.7)
        gains = 0
        for k in rng.sample(KEYS, 4):
            chance = (0.18 + (team.academy_rating - 50) / 250 + max(0, p.potential - p.overall) / 100) * growth_factor
            if rng.random() < min(0.65, chance):
                p.attributes[k] = min(99, p.attributes.get(k, 40) + 1)
                gains += 1
        p.overall = round(min(p.potential, p.overall + gains * 0.04 + rng.uniform(0.0, 0.25)), 1)
        kept.append(p)
    team.youth = kept


def intake(team: TeamState, rng: random.Random, new_year: int, count: int = 3) -> None:
    for i in range(count):
        if len(team.youth) >= 9:
            break
        team.youth.append(
            generate_youth(
                team,
                rng,
                new_year,
                len(team.youth) + i + 1,
                age=rng.choice([14, 15, 16]),
            )
        )


def promote_youth(team: TeamState, player_id: str) -> tuple[bool, str]:
    p = next((x for x in team.youth if x.id == player_id), None)
    if not p:
        return False, "Jugador no encontrado en la cantera."
    team.youth.remove(p)
    p.perfil = "Jugador"
    p.team_name = team.name
    p.league = team.league
    team.players.append(p)
    return True, f"{p.name} sube al primer equipo."


def release_youth(team: TeamState, player_id: str) -> tuple[bool, str]:
    p = next((x for x in team.youth if x.id == player_id), None)
    if not p:
        return False, "Jugador no encontrado."
    team.youth.remove(p)
    return True, f"{p.name} deja la cantera."
