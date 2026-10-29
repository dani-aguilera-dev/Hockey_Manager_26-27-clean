"""Valoraciones contextuales por categoría.

El overall y el potencial son absolutos (current/potential ability). Las
estrellas son relativas a la categoría en la que compite el jugador, al estilo
de Football Manager: un 4,5★ en una categoría inferior puede ser un 3★ al
ascender.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LeagueProfile:
    label: str
    standard: float
    spread: float
    rank: int


LEAGUE_PROFILES = {
    "DHA": LeagueProfile("DHA", 74.8, 8.0, 1),
    "DHB": LeagueProfile("DHB", 64.0, 8.0, 2),
    "1A": LeagueProfile("1ª Andaluza", 56.1, 8.0, 3),
    "1N": LeagueProfile("1ª Autonómica Norte", 53.2, 8.0, 3),
    "1M": LeagueProfile("1ª Autonómica Madrid", 53.3, 8.0, 3),
    "1G": LeagueProfile("1ª Autonómica Galicia", 53.2, 8.0, 3),
    "1C": LeagueProfile("1ª Autonómica Canarias", 52.5, 8.0, 3),
    "1V": LeagueProfile("1ª Autonómica FHCV", 53.8, 8.0, 3),
    "SUP": LeagueProfile("Superlliga Catalana", 59.0, 8.0, 3),
    "CAT1": LeagueProfile("Primera Catalana", 53.0, 8.0, 3),
    "EHL": LeagueProfile("EHL", 86.0, 8.0, 0),
    "NED": LeagueProfile("Hoofdklasse", 84.0, 8.0, 0),
    "BEL": LeagueProfile("Belgian League", 82.0, 8.0, 0),
    "GER": LeagueProfile("Bundesliga", 81.0, 8.0, 0),
    "ENG": LeagueProfile("Premier Division", 79.0, 8.0, 0),
    "ARG": LeagueProfile("Metropolitano", 77.0, 8.0, 0),
    "IND": LeagueProfile("Hockey India League", 76.0, 8.0, 0),
}


def profile(league: str | None) -> LeagueProfile:
    return LEAGUE_PROFILES.get(str(league or ""), LEAGUE_PROFILES["DHA"])


def league_label(league: str | None) -> str:
    return profile(league).label


def stars(value: float, league: str | None) -> float:
    """Estrellas sobre 5, relativas al nivel de la categoría."""
    p = profile(league)
    raw = 3.0 + (float(value) - p.standard) / p.spread
    return math.floor(max(0.5, min(5.0, raw)) * 2 + 0.5) / 2


def stars_text(value: float, league: str | None) -> str:
    return f"{stars(value, league):.1f}★"


def stars_bar(value: float, league: str | None) -> str:
    rating = stars(value, league)
    full = int(rating)
    half = rating - full >= 0.5
    return "★" * full + ("½" if half else "") + "☆" * max(0, 5 - full - (1 if half else 0))


def tier(value: float, league: str | None) -> str:
    rating = stars(value, league)
    if rating >= 4.5:
        return "Estrella de la categoría"
    if rating >= 4.0:
        return "Muy buen jugador"
    if rating >= 3.0:
        return "Titular"
    if rating >= 2.0:
        return "Rotación"
    return "Suplente"


def scout_stars(low: float, high: float, league: str | None) -> str:
    return f"{stars(low, league):.1f}-{stars(high, league):.1f}★"
