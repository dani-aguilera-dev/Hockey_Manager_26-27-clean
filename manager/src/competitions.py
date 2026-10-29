"""Registro de competiciones nacionales e internacionales.

Toda la configuración de ligas vive en ``manager/data/competitions.json`` y
las reglas transversales en ``manager/data/league_rules.json``. Este módulo
solo valida y expone esos datos; no contiene nombres de ligas ni fechas
especiales.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class Competition:
    code: str
    name: str
    short_name: str
    country: str
    country_code: str
    confederation: str
    standard: float
    start_date: str
    teams: int
    format: str = "double_round_robin"
    playoffs: int = 0
    relegation: int = 0
    international: bool = False
    system: str = "double_round_robin"
    promotion_zone: str = ""
    promotion_zone_name: str = ""
    regular_rounds: int = 0
    promotion_qualifiers: int = 2


DATA = Path(__file__).resolve().parents[1] / "data"


def _load_json(name: str) -> dict:
    path = DATA / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_competitions() -> dict[str, Competition]:
    rows = _load_json("competitions.json")
    out: dict[str, Competition] = {}
    allowed = {item.name for item in fields(Competition)}
    for code, row in rows.items():
        payload = {key: value for key, value in row.items() if key in allowed}
        payload["code"] = code
        out[code] = Competition(**payload)
    return out


COMPETITIONS: dict[str, Competition] = _load_competitions()
RULES = _load_json("league_rules.json")

LEAGUE_RATING_TARGETS: dict[str, float] = {
    code: meta.standard for code, meta in COMPETITIONS.items()
}
REGIONAL_CODES = {code for code, meta in COMPETITIONS.items() if meta.format == "regional"}
PROMOTION_GROUP_START = str(RULES["promotion_group_start"])
PROMOTION_FINAL_START = str(RULES["promotion_final_start"])
PROMOTION_SPOTS = int(RULES["promotion_spots"])
MIN_ROSTER_SIZE = int(RULES["min_roster_size"])
MIN_MATCHDAY_SQUAD = int(RULES["min_matchday_squad"])
DEFAULT_REGIONAL_LEAGUE = str(RULES["default_regional_league"])
MARKET_SOURCE_SYSTEMS = set(RULES["market_source_systems"])


def competition(code: str | None) -> Competition:
    if not COMPETITIONS:
        raise RuntimeError("No hay competiciones configuradas en competitions.json")
    return COMPETITIONS.get(str(code or ""), COMPETITIONS[next(iter(COMPETITIONS))])


def code_for_system(system: str) -> str:
    return next((meta.code for meta in COMPETITIONS.values() if meta.system == system), "")


def is_international(code: str | None) -> bool:
    return competition(code).international


def league_name(code: str | None) -> str:
    return competition(code).name


def league_short_name(code: str | None) -> str:
    return competition(code).short_name


def country(code: str | None) -> str:
    return competition(code).country


def is_regional(code: str | None) -> bool:
    return str(code or "") in REGIONAL_CODES


def playable_competitions() -> list[Competition]:
    return list(COMPETITIONS.values())


def promotion_groups() -> list[tuple[str, tuple[str, ...]]]:
    """Agrupa las ligas regionales por la zona declarada en sus datos."""
    zones: dict[str, tuple[str, list[str]]] = {}
    for meta in COMPETITIONS.values():
        if not meta.promotion_zone:
            continue
        name, codes = zones.setdefault(meta.promotion_zone, (meta.promotion_zone_name, []))
        codes.append(meta.code)
    return [(name, tuple(codes)) for name, codes in zones.values()]
