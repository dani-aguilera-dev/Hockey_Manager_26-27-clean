"""Carga de clubes, ciudades y jugadores para el Hockey Manager."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
import zlib
from pathlib import Path

from .models import BoardMember, PlayerState, StaffMember, Tactics, TeamState
from .runtime import project_root

BASE = project_root()
DATA = BASE / "manager" / "data"
TOOLS = BASE / "tools"

# iSquad mezcla plantilla y cuerpo técnico en el mismo CSV. Solo estos perfiles
# son jugadores; el resto se carga en `staff_isquad.json`. Los perfiles vacíos
# son jugadores de equipos B que no tienen ficha individual en la fuente.
STAFF_PROFILES = {
    "delegado equipo",
    "entrenador",
    "staff adicional",
    "fisioterapeuta",
    "preparador fisico",
    "médico",
    "medico",
    "psicólogo",
    "psicologo",
}


def norm(s: str) -> str:
    s = str(s or "").upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return " ".join(s.split())


def slug(s: str) -> str:
    s = norm(s).lower().replace(" ", "-")
    return re.sub(r"-+", "-", s).strip("-")


def load_json(name: str):
    return json.load(open(DATA / name, encoding="utf-8"))


def load_clubs() -> tuple[dict[str, dict], dict[str, dict]]:
    clubs = load_json("clubs.json")
    cities = load_json("cities.json")
    clubs_by_id = {c["id"]: c for c in clubs}
    cities_by_name = {norm(c["name"]): c for c in cities}
    return clubs_by_id, cities_by_name


def _club_for_team(team_name: str, clubs_by_id: dict[str, dict]) -> dict | None:
    target = norm(team_name)
    for c in clubs_by_id.values():
        if norm(c["name"]) == target or norm(c["full_name"]) == target:
            return c
    # alias manuales
    aliases = {
        "CD TERRASSA HOCKEY": "cd-terrassa",
        "REAL CLUB DE CAMPO VILLA DE MADRID": "rc-de-campo",
        "SANSE COMPLUTENSE": "sanse-complutense",
        "SARDINERO HOCKEY CLUB": "sardinero",
        "RS TENIS": "rs-tenis",
        "UD TABURIENTE": "ud-taburiente",
        "JUNIOR FC": "junior-fc",
        "CLUB EGARA": "club-egara",
        "RC POLO": "rc-polo",
        "ATLÈTIC TERRASSA HC": "atletic-terrassa",
        "CH CARPESA": "ch-carpesa",
        "FC BARCELONA": "fc-barcelona",
        "AD RIMAS": "ad-rimas",
        "CASTELLDEFELS HC": "castelldefels",
        "CD GINER DE LOS RÍOS": "cd-giner",
        "CLUB HOCKEY MADRID - LAS ROZAS": "ch-madrid-las-rozas",
        "EGARA 1935": "egara-1935",
        "HC SANT CUGAT": "hc-sant-cugat",
        "ILURO HC": "iluro",
        "LÍNIA 22 STERN MOTOR": "linia-22",
        "PEDRALBES HC": "pedralbes",
        "RC JOLASETA": "rc-jolaseta",
        "POZUELO": "pozuuelo",
        "REAL SOCIEDAD 1927": "real-sociedad-1927",
        "SPV": "spv",
        "UNIVERSITAT D'ALACANT - SAN VICENTE": "universitat-alacant",
        "VALLES ESPORTIU": "valles-esportiu",
        "ATICOS INMOBILIARIA CH SAN FERNANDO": "aticos-san-fernando",
        "CLUB DE HOCKEY SAN FERNANDO": "san-fernando-andaluza",
    }
    cid = aliases.get(target)
    return clubs_by_id.get(cid) if cid else None


def load_teams() -> tuple[dict[str, TeamState], dict[str, dict], dict[str, dict]]:
    clubs_by_id, cities_by_name = load_clubs()
    staff_path = DATA / "staff_dha.json"
    staff_by_club = json.load(open(staff_path, encoding="utf-8")) if staff_path.exists() else {}
    isquad_path = DATA / "staff_isquad.json"
    isquad_staff = json.load(open(isquad_path, encoding="utf-8")) if isquad_path.exists() else {}
    rows = list(csv.DictReader(open(TOOLS / "player_attributes_v2.csv", encoding="utf-8-sig")))
    by_team: dict[str, list[dict]] = {}
    for r in rows:
        by_team.setdefault(str(r.get("equipo", "")).strip(), []).append(r)
    teams: dict[str, TeamState] = {}
    for team_name, team_rows in by_team.items():
        club = _club_for_team(team_name, clubs_by_id)
        if not club:
            continue
        players: list[PlayerState] = []
        seen: dict[str, int] = {}
        for i, r in enumerate(team_rows):
            profile = str(r.get("perfil", "")).strip().lower()
            if profile in STAFF_PROFILES:
                continue
            name = str(r.get("jugador", "")).strip()
            key = slug(name)
            seen[key] = seen.get(key, 0) + 1
            pid = f"{club['id']}-{key}-{seen[key]}"
            attrs = {}
            for k, v in r.items():
                if k.startswith("attr_"):
                    try:
                        attrs[k[5:]] = int(float(v or 50))
                    except Exception:
                        attrs[k[5:]] = 50
            try:
                overall = float(r.get("overall") or 0)
            except Exception:
                overall = 0.0
            try:
                potential = float(r.get("potential") or overall)
            except Exception:
                potential = overall
            try:
                value = int(float(r.get("value") or 0))
            except Exception:
                value = 0
            try:
                goals = int(float(r.get("goles") or 0))
            except Exception:
                goals = 0
            try:
                age = int(float(r.get("edad") or 0))
            except Exception:
                age = 0
            overalls = {}
            for pos, col in [
                ("Portero", "overall_portero"),
                ("Central", "overall_central"),
                ("Lateral", "overall_lateral"),
                ("Medio", "overall_medio"),
                ("Delantero", "overall_delantero"),
            ]:
                try:
                    overalls[pos] = float(r.get(col) or 0)
                except Exception:
                    overalls[pos] = 0.0
            try:
                poly = float(r.get("polivalencia") or 0)
            except Exception:
                poly = 0.0
            contract_years = 1 + zlib.crc32(pid.encode("utf-8")) % 4
            if age >= 32:
                contract_years = 1
            contract_until = f"{2027 + contract_years - 1}-06-30"
            photo_rel = str(r.get("archivo_original") or "").strip()
            photo = photo_rel if photo_rel and (BASE / "jugadores" / photo_rel).exists() else ""
            photo_remote = str(r.get("imagen_url") or "").strip()
            players.append(
                PlayerState(
                    id=pid,
                    name=name,
                    team_name=club["name"],
                    position_group=str(r.get("position_group") or r.get("pos") or "Medio"),
                    subposition=str(r.get("subposicion") or r.get("pos") or "Medio"),
                    age=age,
                    overall=overall,
                    potential=potential,
                    attributes=attrs,
                    archetype=str(r.get("archetype") or "Jugador"),
                    perfil=str(r.get("perfil") or "Jugador"),
                    goals_isquad=goals,
                    value=value,
                    polivalencia=poly,
                    overalls=overalls,
                    contract_until=contract_until,
                    league=club["league"],
                    photo=photo,
                    photo_remote=photo_remote,
                )
            )
        fin = club.get("finances", {})
        stadium = club.get("stadium", {})
        fac = club.get("facilities", {})
        assistant_rating = 50 + int(fac.get("academy", 0) or 0) * 4
        assistant_rating += 5 if fac.get("video") else 0
        assistant_rating += 3 if fac.get("medical") else 0
        assistant_rating = max(45, min(85, assistant_rating))
        curated = staff_by_club.get(club["id"], {})
        scraped_rows = isquad_staff.get(club["id"], {}).get("staff", [])
        staff_rows = scraped_rows or curated.get("staff", [])
        staff = [
            StaffMember(**{k: v for k, v in row.items() if k in StaffMember.__dataclass_fields__}) for row in staff_rows
        ]
        board = [
            BoardMember(**{k: v for k, v in row.items() if k in BoardMember.__dataclass_fields__})
            for row in curated.get("board", [])
        ]
        if staff:
            assistant = next((m for m in staff if m.role == "assistant"), None)
            if assistant:
                assistant_rating = assistant.rating
        wage_budget = int(fin.get("wage_budget", 0) or 0)
        # Reparto salarial proporcional al nivel de los jugadores.
        if players and wage_budget:
            weights = [max(1.0, p.overall - 40.0) ** 2 for p in players]
            total_w = sum(weights)
            assigned = 0
            for i, (p, w) in enumerate(zip(players, weights)):
                if i == len(players) - 1:
                    p.salary = max(0, wage_budget - assigned)
                else:
                    p.salary = int(wage_budget * w / total_w)
                    assigned += p.salary
            # Suelo salarial: una estrella no puede cobrar como un suplente.
            for p in players:
                p.salary = max(p.salary, int(max(5000, (p.overall - 48) * 700)))
            wage_budget = max(wage_budget, sum(p.salary for p in players))
        transfer_budget = int(int(fin.get("transfer_budget", 0) or 0) * 1.5)
        cash = transfer_budget + int(wage_budget * 0.45)
        facilities = {
            "training": max(40, min(95, 50 + int(bool(fac.get("gym"))) * 12 + int(fac.get("pitches", 0) or 0) * 4)),
            "youth": max(40, min(90, 50 + int(fac.get("academy", 0) or 0) * 7)),
            "medical": 60 if fac.get("medical") else 50,
            "video": 60 if fac.get("video") else 50,
            "scouting": max(40, min(90, 55 + int(fac.get("academy", 0) or 0) * 2)),
            "stadium": max(40, min(95, 40 + int(stadium.get("capacity", 1000) or 1000) // 60)),
        }
        teams[club["id"]] = TeamState(
            id=club["id"],
            name=club["name"],
            league=club["league"],
            city=club["city"],
            community=club.get("community", ""),
            players=players,
            tactics=Tactics(),
            stadium_name=stadium.get("name", ""),
            stadium_capacity=int(stadium.get("capacity", 1000) or 1000),
            board_expectation=club.get("board", {}).get("expectation", ""),
            board_patience=int(club.get("board", {}).get("patience", 3) or 3),
            board_pressure=str(club.get("board", {}).get("pressure", "media")),
            academy_rating=max(40, min(90, 50 + int(fac.get("academy", 0) or 0) * 7)),
            preferred_mode=club.get("logistics", {}).get("preferred_mode", ""),
            assistant_rating=assistant_rating,
            staff=staff,
            board=board,
            transfer_budget=transfer_budget,
            club_tier=int(fin.get("tier", 3) or 3),
            budget=cash,
            wage_budget=wage_budget,
            facilities=facilities,
        )
    return teams, clubs_by_id, cities_by_name


def dha_teams(teams: dict[str, TeamState]) -> list[TeamState]:
    return [t for t in teams.values() if t.league == "DHA"]


LOWER_LEAGUE_CODES = {"1A", "1N", "1M", "1G", "1C", "1V", "SUP", "CAT1"}
LOWER_SALARY_FACTOR = {
    "1A": 0.62,
    "1N": 0.56,
    "1M": 0.56,
    "1G": 0.56,
    "1C": 0.56,
    "1V": 0.56,
    "SUP": 0.70,
    "CAT1": 0.52,
}


def load_lower_division_free_agents() -> list[PlayerState]:
    """Jugadores de divisiones autonómicas, disponibles como agentes libres.

    No crean equipos jugables. Se cargan desde el CSV regenerado con las
    plantillas de iSquad y quedan fuera de ``state.teams``.
    """
    path = TOOLS / "player_attributes_v2.csv"
    if not path.exists():
        return []
    agents: list[PlayerState] = []
    seen: set[str] = set()
    seen_names: set[str] = set()
    # Ningún jugador de DHA/DHB puede volver a aparecer como agente libre
    # autonómico. El nombre normalizado es la clave de identidad.
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("liga") or "").strip() in ("DHA", "DHB"):
                name = str(row.get("jugador") or "").strip()
                if name:
                    seen_names.add(norm(name))
    with path.open(encoding="utf-8-sig") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            league = str(row.get("liga") or "").strip()
            if league not in LOWER_LEAGUE_CODES:
                continue
            if str(row.get("perfil") or "").strip().lower() in STAFF_PROFILES:
                continue
            team_name = str(row.get("equipo") or "").strip()
            # San Fernando 1ª ya se incorpora desde el equipo 1A original.
            if team_name == "CLUB DE HOCKEY SAN FERNANDO":
                continue
            name = str(row.get("jugador") or "").strip()
            if not name:
                continue
            key = f"{slug(team_name)}-{slug(name)}"
            if key in seen:
                continue
            # Un jugador solo puede estar en un equipo. Si iSquad lo publica
            # en el primer equipo y en el filial, prevalece la primera ficha.
            name_key = norm(name)
            if name_key in seen_names:
                continue
            seen.add(key)
            seen_names.add(name_key)
            attrs = {}
            for column, value in row.items():
                if column.startswith("attr_"):
                    try:
                        attrs[column[5:]] = int(float(value or 50))
                    except (TypeError, ValueError):
                        attrs[column[5:]] = 50
            try:
                overall = float(row.get("overall") or 0)
            except (TypeError, ValueError):
                overall = 0.0
            # Techo general por categoría: un jugador de 1A puede destacar,
            # pero no debe superar la media del DHB más bajo. Es una
            # calibración de escalera, no una excepción de club.
            from .ratings import profile as league_profile

            overall = min(overall, league_profile(league).standard + 3.4)
            try:
                potential = float(row.get("potential") or overall)
            except (TypeError, ValueError):
                potential = overall
            try:
                value = int(float(row.get("value") or 0))
            except (TypeError, ValueError):
                value = 0
            try:
                goals = int(float(row.get("goles") or 0))
            except (TypeError, ValueError):
                goals = 0
            try:
                age = int(float(row.get("edad") or 22))
            except (TypeError, ValueError):
                age = 22
            overalls = {}
            for pos, column in (
                ("Portero", "overall_portero"),
                ("Central", "overall_central"),
                ("Lateral", "overall_lateral"),
                ("Medio", "overall_medio"),
                ("Delantero", "overall_delantero"),
            ):
                try:
                    overalls[pos] = float(row.get(column) or 0)
                except (TypeError, ValueError):
                    overalls[pos] = 0.0
            try:
                poly = float(row.get("polivalencia") or 0)
            except (TypeError, ValueError):
                poly = 0.0
            photo_rel = str(row.get("archivo_original") or "").strip()
            photo = photo_rel if photo_rel and (BASE / "jugadores" / photo_rel).exists() else ""
            photo_remote = str(row.get("imagen_url") or "").strip()
            salary_factor = LOWER_SALARY_FACTOR.get(league, 0.55)
            salary = int(max(5000, (overall - 40) * 1200 * salary_factor))
            player_id = f"fa-{slug(team_name)}-{slug(name)}-{index}"
            agents.append(
                PlayerState(
                    id=player_id,
                    name=name,
                    team_name="Agente libre",
                    origin_team=team_name,
                    position_group=str(row.get("position_group") or "Medio"),
                    subposition=str(row.get("subposicion") or "Medio"),
                    age=age,
                    overall=overall,
                    potential=potential,
                    attributes=attrs,
                    archetype=str(row.get("archetype") or "Jugador"),
                    perfil=str(row.get("perfil") or "Jugador"),
                    goals_isquad=goals,
                    value=value,
                    polivalencia=poly,
                    overalls=overalls,
                    salary=salary,
                    contract_until="2027-06-30",
                    league=league,
                    photo=photo,
                    photo_remote=photo_remote,
                    form=6.5,
                    relationship=50,
                    morale=12,
                )
            )
    return agents
