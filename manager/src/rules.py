"""Reglas FIH que afectan al motor de partido y a la disciplina.

La referencia principal es la edición 2027 de las Reglas de Hockey de la FIH,
efectiva desde el 1 de noviembre de 2026. La edición 2026 se mantiene como
referencia para el inicio de la temporada 2026-27.

Este módulo no pretende sustituir al reglamento: centraliza las constantes y
decisiones operativas que el videojuego necesita para que las tarjetas, las
suspensiones y los tiempos de partido sean coherentes.
"""

from __future__ import annotations

from typing import Literal

RULESET = "FIH_2027"
RULES_EFFECTIVE_DATE = "2026-11-01"
RULES_REFERENCE = "https://www.fih.hockey/static-assets/pdf/2026_09_14_fih_rules_of_hockey_2027_clean.pdf"

# Estructura del partido.
QUARTERS = 4
QUARTER_MINUTES = 15.0
QUARTER_INTERVAL_MINUTES = 2
HALF_TIME_MINUTES = 10
PLAYERS_ON_FIELD = 11
MAX_SQUAD_SIZE = 16
MAX_SUBSTITUTES = 5
MAX_SUBSTITUTIONS = 5

# Disciplina.
GREEN_CARD_MINUTES = 2
YELLOW_CARD_MINUTES = (5, 10)
RED_CARD_REST_OF_MATCH = True
# Simplificación de competición: una roja puede acarrear sanción posterior.
# El módulo disciplinario podrá ampliarla según el comité.
RED_CARD_NEXT_MATCHES = 1

# Revisión de vídeo (video umpire). En las competiciones con videoarbitraje
# cada equipo dispone de una referencia; si prospera, la conserva, y si no,
# la pierde. El capitán puede solicitar la revisión de un gol, un penalty
# corner o un penalty stroke.
REFERRALS_PER_TEAM = 1
# Faltas y discrecionalidad arbitral.
FREE_HIT_DISTANCE_METERS = 5
ADVANTAGE_SECONDS = 3
FOUL_TYPES: dict[str, dict[str, object]] = {
    "stick": {"label": "golpe de stick", "dangerous": True, "weight": 0.30},
    "dangerous": {"label": "juego peligroso", "dangerous": True, "weight": 0.15},
    "physical": {"label": "carga física", "dangerous": False, "weight": 0.25},
    "foot": {"label": "pie", "dangerous": False, "weight": 0.20},
    "obstruction": {"label": "obstrucción", "dangerous": False, "weight": 0.10},
}

OPPOSITION_INSTRUCTIONS: dict[str, dict[str, object]] = {
    "tight_marking": {
        "label": "Marcaje individual",
        "description": "Seguir de cerca al jugador para quitarle tiempo y espacio.",
        "attack": 1.3,
        "defense": 0.2,
    },
    "press": {
        "label": "Presión alta",
        "description": "Saltar a presionar para forzar errores en la salida.",
        "attack": 1.0,
        "defense": 0.1,
    },
    "double_team": {
        "label": "Doblar por banda",
        "description": "Enviar ayuda al lado del jugador y cerrar la superioridad.",
        "attack": 1.8,
        "defense": 0.3,
    },
    "force_weak_side": {
        "label": "Forzar lado débil",
        "description": "Orientar al rival hacia su lado menos peligroso.",
        "attack": 0.8,
        "defense": 0.0,
    },
}

REFERRAL_DECISIONS: dict[str, str] = {
    "goal": "Gol",
    "penalty_corner": "Penalty corner",
    "penalty_stroke": "Penalty stroke",
}

CardType = Literal["green", "yellow", "red"]

CARD_LABELS: dict[str, str] = {
    "green": "Tarjeta verde",
    "yellow": "Tarjeta amarilla",
    "red": "Tarjeta roja",
}

CARD_DESCRIPTIONS: dict[str, str] = {
    "green": "Suspensión temporal de 2 minutos de tiempo de juego.",
    "yellow": "Suspensión temporal de 5 o 10 minutos de tiempo de juego.",
    "red": "Expulsión para el resto del partido.",
}

# Motivos genéricos para que el parte y el historial no muestren una tarjeta
# sin contexto. El motor puede sustituirlos por un motivo más concreto.
REFEREE_PROFILES: list[dict[str, object]] = [
    {"name": "Marta Solís", "style": "técnica", "strictness": 62, "card_bias": 0.015},
    {"name": "Hugo Peña", "style": "permisiva", "strictness": 38, "card_bias": -0.035},
    {"name": "Clara Ferrán", "style": "estricta", "strictness": 82, "card_bias": 0.045},
    {"name": "Iker Salas", "style": "experimentada", "strictness": 55, "card_bias": 0.0},
    {"name": "Nora Vidal", "style": "de contacto", "strictness": 70, "card_bias": 0.025},
]

CARD_REASONS: dict[str, list[str]] = {
    "green": [
        "falta técnica repetida",
        "protesta",
        "juego peligroso leve",
        "retraso deliberado",
    ],
    "yellow": [
        "juego peligroso",
        "falta intencionada",
        "protesta reiterada",
        "conducta antideportiva",
    ],
    "red": [
        "conducta violenta",
        "agresión",
        "insulto grave",
        "juego peligroso grave",
    ],
}


def is_temporary_card(card_type: str) -> bool:
    return card_type in ("green", "yellow")


def is_permanent_card(card_type: str) -> bool:
    return card_type == "red"


def suspension_minutes(card_type: str, serious: bool = False) -> int:
    """Minutos de suspensión durante el partido.

    La verde son siempre 2 minutos. La amarilla es 5 minutos para una falta
    menor y 10 para una falta grave o física.
    """
    if card_type == "green":
        return GREEN_CARD_MINUTES
    if card_type == "yellow":
        return 10 if serious else 5
    return 0


def next_match_suspension(card_type: str) -> int:
    """Partidos de sanción posteriores al partido.

    Las tarjetas verde y amarilla son sanciones exclusivamente de partido.
    La roja puede tener consecuencias posteriores según la competición.
    """
    if card_type == "red":
        return RED_CARD_NEXT_MATCHES
    return 0


def next_card_for_player(cards: list[str]) -> str:
    """Siguiente categoría si el jugador ya ha visto una tarjeta.

    La edición 2027 evita que el mismo jugador reciba dos verdes o dos
    amarillas en el mismo partido. Si ya tiene una sanción personal, la
    siguiente tarjeta debe ser de categoría superior.
    """
    if "red" in cards:
        return "red"
    if "yellow" in cards:
        return "red"
    if "green" in cards:
        return "yellow"
    return "green"


def card_sort_key(card_type: str) -> int:
    return {"green": 0, "yellow": 1, "red": 2}.get(card_type, 0)
