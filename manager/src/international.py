"""Carga de ligas internacionales y generación de plantillas base.

Las seis ligas usan clubes y plantillas reales. Los datos quedan separados en
`data/international.json` e `international_real.json`; si una ficha no tiene
plantilla real se completa con generación determinista para no romper partidas
antiguas.
"""

from __future__ import annotations

import json
import random
import re
import unicodedata
import zlib
from functools import lru_cache
from pathlib import Path

from .competitions import LEAGUE_RATING_TARGETS, competition
from .models import BoardMember, PlayerState, StaffMember, Tactics, TeamState

DATA = Path(__file__).resolve().parents[1] / "data" / "international.json"
REAL_DATA = DATA.with_name("international_real.json")

POSITIONS = (
    ["Portero"] * 2
    + ["Defensa"] * 5
    + ["Medio"] * 5
    + ["Delantero"] * 6
)

ATTRIBUTE_KEYS = [
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
    "reflejos",
    "blocaje",
    "rebote_gk",
    "uno_vs_uno",
    "distribucion",
    "concentracion",
    "decisiones",
    "competitividad",
    "liderazgo",
    "coordinacion",
]

NAMES = {
    "NL": {
        "first": ["Jip", "Thijs", "Bram", "Lars", "Daan", "Sem", "Ruben", "Teun", "Mees", "Jesse", "Koen", "Sander", "Floris", "Hidde", "Joep", "Noud", "Tijn", "Rik", "Stijn", "Milan"],
        "last": ["Janssen", "de Vries", "van Dijk", "Bakker", "Visser", "Smit", "Meijer", "Mulder", "Bos", "Vos", "Peters", "Hendriks", "van Leeuwen", "Dekker", "Brouwer", "de Wit", "Dijkstra", "Smits", "de Graaf", "van der Meer"],
    },
    "BE": {
        "first": ["Arthur", "Louis", "Jules", "Victor", "Lucas", "Noah", "Liam", "Milan", "Wout", "Seppe", "Emile", "Basile", "Simon", "Thomas", "Maxime", "Gauthier", "Nicolas", "Ruben", "Jef", "Lars"],
        "last": ["Peeters", "Janssens", "Maes", "Jacobs", "Mertens", "Willems", "Claes", "Goossens", "Wouters", "De Smet", "Vermeulen", "Dupont", "Leclercq", "Dubois", "Lambert", "Martin", "Simon", "Laurent", "Vandenberghe", "Van Damme"],
    },
    "DE": {
        "first": ["Jonas", "Leon", "Finn", "Luca", "Paul", "Max", "Felix", "Tim", "Niklas", "Jan", "Moritz", "Lukas", "Elias", "Noah", "Ben", "Tom", "Jannik", "Florian", "Nico", "David"],
        "last": ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann", "Koch", "Richter", "Klein", "Wolf", "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger", "Hartmann"],
    },
    "EN": {
        "first": ["Harry", "Jack", "Oliver", "George", "Charlie", "Thomas", "James", "William", "Henry", "Alfie", "Freddie", "Sam", "Ben", "Tom", "Luke", "Joe", "Alex", "Dan", "Matt", "Chris"],
        "last": ["Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies", "Robinson", "Wright", "Thompson", "Evans", "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Clarke", "Jackson"],
    },
    "AR": {
        "first": ["Santiago", "Mateo", "Lucas", "Tomás", "Agustín", "Nicolás", "Franco", "Joaquín", "Bautista", "Ignacio", "Facundo", "Martín", "Juan", "Pedro", "Gonzalo", "Ramiro", "Emiliano", "Bruno", "Lautaro", "Federico"],
        "last": ["González", "Rodríguez", "Fernández", "López", "Martínez", "Pérez", "García", "Sánchez", "Romero", "Díaz", "Torres", "Ruiz", "Álvarez", "Acosta", "Benítez", "Sosa", "Molina", "Silva", "Castro", "Ríos"],
    },
    "IN": {
        "first": ["Arjun", "Rohan", "Vikram", "Aditya", "Karan", "Rahul", "Aman", "Sukhjeet", "Manpreet", "Harman", "Jaskaran", "Rupinder", "Amit", "Naveen", "Pawan", "Sandeep", "Yash", "Dev", "Ishaan", "Vivek"],
        "last": ["Singh", "Sharma", "Kumar", "Patel", "Reddy", "Nair", "Das", "Kaur", "Yadav", "Mishra", "Chauhan", "Rathore", "Jha", "Menon", "Pillai", "Gill", "Sandhu", "Bhatia", "Verma", "Thakur"],
    },
}


@lru_cache(maxsize=1)
def international_data() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def real_data() -> dict:
    if not REAL_DATA.exists():
        return {}
    return json.loads(REAL_DATA.read_text(encoding="utf-8"))


def club_catalog() -> dict[str, dict]:
    return {club["id"]: club for club in international_data()["clubs"]}


@lru_cache(maxsize=1)
def international_cities() -> dict[str, dict]:
    return {_norm(city["name"]): city for city in international_data()["cities"]}


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip().upper()


def _league_factor(code: str) -> float:
    return {"ARG": 0.82, "IND": 0.85, "BEL": 1.10, "GER": 1.10, "ENG": 1.02, "NED": 1.15}.get(code, 1.0)


# Correcciones puntuales verificadas con una fuente externa a la ficha del club.
# El id es el identificador estable del jugador en international_real.json.
POSITION_OVERRIDES: dict[str, tuple[str, str]] = {
    "ned-kampong-luis-calzado": ("Portero", "Portero"),
}


def _position_from_real(value: str) -> tuple[str, str]:
    """Traduce posiciones de las fuentes (ES/EN/NL) al modelo del juego."""
    text = (value or "").lower()
    if any(term in text for term in ("goal", "keeper", "portero", "doelman", "arquero")):
        return "Portero", "Portero"
    if any(term in text for term in ("defen", "verdedig", "defensa", "back")):
        return "Defensa", "Central"
    if any(term in text for term in ("mid", "midden", "medio", "centre")):
        return "Medio", "Medio"
    if any(term in text for term in ("attack", "aanval", "forward", "delan", "spits", "delantero")):
        return "Delantero", "Delantero"
    return "Medio", "Medio"


def _real_player(club: dict, entry: dict, index: int, rng: random.Random) -> PlayerState:
    base = _make_player(club, index, rng)
    group, sub = POSITION_OVERRIDES.get(str(entry.get("id", "")), _position_from_real(entry.get("position", "")))
    dob = entry.get("dob", "")
    age = 25
    if dob:
        try:
            day, month, year = [int(x) for x in dob.split("/")]
            age = 2026 - year - ((10, 22) < (month, day))
        except Exception:
            pass
    base.id = entry["id"]
    base.name = entry["name"]
    base.position_group = group
    base.subposition = sub
    base.age = max(16, min(42, age))
    base.overall = float(entry.get("overall", base.overall))
    base.potential = max(base.overall, min(94.0, base.overall + (6 if base.age <= 23 else 2)))
    base.photo = entry.get("photo", "")
    base.photo_remote = entry.get("photo_remote", "")
    base.value = int(max(30000, (base.overall - 40) ** 2 * 190 * _league_factor(club["league"])))
    base.salary = int(max(12000, (base.overall - 45) * 1400 * _league_factor(club["league"])))
    base.contract_until = "2029-06-30"
    base.league = club["league"]
    base.team_name = club["name"]
    return base


def _make_player(club: dict, index: int, rng: random.Random) -> PlayerState:
    league = competition(club["league"])
    country_code = league.country_code
    pool = NAMES.get(country_code, NAMES["EN"])
    position = POSITIONS[index % len(POSITIONS)]
    if position == "Portero":
        group = "Portero"
        subposition = "Portero"
        archetype = "Portero"
        pos_bonus = 0.0
    elif position == "Defensa":
        group = "Defensa"
        subposition = "Central" if index % 3 else "Lateral"
        archetype = "Central constructor" if subposition == "Central" else "Lateral físico"
        pos_bonus = -1.5
    elif position == "Medio":
        group = "Medio"
        subposition = "Medio"
        archetype = "Medio creativo" if index % 2 else "Medio de contención"
        pos_bonus = 0.0
    else:
        group = "Delantero"
        subposition = "Delantero"
        archetype = "Delantero finalizador" if index % 2 else "Delantero móvil"
        pos_bonus = 1.0

    club_bonus = rng.uniform(-3.0, 3.5)
    base = league.standard + club_bonus + pos_bonus + rng.uniform(-2.5, 2.5)
    if position == "Portero":
        base -= 1.0
    overall = round(max(48.0, min(90.0, base)), 1)
    age = rng.randint(19, 34)
    potential = round(min(94.0, overall + rng.uniform(1.0, 10.0) + (3.0 if age <= 23 else 0.0)), 1)
    attributes = {}
    for key in ATTRIBUTE_KEYS:
        bonus = 0
        if position == "Portero" and key in ("reflejos", "blocaje", "pc_gk_save", "stroke_save", "rebote_gk", "agilidad"):
            bonus = 7
        elif position == "Defensa" and key in ("cobertura", "posicionamiento", "pressing", "fuerza", "pc_first_runner"):
            bonus = 4
        elif position == "Medio" and key in ("pase", "control", "vision", "distribucion", "resistencia"):
            bonus = 4
        elif position == "Delantero" and key in ("definicion", "velocidad", "regate_3d", "pc_flick", "desmarque"):
            bonus = 5
        attributes[key] = int(max(34, min(94, overall + bonus + rng.randint(-7, 7))))
    overalls = {
        "Portero": overall,
        "Central": round(overall + (3 if position == "Defensa" else -2), 1),
        "Lateral": round(overall + (2 if position == "Defensa" else -2), 1),
        "Medio": round(overall + (3 if position == "Medio" else -2), 1),
        "Delantero": round(overall + (3 if position == "Delantero" else -2), 1),
    }
    name = f"{rng.choice(pool['first'])} {rng.choice(pool['last'])}"
    player_id = f"{club['id']}-p{index + 1:02d}"
    value = int(max(25000, (overall - 40) ** 2 * 190 * _league_factor(club["league"])))
    salary = int(max(9000, (overall - 45) * 1200 * _league_factor(club["league"])))
    contract_years = 1 + zlib.crc32(player_id.encode("utf-8")) % 4
    return PlayerState(
        id=player_id,
        name=name,
        team_name=club["name"],
        position_group=group,
        subposition=subposition,
        age=age,
        overall=overall,
        potential=potential,
        attributes=attributes,
        archetype=archetype,
        perfil="Jugador",
        goals_isquad=0,
        value=value,
        polivalencia=round(rng.uniform(0, 0.35), 2),
        overalls=overalls,
        relationship=45 + zlib.crc32(player_id.encode("utf-8")) % 26,
        form=6.2 + rng.random() * 0.9,
        salary=salary,
        contract_until=f"{2027 + contract_years - 1}-06-30",
        league=club["league"],
        photo="",
        photo_remote="",
    )


def _make_staff(club: dict, rng: random.Random) -> list[StaffMember]:
    league = competition(club["league"])
    pool = NAMES.get(league.country_code, NAMES["EN"])
    roles = [("head_coach", 4), ("assistant", 0), ("fitness_coach", -4), ("scout", -3), ("physio", -5)]
    staff = []
    for role, delta in roles:
        name = f"{rng.choice(pool['first'])} {rng.choice(pool['last'])}"
        rating = max(48, min(88, int(league.standard + delta + rng.randint(-5, 5))))
        staff.append(
            StaffMember(
                role=role,
                name=name,
                rating=rating,
                salary=int(max(12000, (rating - 40) * 2400 * _league_factor(club["league"]))),
                contract_until="2028-06-30",
                source="modelo internacional",
                confidence="baja",
            )
        )
    return staff


def _calibrate_league_means(teams: dict[str, TeamState]) -> None:
    """Ajusta cada liga internacional a su media objetivo.

    Las plantillas reales pueden tener medias distintas según la fuente. Este
    ajuste conserva la dispersión interna de cada liga y fija la jerarquía
    NED > BEL > GER > ENG > ARG > IND.
    """
    for code, target in LEAGUE_RATING_TARGETS.items():
        players = [player for team in teams.values() if team.league == code for player in team.players]
        if not players:
            continue
        current = sum(player.overall for player in players) / len(players)
        shift = target - current
        for player in players:
            player.overall = round(max(40.0, min(95.0, player.overall + shift)), 2)
            player.potential = round(max(player.overall, min(99.0, player.potential + shift)), 2)
            if player.overalls:
                player.overalls = {
                    key: round(max(40.0, min(95.0, value + shift)), 2)
                    for key, value in player.overalls.items()
                }


def load_international_teams() -> tuple[dict[str, TeamState], dict[str, dict], dict[str, dict]]:
    data = international_data()
    clubs = data["clubs"]
    cities = {_norm(city["name"]): city for city in data["cities"]}
    teams: dict[str, TeamState] = {}
    for club in clubs:
        league = competition(club["league"])
        seed = zlib.crc32(club["id"].encode("utf-8")) + int(league.standard * 1000)
        rng = random.Random(seed)
        real_club = real_data().get(club["league"], {}).get("clubs", {}).get(club["id"], {})
        real_players = real_club.get("players", [])
        if real_players:
            players = [_real_player(club, entry, i, rng) for i, entry in enumerate(real_players)]
            used = {p.id for p in players}
            i = len(players)
            while len(players) < 18:
                extra = _make_player(club, i, rng)
                if extra.id not in used:
                    players.append(extra)
                    used.add(extra.id)
                i += 1
        else:
            players = [_make_player(club, i, rng) for i in range(18)]
        finances = club.get("finances", {})
        staff = _make_staff(club, rng)
        head = next((m for m in staff if m.role == "head_coach"), None)
        teams[club["id"]] = TeamState(
            id=club["id"],
            name=club["name"],
            league=club["league"],
            city=club["city"],
            community=club.get("country", league.country),
            country=club.get("country", league.country),
            players=players,
            tactics=Tactics(),
            stadium_name=club.get("stadium", {}).get("name", ""),
            stadium_capacity=int(club.get("stadium", {}).get("capacity", 1000) or 1000),
            board_expectation=club.get("expectation", "Consolidarse"),
            board_patience=3,
            board_pressure="media",
            academy_rating=max(40, min(90, 45 + int(club.get("academy", 3) or 3) * 8)),
            preferred_mode="avión" if club["league"] in ("ARG", "IND") else "bus",
            assistant_rating=head.rating if head else 60,
            staff=staff,
            board=[],
            budget=int(finances.get("wage_budget", 400000) or 400000) * 2,
            wage_budget=int(finances.get("wage_budget", 400000) or 400000),
            transfer_budget=int(finances.get("transfer_budget", 150000) or 150000),
            club_tier=int(finances.get("tier", 3) or 3),
            morale=12,
            cohesion=12,
            board_confidence=60,
            fan_confidence=60,
            manager_rating=60,
        )
    _calibrate_league_means(teams)
    return teams, {club["id"]: club for club in clubs}, cities


def replacement_player(team: TeamState, year: int, seq: int) -> PlayerState:
    """Genera un recambio internacional cuando expira un contrato."""
    club = {
        "id": team.id,
        "name": team.name,
        "league": team.league,
        "country": team.country,
    }
    rng = random.Random(zlib.crc32(f"{team.id}-{year}-{seq}".encode("utf-8")))
    player = _make_player(club, seq, rng)
    player.team_name = team.name
    player.league = team.league
    player.contract_until = f"{year + 2}-06-30"
    return player


def load_all_teams() -> tuple[dict[str, TeamState], dict[str, dict], dict[str, dict]]:
    """Equipos españoles + internacionales, con ciudades combinadas."""
    from .data_loader import load_teams

    teams, clubs, cities = load_teams()
    intl_teams, intl_clubs, intl_cities = load_international_teams()
    teams.update(intl_teams)
    clubs.update(intl_clubs)
    cities.update(intl_cities)
    return teams, clubs, cities
